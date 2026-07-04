"""
Compensation models for Liftra.
"""

from decimal import Decimal
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from liftra.core.models.base import BaseModel


class CompensationType(str, Enum):
    """Type of compensation."""

    CASH = "cash"
    VOUCHER = "voucher"
    CREDIT = "credit"
    REPLACEMENT = "replacement"
    REFUND = "refund"
    DISCOUNT = "discount"
    OTHER = "other"


class CompensationStatus(str, Enum):
    """Status of compensation."""

    REQUESTED = "requested"
    APPROVED = "approved"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class Compensation(BaseModel):
    """
    Represents a compensation transaction.
    
    Compensation can be for poor service, quality issues, or other problems.
    It can be linked to original transactions or complaint cases.
    """

    # Compensation details
    amount: Decimal = Field(
        ..., gt=0, description="Amount of the compensation"
    )
    currency_code: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    compensation_type: CompensationType = Field(
        ..., description="Type of compensation"
    )
    
    # Status
    status: CompensationStatus = Field(
        default=CompensationStatus.REQUESTED, description="Current status of the compensation"
    )
    
    # Related entities
    original_transaction_id: UUID | None = Field(
        default=None, description="ID of the original transaction (if applicable)"
    )
    case_id: UUID | None = Field(
        default=None, description="ID of the case/complaint (if applicable)"
    )
    payee_id: UUID | None = Field(
        default=None, description="ID of the payee providing compensation"
    )
    account_id: UUID | None = Field(
        default=None, description="ID of the account for the compensation"
    )
    
    # Transaction reference
    transaction_id: UUID | None = Field(
        default=None, description="ID of the transaction created for this compensation"
    )
    
    # Details
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the compensation"
    )
    reason: str | None = Field(
        default=None, max_length=1000, description="Reason for the compensation"
    )
    
    # Dates
    requested_date: date | None = Field(
        default=None, description="Date when compensation was requested"
    )
    offered_date: date | None = Field(
        default=None, description="Date when compensation was offered"
    )
    accepted_date: date | None = Field(
        default=None, description="Date when compensation was accepted"
    )
    paid_date: date | None = Field(
        default=None, description="Date when compensation was paid"
    )
    
    # Reference
    reference: str | None = Field(
        default=None, max_length=255, description="Compensation reference number"
    )
    
    # Budget impact
    exclude_from_budget: bool = Field(
        default=True, description="Whether to exclude this compensation from budget calculations"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"Compensation: {self.amount} {self.currency_code} ({self.compensation_type.value})"
    
    @property
    def is_paid(self) -> bool:
        """Check if the compensation has been paid."""
        return self.status == CompensationStatus.PAID
    
    @property
    def is_pending(self) -> bool:
        """Check if the compensation is pending."""
        return self.status in [
            CompensationStatus.REQUESTED,
            CompensationStatus.APPROVED,
            CompensationStatus.OFFERED,
            CompensationStatus.ACCEPTED
        ]
