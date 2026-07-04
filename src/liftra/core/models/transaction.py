"""
Transaction models for Liftra.
"""

from decimal import Decimal
from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from liftra.core.models.base import BaseModel


class TransactionType(str, Enum):
    """Types of financial transactions."""

    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    REFUND = "refund"
    COMPENSATION = "compensation"
    FEE = "fee"
    INTEREST = "interest"
    DIVIDEND = "dividend"
    CAPITAL_GAIN = "capital_gain"
    TAX = "tax"
    PENSION_CONTRIBUTION = "pension_contribution"
    INVESTMENT = "investment"
    OTHER = "other"


class TransactionDateType(str, Enum):
    """Types of dates associated with a transaction."""

    LOGICAL = "logical"  # When the transaction was made/agreed
    CLEARING = "clearing"  # When the transaction clears in the account
    USAGE = "usage"  # When a good/service was received or used
    DUE = "due"  # When payment is due
    PAYMENT = "payment"  # When payment was made
    CUSTOM = "custom"  # Custom date type


class TransactionStatus(str, Enum):
    """Status of a transaction."""

    PENDING = "pending"
    CLEARED = "cleared"
    RECONCILED = "reconciled"
    VOIDED = "voided"
    DUPLICATE = "duplicate"


class TransactionDate(BaseModel):
    """
    Represents a date associated with a transaction.
    
    Transactions can have multiple dates of different types.
    """

    date_type: TransactionDateType = Field(
        ..., description="Type of the date"
    )
    date_value: date = Field(
        ..., description="The date value"
    )
    description: str | None = Field(
        default=None, max_length=500, description="Description of this date"
    )
    is_primary: bool = Field(
        default=False, description="Whether this is the primary date for the transaction"
    )

    def __str__(self) -> str:
        return f"{self.date_type.value}: {self.date_value.isoformat()}"


class Transaction(BaseModel):
    """
    Represents a financial transaction.
    
    Transactions are the core entity in Liftra, representing any financial
    movement between accounts, to/from payees, or within an account.
    """

    # Transaction details
    description: str = Field(
        ..., min_length=1, max_length=1000, description="Description of the transaction"
    )
    transaction_type: TransactionType = Field(
        ..., description="Type of the transaction"
    )
    status: TransactionStatus = Field(
        default=TransactionStatus.CLEARED, description="Current status of the transaction"
    )
    
    # Amount and currency
    amount: Decimal = Field(
        ..., description="Amount of the transaction (positive for income, negative for expense)"
    )
    currency_code: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    
    # Account
    account_id: UUID = Field(
        ..., description="ID of the account this transaction belongs to"
    )
    
    # Related entities
    category_id: UUID | None = Field(
        default=None, description="ID of the category for this transaction"
    )
    payee_id: UUID | None = Field(
        default=None, description="ID of the payee for this transaction"
    )
    
    # For transfer transactions
    related_transaction_id: UUID | None = Field(
        default=None, description="ID of related transaction (for transfers)"
    )
    
    # For refund/compensation transactions
    original_transaction_id: UUID | None = Field(
        default=None, description="ID of original transaction (for refunds/compensation)"
    )
    
    # Dates - stored as a list of TransactionDate objects
    dates: list[TransactionDate] = Field(
        default_factory=list, description="List of dates associated with this transaction"
    )
    
    # Tags
    tag_ids: list[UUID] = Field(
        default_factory=list, description="List of tag IDs for this transaction"
    )
    
    # Attachments
    attachment_ids: list[UUID] = Field(
        default_factory=list, description="List of attachment IDs for this transaction"
    )
    
    # Conversion (for foreign currency transactions)
    conversion_rate: Decimal | None = Field(
        default=None, description="Exchange rate used for conversion"
    )
    converted_amount: Decimal | None = Field(
        default=None, description="Amount in account's base currency"
    )
    
    # Reconciliation
    is_reconciled: bool = Field(
        default=False, description="Whether the transaction has been reconciled"
    )
    reconciliation_date: date | None = Field(
        default=None, description="Date when the transaction was reconciled"
    )
    statement_reference: str | None = Field(
        default=None, max_length=255, description="Reference from bank statement"
    )
    
    # Metadata
    reference: str | None = Field(
        default=None, max_length=255, description="User-defined reference"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    
    # Budget tracking
    budget_category_id: UUID | None = Field(
        default=None, description="ID of the budget category for this transaction"
    )
    
    # For bill splitting
    bill_split_expense_id: UUID | None = Field(
        default=None, description="ID of the bill split expense (if applicable)"
    )
    
    @field_validator("currency_code")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """Validate that currency code is uppercase."""
        return v.upper()
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount precision."""
        return v.quantize(Decimal("0.0001"))
    
    @field_validator("conversion_rate", "converted_amount")
    @classmethod
    def validate_conversion(cls, v: Decimal | None) -> Decimal | None:
        """Validate conversion precision."""
        if v is not None:
            return v.quantize(Decimal("0.000001"))
        return v
    
    @property
    def is_income(self) -> bool:
        """Check if this is an income transaction."""
        return self.transaction_type in [
            TransactionType.INCOME,
            TransactionType.REFUND,
            TransactionType.COMPENSATION,
            TransactionType.INTEREST,
            TransactionType.DIVIDEND,
            TransactionType.CAPITAL_GAIN,
        ]
    
    @property
    def is_expense(self) -> bool:
        """Check if this is an expense transaction."""
        return self.transaction_type in [
            TransactionType.EXPENSE,
            TransactionType.FEE,
            TransactionType.TAX,
            TransactionType.PENSION_CONTRIBUTION,
        ]
    
    @property
    def is_transfer(self) -> bool:
        """Check if this is a transfer transaction."""
        return self.transaction_type == TransactionType.TRANSFER
    
    @property
    def logical_date(self) -> date | None:
        """Get the logical date (when transaction was made/agreed)."""
        for dt in self.dates:
            if dt.date_type == TransactionDateType.LOGICAL:
                return dt.date_value
        # Fallback to first date if no logical date
        return self.dates[0].date_value if self.dates else None
    
    @property
    def clearing_date(self) -> date | None:
        """Get the clearing date (when transaction clears)."""
        for dt in self.dates:
            if dt.date_type == TransactionDateType.CLEARING:
                return dt.date_value
        return None
    
    @property
    def usage_dates(self) -> list[date]:
        """Get all usage dates."""
        return [dt.date_value for dt in self.dates if dt.date_type == TransactionDateType.USAGE]
    
    def __str__(self) -> str:
        date_str = self.logical_date.isoformat() if self.logical_date else "?"
        return f"{date_str}: {self.description} ({self.amount} {self.currency_code})"
