"""
Category models for Liftra.
"""

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from liftra.core.models.base import BaseModel


class Category(BaseModel):
    """
    Represents a category for organizing transactions.
    
    Categories can be hierarchical (parent/child relationships) and can have
    rules for auto-categorizing transactions.
    """

    # Category details
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the category"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the category"
    )
    
    # Hierarchy
    parent_id: UUID | None = Field(
        default=None, description="ID of the parent category (for hierarchical categories)"
    )
    path: str = Field(
        default="", description="Full path of the category (e.g., 'Expenses/Food/Groceries')"
    )
    
    # Category type
    is_income: bool = Field(
        default=False, description="Whether this is an income category"
    )
    is_expense: bool = Field(
        default=True, description="Whether this is an expense category"
    )
    is_transfer: bool = Field(
        default=False, description="Whether this is a transfer category"
    )
    
    # Color and icon
    color: str | None = Field(
        default=None, max_length=20, description="Color for the category (hex code)"
    )
    icon: str | None = Field(
        default=None, max_length=100, description="Icon name or path"
    )
    
    # Auto-categorization rules
    rules: list[dict[str, Any]] = Field(
        default_factory=list, 
        description="Rules for auto-categorizing transactions to this category"
    )
    
    # Budget
    budget_id: UUID | None = Field(
        default=None, description="ID of the budget associated with this category"
    )
    
    # Order
    order: int = Field(
        default=0, description="Order for sorting categories"
    )
    
    # Status
    is_active: bool = Field(
        default=True, description="Whether the category is active"
    )
    is_system: bool = Field(
        default=False, description="Whether this is a system category (cannot be deleted)"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate and normalize category path."""
        if not v:
            return ""
        # Remove leading/trailing slashes
        v = v.strip("/")
        # Replace multiple slashes with single slash
        v = "/".join(part for part in v.split("/") if part)
        return v
    
    @property
    def depth(self) -> int:
        """Get the depth of the category in the hierarchy."""
        if not self.path:
            return 0
        return len(self.path.split("/"))
    
    @property
    def is_root(self) -> bool:
        """Check if this is a root category."""
        return self.depth == 0
    
    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf category (has no children)."""
        # This would need to be checked against the repository
        return True
    
    def __str__(self) -> str:
        return self.name
    
    @property
    def display_name(self) -> str:
        """Get display name with full path."""
        if self.path:
            return f"{self.path}/{self.name}"
        return self.name
