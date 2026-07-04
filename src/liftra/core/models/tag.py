"""
Tag models for Liftra.
"""

from typing import Any

from pydantic import Field, field_validator

from liftra.core.models.base import BaseModel


class Tag(BaseModel):
    """
    Represents a tag for organizing and categorizing entities.
    
    Tags can be applied to transactions, accounts, payees, and other entities
    to provide flexible organization and filtering capabilities.
    """

    # Tag details
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the tag"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the tag"
    )
    
    # Color and icon
    color: str | None = Field(
        default=None, max_length=20, description="Color for the tag (hex code)"
    )
    icon: str | None = Field(
        default=None, max_length=100, description="Icon name or path"
    )
    
    # Category
    category: str | None = Field(
        default=None, max_length=255, description="Category for grouping tags"
    )
    
    # Usage
    usage_count: int = Field(
        default=0, description="Number of times this tag has been used"
    )
    
    # Status
    is_active: bool = Field(
        default=True, description="Whether the tag is active"
    )
    is_system: bool = Field(
        default=False, description="Whether this is a system tag (cannot be deleted)"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and normalize tag name."""
        # Remove leading/trailing whitespace
        v = v.strip()
        # Replace multiple spaces with single space
        v = " ".join(v.split())
        return v
    
    def __str__(self) -> str:
        return self.name
    
    @property
    def display_name(self) -> str:
        """Get display name with category."""
        if self.category:
            return f"{self.category}:{self.name}"
        return self.name
