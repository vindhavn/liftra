"""
Budget models for Liftra.
"""

from decimal import Decimal
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from liftra.core.models.base import BaseModel


class BudgetType(str, Enum):
    """Types of budgets."""

    MONTHLY = "monthly"
    ANNUAL = "annual"
    WEEKLY = "weekly"
    DAILY = "daily"
    QUARTERLY = "quarterly"
    PROJECT = "project"
    ROLLING = "rolling"
    ZERO_BASED = "zero_based"


class BudgetStatus(str, Enum):
    """Status of a budget."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class Budget(BaseModel):
    """
    Represents a budget.
    
    Budgets can be for various periods and can be hierarchical.
    """

    # Budget details
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the budget"
    )
    budget_type: BudgetType = Field(
        default=BudgetType.MONTHLY, description="Type of budget"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the budget"
    )
    
    # Period
    start_date: date = Field(
        ..., description="Start date of the budget period"
    )
    end_date: date | None = Field(
        default=None, description="End date of the budget period"
    )
    
    # Amount
    target_amount: Decimal | None = Field(
        default=None, description="Target amount for the budget"
    )
    currency_code: str = Field(
        default="GBP", min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    
    # Status
    status: BudgetStatus = Field(
        default=BudgetStatus.DRAFT, description="Current status of the budget"
    )
    
    # Hierarchy
    parent_id: UUID | None = Field(
        default=None, description="ID of the parent budget (for hierarchical budgets)"
    )
    category_ids: list[UUID] = Field(
        default_factory=list, description="List of category IDs included in this budget"
    )
    
    # Tracking
    current_spent: Decimal = Field(
        default=Decimal("0"), description="Current amount spent"
    )
    current_income: Decimal = Field(
        default=Decimal("0"), description="Current income (for income budgets)"
    )
    
    # Rollovers
    allow_rollover: bool = Field(
        default=False, description="Whether to allow rollover of unused budget"
    )
    rollover_amount: Decimal = Field(
        default=Decimal("0"), description="Amount rolled over from previous period"
    )
    
    # Alerts
    alert_threshold: Decimal | None = Field(
        default=None, description="Threshold for budget alerts (percentage)"
    )
    alert_email: str | None = Field(
        default=None, max_length=255, description="Email for budget alerts"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"{self.name} ({self.budget_type.value})"
    
    @property
    def remaining(self) -> Decimal:
        """Get remaining budget amount."""
        if self.target_amount is None:
            return Decimal("0")
        return self.target_amount - self.current_spent
    
    @property
    def percentage_used(self) -> Decimal:
        """Get percentage of budget used."""
        if self.target_amount is None or self.target_amount == Decimal("0"):
            return Decimal("0")
        return (self.current_spent / self.target_amount) * Decimal("100")
    
    @property
    def is_on_track(self) -> bool:
        """Check if budget is on track."""
        if self.target_amount is None:
            return True
        return self.current_spent <= self.target_amount


class BudgetCategory(BaseModel):
    """
    Represents a category within a budget.
    """

    # Category details
    budget_id: UUID = Field(
        ..., description="ID of the parent budget"
    )
    category_id: UUID | None = Field(
        default=None, description="ID of the linked category (if any)"
    )
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the budget category"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the budget category"
    )
    
    # Amount
    target_amount: Decimal | None = Field(
        default=None, description="Target amount for this category"
    )
    current_spent: Decimal = Field(
        default=Decimal("0"), description="Current amount spent in this category"
    )
    
    # Type
    is_income: bool = Field(
        default=False, description="Whether this is an income category"
    )
    is_expense: bool = Field(
        default=True, description="Whether this is an expense category"
    )
    
    # Order
    order: int = Field(
        default=0, description="Order for sorting categories"
    )
    
    # Status
    is_active: bool = Field(
        default=True, description="Whether the category is active"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"{self.name}"
    
    @property
    def remaining(self) -> Decimal:
        """Get remaining amount for this category."""
        if self.target_amount is None:
            return Decimal("0")
        return self.target_amount - self.current_spent
