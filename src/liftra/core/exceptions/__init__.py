"""
Custom exceptions for Liftra.
"""

from typing import Any


class LiftraError(Exception):
    """Base exception for all Liftra errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ValidationError(LiftraError):
    """Raised when data validation fails."""

    pass


class NotFoundError(LiftraError):
    """Raised when a requested resource is not found."""

    def __init__(
        self, resource_type: str, resource_id: str | None = None, message: str | None = None
    ) -> None:
        if message:
            super().__init__(message)
        else:
            if resource_id:
                msg = f"{resource_type} with ID '{resource_id}' not found"
            else:
                msg = f"{resource_type} not found"
            super().__init__(msg)
        self.resource_type = resource_type
        self.resource_id = resource_id


class DuplicateError(LiftraError):
    """Raised when attempting to create a duplicate resource."""

    def __init__(
        self, resource_type: str, field: str, value: Any, message: str | None = None
    ) -> None:
        if message:
            super().__init__(message)
        else:
            msg = f"Duplicate {resource_type} with {field}='{value}'"
            super().__init__(msg)
        self.resource_type = resource_type
        self.field = field
        self.value = value


class CurrencyError(LiftraError):
    """Raised for currency-related errors."""

    pass


class EncryptionError(LiftraError):
    """Raised for encryption/decryption errors."""

    pass


class StorageError(LiftraError):
    """Raised for storage-related errors."""

    pass


class ConfigurationError(LiftraError):
    """Raised for configuration errors."""

    pass


class PluginError(LiftraError):
    """Raised for plugin-related errors."""

    pass


class AuthenticationError(LiftraError):
    """Raised for authentication errors."""

    pass


class AuthorizationError(LiftraError):
    """Raised for authorization errors."""

    pass
