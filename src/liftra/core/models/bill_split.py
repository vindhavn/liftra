"""
Bill splitting models for Liftra.
"""

from decimal import Decimal
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from liftra.core.models.base import BaseModel


class BillSplitStatus(str, Enum):
    """Status of a bill split group."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BillSplitGroup(BaseModel):
    """
    Represents a group for splitting bills.
    
    This could be for a holiday, trip, project, meal, etc.
    """

    # Group details
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the group"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the group"
    )
    
    # Status
    status: BillSplitStatus = Field(
        default=BillSplitStatus.DRAFT, description="Current status of the group"
    )
    
    # Dates
    start_date: date | None = Field(
        default=None, description="Start date of the group"
    )
    end_date: date | None = Field(
        default=None, description="End date of the group"
    )
    
    # Participants
    participant_ids: list[UUID] = Field(
        default_factory=list, description="List of participant IDs"
    )
    
    # Expenses
    expense_ids: list[UUID] = Field(
        default_factory=list, description="List of expense IDs"
    )
    
    # Currency
    currency_code: str = Field(
        default="GBP", min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"{self.name} ({self.status.value})"


class BillSplitParticipant(BaseModel):
    """
    Represents a participant in a bill split group.
    """

    # Participant details
    group_id: UUID = Field(
        ..., description="ID of the parent group"
    )
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the participant"
    )
    
    # Contact information
    email: str | None = Field(
        default=None, max_length=255, description="Email address"
    )
    phone: str | None = Field(
        default=None, max_length=50, description="Phone number"
    )
    
    # Payment information
    payment_method: str | None = Field(
        default=None, max_length=100, description="Preferred payment method"
    )
    account_details: str | None = Field(
        default=None, max_length=500, description="Bank account details for transfers"
    )
    
    # Status
    is_active: bool = Field(
        default=True, description="Whether the participant is active"
    )
    
    # Balances
    total_paid: Decimal = Field(
        default=Decimal("0"), description="Total amount paid by this participant"
    )
    total_owed: Decimal = Field(
        default=Decimal("0"), description="Total amount owed by this participant"
    )
    total_used: Decimal = Field(
        default=Decimal("0"), description="Total amount used/benefited by this participant"
    )
    balance: Decimal = Field(
        default=Decimal("0"), description="Current balance (positive = owed to participant, negative = participant owes)"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"{self.name} (Balance: {self.balance})"


class BillSplitExpense(BaseModel):
    """
    Represents an expense in a bill split group.
    """

    # Expense details
    group_id: UUID = Field(
        ..., description="ID of the parent group"
    )
    description: str = Field(
        ..., min_length=1, max_length=1000, description="Description of the expense"
    )
    amount: Decimal = Field(
        ..., gt=0, description="Amount of the expense"
    )
    currency_code: str = Field(
        default="GBP", min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    
    # Payer
    payer_id: UUID | None = Field(
        default=None, description="ID of the participant who paid"
    )
    
    # Dates
    expense_date: date = Field(
        ..., description="Date of the expense"
    )
    
    # Category
    category: str | None = Field(
        default=None, max_length=255, description="Category of the expense"
    )
    
    # Splitting method
    split_method: str = Field(
        default="equal", description="Method for splitting the expense (equal, proportional, custom)"
    )
    
    # Usage tracking
    usage_ids: list[UUID] = Field(
        default_factory=list, description="List of usage IDs for this expense"
    )
    
    # Related transaction
    transaction_id: UUID | None = Field(
        default=None, description="ID of the related transaction"
    )
    
    # Status
    is_verified: bool = Field(
        default=False, description="Whether the expense has been verified"
    )
    is_settled: bool = Field(
        default=False, description="Whether the expense has been settled"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"{self.description}: {self.amount} {self.currency_code}"


class BillSplitUsage(BaseModel):
    """
    Represents usage of an expense by a participant.
    
    This allows tracking who used/benefited from what,
    which is useful for fair splitting (e.g., different meal costs).
    """

    # Usage details
    expense_id: UUID = Field(
        ..., description="ID of the parent expense"
    )
    participant_id: UUID = Field(
        ..., description="ID of the participant"
    )
    
    # Usage amount
    amount: Decimal | None = Field(
        default=None, description="Amount used by this participant (None = equal share)"
    )
    proportion: Decimal | None = Field(
        default=None, description="Proportion used by this participant (0-1)"
    )
    
    # Description
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the usage"
    )
    
    # Dates
    usage_date: date | None = Field(
        default=None, description="Date when the usage occurred"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"Usage by {self.participant_id} for {self.expense_id}"
