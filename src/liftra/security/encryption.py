"""
Encryption service for Liftra.

This module provides encryption and decryption services for protecting
sensitive financial data at rest.
"""

import base64
import hashlib
import hmac
import json
import os
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

from liftra.core.exceptions import EncryptionError


class EncryptionService:
    """
    Service for encrypting and decrypting data.
    
    This service uses AES-256-GCM for encryption and Argon2id for key derivation.
    It provides methods for:
    - Encrypting and decrypting data
    - Generating and deriving encryption keys
    - Creating and verifying HMAC signatures
    """

    # Encryption settings
    AES_KEY_LENGTH = 32  # 256 bits for AES-256
    AES_NONCE_LENGTH = 12  # 96 bits for GCM nonce
    AES_TAG_LENGTH = 16  # 128 bits for GCM tag
    
    # Key derivation settings (Argon2id)
    ARGON2_TIME_COST = 3  # Number of iterations
    ARGON2_MEMORY_COST = 65536  # 64 MB memory usage
    ARGON2_PARALLELISM = 4  # Number of parallel threads
    ARGON2_HASH_LENGTH = 32  # Length of the derived key
    ARGON2_SALT_LENGTH = 16  # Length of the salt
    
    def __init__(self, master_key: bytes | None = None) -> None:
        """
        Initialize the encryption service.
        
        Args:
            master_key: Optional master key for encryption
        """
        self._master_key = master_key
        self._backend = default_backend()

    @property
    def has_master_key(self) -> bool:
        """Check if a master key is set."""
        return self._master_key is not None

    @property
    def master_key_fingerprint(self) -> str | None:
        """Get a fingerprint of the master key."""
        if self._master_key is None:
            return None
        return hashlib.sha256(self._master_key).hexdigest()[:16]

    def set_master_key(self, master_key: bytes | str) -> None:
        """
        Set the master key for encryption.
        
        Args:
            master_key: Master key (bytes or string)
        """
        if isinstance(master_key, str):
            self._master_key = master_key.encode("utf-8")
        else:
            self._master_key = master_key

    def generate_master_key(self) -> bytes:
        """
        Generate a new random master key.
        
        Returns:
            Random 32-byte master key
        """
        self._master_key = os.urandom(self.AES_KEY_LENGTH)
        return self._master_key

    def derive_key_from_password(
        self, password: str, salt: bytes | None = None
    ) -> tuple[bytes, bytes]:
        """
        Derive an encryption key from a password using Argon2id.
        
        Args:
            password: Password to derive key from
            salt: Optional salt (if None, a new random salt will be generated)
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(self.ARGON2_SALT_LENGTH)
        
        # Create Argon2id key derivation function
        kdf = Argon2id(
            salt=salt,
            length=self.ARGON2_HASH_LENGTH,
            iterations=self.ARGON2_TIME_COST,
            lanes=self.ARGON2_PARALLELISM,
            memory_cost=self.ARGON2_MEMORY_COST,
        )
        
        # Derive the key
        derived_key = kdf.derive(password.encode("utf-8"))
        
        return derived_key, salt

    def encrypt(self, plaintext: bytes | str) -> dict[str, Any]:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            plaintext: Data to encrypt (bytes or string)
            
        Returns:
            Dictionary containing:
            - ciphertext: Base64-encoded ciphertext
            - nonce: Base64-encoded nonce
            - tag: Base64-encoded authentication tag
            - version: Encryption version
            
        Raises:
            EncryptionError: If encryption fails
        """
        if self._master_key is None:
            raise EncryptionError("No master key set for encryption")
        
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")
        
        # Generate a random nonce
        nonce = os.urandom(self.AES_NONCE_LENGTH)
        
        # Create AES-GCM cipher
        aesgcm = AESGCM(self._master_key)
        
        # Encrypt the data
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        # Split ciphertext and tag
        tag_length = self.AES_TAG_LENGTH
        tag = ciphertext[-tag_length:]
        ciphertext = ciphertext[:-tag_length]
        
        return {
            "version": "1.0",
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "tag": base64.b64encode(tag).decode("ascii"),
        }

    def decrypt(self, encrypted_data: dict[str, Any]) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            encrypted_data: Dictionary containing encrypted data (from encrypt method)
            
        Returns:
            Decrypted data as bytes
            
        Raises:
            EncryptionError: If decryption fails
        """
        if self._master_key is None:
            raise EncryptionError("No master key set for decryption")
        
        # Extract and decode components
        try:
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
            nonce = base64.b64decode(encrypted_data["nonce"])
            tag = base64.b64decode(encrypted_data["tag"])
        except (KeyError, ValueError) as e:
            raise EncryptionError(f"Invalid encrypted data format: {e}") from e
        
        # Reconstruct full ciphertext
        full_ciphertext = ciphertext + tag
        
        # Create AES-GCM cipher
        aesgcm = AESGCM(self._master_key)
        
        try:
            # Decrypt the data
            plaintext = aesgcm.decrypt(nonce, full_ciphertext, None)
            return plaintext
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}") from e

    def encrypt_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Encrypt a dictionary.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Dictionary with encrypted data and metadata
        """
        json_data = json.dumps(data, ensure_ascii=False, default=str)
        encrypted = self.encrypt(json_data)
        return encrypted

    def decrypt_dict(self, encrypted_data: dict[str, Any]) -> dict[str, Any]:
        """
        Decrypt a dictionary.
        
        Args:
            encrypted_data: Encrypted data (from encrypt_dict)
            
        Returns:
            Decrypted dictionary
        """
        decrypted_bytes = self.decrypt(encrypted_data)
        return json.loads(decrypted_bytes.decode("utf-8"))

    def encrypt_string(self, text: str) -> dict[str, Any]:
        """
        Encrypt a string.
        
        Args:
            text: String to encrypt
            
        Returns:
            Dictionary with encrypted data and metadata
        """
        return self.encrypt(text)

    def decrypt_string(self, encrypted_data: dict[str, Any]) -> str:
        """
        Decrypt a string.
        
        Args:
            encrypted_data: Encrypted data (from encrypt_string)
            
        Returns:
            Decrypted string
        """
        decrypted_bytes = self.decrypt(encrypted_data)
        return decrypted_bytes.decode("utf-8")

    def create_hmac(self, data: bytes | str, key: bytes | None = None) -> dict[str, Any]:
        """
        Create an HMAC signature for data.
        
        Args:
            data: Data to sign
            key: Optional key for HMAC (defaults to master key)
            
        Returns:
            Dictionary containing signature and metadata
        """
        if key is None:
            if self._master_key is None:
                raise EncryptionError("No master key set for HMAC")
            key = self._master_key
        
        if isinstance(data, str):
            data = data.encode("utf-8")
        
        # Create HMAC
        h = hmac.new(key, data, hashlib.sha256)
        signature = h.digest()
        
        return {
            "version": "1.0",
            "signature": base64.b64encode(signature).decode("ascii"),
        }

    def verify_hmac(
        self, data: bytes | str, signature_data: dict[str, Any], key: bytes | None = None
    ) -> bool:
        """
        Verify an HMAC signature.
        
        Args:
            data: Data that was signed
            signature_data: Dictionary containing signature (from create_hmac)
            key: Optional key for HMAC (defaults to master key)
            
        Returns:
            True if signature is valid, False otherwise
        """
        if key is None:
            if self._master_key is None:
                raise EncryptionError("No master key set for HMAC verification")
            key = self._master_key
        
        if isinstance(data, str):
            data = data.encode("utf-8")
        
        try:
            signature = base64.b64decode(signature_data["signature"])
        except (KeyError, ValueError):
            return False
        
        # Create HMAC and compare
        h = hmac.new(key, data, hashlib.sha256)
        try:
            h.digest() == signature
            return True
        except ValueError:
            # Constant-time comparison
            return hmac.compare_digest(h.digest(), signature)

    def encrypt_field(self, data: Any, field_name: str) -> dict[str, Any]:
        """
        Encrypt a specific field in a dictionary.
        
        Args:
            data: Dictionary containing the field to encrypt
            field_name: Name of the field to encrypt
            
        Returns:
            Dictionary with the field encrypted
        """
        if field_name not in data:
            return data
        
        result = data.copy()
        field_value = data[field_name]
        
        if isinstance(field_value, (str, bytes)):
            result[field_name] = self.encrypt(field_value)
            result[f"{field_name}_encrypted"] = True
        
        return result

    def decrypt_field(self, data: dict[str, Any], field_name: str) -> dict[str, Any]:
        """
        Decrypt a specific field in a dictionary.
        
        Args:
            data: Dictionary containing the encrypted field
            field_name: Name of the field to decrypt
            
        Returns:
            Dictionary with the field decrypted
        """
        if field_name not in data or not data.get(f"{field_name}_encrypted"):
            return data
        
        result = data.copy()
        encrypted_value = data[field_name]
        
        if isinstance(encrypted_value, dict):
            result[field_name] = self.decrypt(encrypted_value).decode("utf-8")
        
        return result

    def secure_wipe(self, data: bytes | str) -> None:
        """
        Securely wipe data from memory.
        
        Args:
            data: Data to wipe
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        
        # Overwrite with zeros
        for i in range(len(data)):
            data[i] = 0
