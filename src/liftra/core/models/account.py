"""
Account models for Liftra.
"""

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from liftra.core.models.base import BaseModel


class AccountType(str, Enum):
    """Types of accounts supported by Liftra."""

    BANK = "bank"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    PENSION = "pension"
    LOAN = "loan"
    MORTGAGE = "mortgage"
    OTHER = "other"


class AccountStatus(str, Enum):
    """Status of an account."""

    ACTIVE = "active"
    CLOSED = "closed"
    FROZEN = "frozen"
    ARCHIVED = "archived"


class Account(BaseModel):
    """
    Represents a financial account.
    
    Accounts can be bank accounts, cash, credit cards, investment accounts, etc.
    Each account has a balance and can contain multiple transactions.
    """

    # Account details
    name: str = Field(..., min_length=1, max_length=255, description="Name of the account")
    account_type: AccountType = Field(
        default=AccountType.BANK, description="Type of the account"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the account"
    )
    
    # Status
    status: AccountStatus = Field(
        default=AccountStatus.ACTIVE, description="Current status of the account"
    )
    
    # Balance information
    current_balance: Decimal | None = Field(
        default=None, 
        description="Current balance of the account (calculated from transactions)"
    )
    available_balance: Decimal | None = Field(
        default=None,
        description="Available balance (for accounts with pending transactions)"
    )
    
    # Currency
    currency_code: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    
    # Account identifiers
    account_number: str | None = Field(
        default=None, max_length=100, description="Account number"
    )
    sort_code: str | None = Field(
        default=None, max_length=50, description="Sort code (UK) or routing number"
    )
    iban: str | None = Field(
        default=None, max_length=100, description="International Bank Account Number"
    )
    bic: str | None = Field(
        default=None, max_length=50, description="Bank Identifier Code"
    )
    
    # Institution
    institution_name: str | None = Field(
        default=None, max_length=255, description="Name of the financial institution"
    )
    institution_address: str | None = Field(
        default=None, max_length=1000, description="Address of the financial institution"
    )
    
    # Dates
    opened_date: str | None = Field(
        default=None, description="Date when the account was opened (YYYY-MM-DD)"
    )
    closed_date: str | None = Field(
        default=None, description="Date when the account was closed (YYYY-MM-DD)"
    )
    
    # Settings
    is_default: bool = Field(
        default=False, description="Whether this is the default account"
    )
    allow_negative_balance: bool = Field(
        default=False, description="Whether the account can have a negative balance"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    @field_validator("currency_code")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """Validate that currency code is uppercase."""
        return v.upper()
    
    @field_validator("current_balance", "available_balance")
    @classmethod
    def validate_balance(cls, v: Decimal | None) -> Decimal | None:
        """Validate balance precision."""
        if v is not None:
            # Limit to 4 decimal places for most currencies
            return v.quantize(Decimal("0.0001"))
        return v
    
    def __str__(self) -> str:
        return f"{self.name} ({self.account_type.value})"
    
    @property
    def display_name(self) -> str:
        """Get display name with type."""
        return f"{self.name} ({self.account_type.value})"
    
    @property
    def is_active(self) -> bool:
        """Check if account is active."""
        return self.status == AccountStatus.ACTIVE
