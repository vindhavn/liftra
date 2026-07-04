"""
Refund models for Liftra.
"""

from decimal import Decimal
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from liftra.core.models.base import BaseModel


class RefundStatus(str, Enum):
    """Status of a refund."""

    REQUESTED = "requested"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class RefundReason(str, Enum):
    """Reason for a refund."""

    CANCELLATION = "cancellation"
    RETURN = "return"
    POOR_QUALITY = "poor_quality"
    NOT_AS_DESCRIBED = "not_as_described"
    DUPLICATE_CHARGE = "duplicate_charge"
    FRAUD = "fraud"
    OTHER = "other"


class Refund(BaseModel):
    """
    Represents a refund transaction.
    
    Refunds are special transactions that are linked to original
    transactions and are excluded from budget calculations.
    """

    # Refund details
    original_transaction_id: UUID = Field(
        ..., description="ID of the original transaction being refunded"
    )
    amount: Decimal = Field(
        ..., gt=0, description="Amount of the refund"
    )
    currency_code: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    
    # Status and reason
    status: RefundStatus = Field(
        default=RefundStatus.REQUESTED, description="Current status of the refund"
    )
    reason: RefundReason | None = Field(
        default=None, description="Reason for the refund"
    )
    reason_description: str | None = Field(
        default=None, max_length=1000, description="Detailed reason description"
    )
    
    # Dates
    requested_date: date | None = Field(
        default=None, description="Date when refund was requested"
    )
    approved_date: date | None = Field(
        default=None, description="Date when refund was approved"
    )
    processed_date: date | None = Field(
        default=None, description="Date when refund was processed"
    )
    completed_date: date | None = Field(
        default=None, description="Date when refund was completed"
    )
    
    # Transaction reference
    transaction_id: UUID | None = Field(
        default=None, description="ID of the transaction created for this refund"
    )
    
    # Account
    account_id: UUID | None = Field(
        default=None, description="ID of the account for the refund"
    )
    
    # Payee (who is refunding)
    payee_id: UUID | None = Field(
        default=None, description="ID of the payee issuing the refund"
    )
    
    # Method
    refund_method: str | None = Field(
        default=None, max_length=100, description="Method of refund (cash, bank_transfer, etc.)"
    )
    reference: str | None = Field(
        default=None, max_length=255, description="Refund reference number"
    )
    
    # Budget impact
    exclude_from_budget: bool = Field(
        default=True, description="Whether to exclude this refund from budget calculations"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"Refund for {self.original_transaction_id}: {self.amount} {self.currency_code}"
    
    @property
    def is_complete(self) -> bool:
        """Check if the refund is complete."""
        return self.status == RefundStatus.COMPLETED
    
    @property
    def is_pending(self) -> bool:
        """Check if the refund is pending."""
        return self.status in [
            RefundStatus.REQUESTED,
            RefundStatus.APPROVED,
            RefundStatus.PROCESSING
        ]
