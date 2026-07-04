"""
Attachment models for Liftra.
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from liftra.core.models.base import BaseModel


class Attachment(BaseModel):
    """
    Represents an attachment (file) associated with an entity.
    
    Attachments can be files, images, documents, or any other binary data
    that is linked to accounts, transactions, payees, etc.
    """

    # File details
    filename: str = Field(
        ..., min_length=1, max_length=1000, description="Original filename"
    )
    display_name: str | None = Field(
        default=None, max_length=255, description="Display name for the attachment"
    )
    
    # File type
    mime_type: str | None = Field(
        default=None, max_length=255, description="MIME type of the file"
    )
    file_extension: str | None = Field(
        default=None, max_length=50, description="File extension"
    )
    
    # Storage information
    storage_type: str = Field(
        default="local", description="Type of storage (local, cloud, embedded)"
    )
    storage_path: str | None = Field(
        default=None, max_length=2000, description="Path to the file in storage"
    )
    file_size: int = Field(
        default=0, ge=0, description="Size of the file in bytes"
    )
    
    # Content
    content: bytes | None = Field(
        default=None, description="File content (for embedded storage)"
    )
    content_encoding: str | None = Field(
        default=None, max_length=50, description="Content encoding (e.g., base64)"
    )
    
    # Thumbnail (for images)
    has_thumbnail: bool = Field(
        default=False, description="Whether a thumbnail is available"
    )
    thumbnail_content: bytes | None = Field(
        default=None, description="Thumbnail content"
    )
    
    # Metadata
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the attachment"
    )
    
    # Dates
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the file was uploaded"
    )
    modified_at: datetime | None = Field(
        default=None, description="When the file was last modified"
    )
    
    # Security
    is_encrypted: bool = Field(
        default=False, description="Whether the file content is encrypted"
    )
    encryption_key_id: str | None = Field(
        default=None, description="ID of the encryption key used"
    )
    
    # Status
    is_active: bool = Field(
        default=True, description="Whether the attachment is active"
    )
    
    # Custom fields
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    
    def __str__(self) -> str:
        return self.filename
    
    @property
    def display_filename(self) -> str:
        """Get display filename."""
        return self.display_name or self.filename
    
    @property
    def file_size_display(self) -> str:
        """Get human-readable file size."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"
