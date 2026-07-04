"""
Investment models for Liftra.
"""

from decimal import Decimal
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from liftra.core.models.base import BaseModel


class InvestmentType(str, Enum):
    """Types of investments."""

    ISA = "isa"
    SIPP = "sipp"
    GENERAL_INVESTMENT = "general_investment"
    WORKPLACE_PENSION = "workplace_pension"
    STOCKS_AND_SHARES = "stocks_and_shares"
    CASH_ISA = "cash_isa"
    LIFETIME_ISA = "lifetime_isa"
    JUNIOR_ISA = "junior_isa"
    OTHER = "other"


class InvestmentTransactionType(str, Enum):
    """Types of investment transactions."""

    CONTRIBUTION = "contribution"
    WITHDRAWAL = "withdrawal"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    CAPITAL_GAIN = "capital_gain"
    CAPITAL_LOSS = "capital_loss"
    FEE = "fee"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    REINVESTMENT = "reinvestment"
    OTHER = "other"


class Investment(BaseModel):
    """
    Represents an investment account or portfolio.
    """

    # Investment details
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the investment"
    )
    investment_type: InvestmentType = Field(
        ..., description="Type of investment"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the investment"
    )
    
    # Account information
    account_number: str | None = Field(
        default=None, max_length=100, description="Investment account number"
    )
    provider: str | None = Field(
        default=None, max_length=255, description="Investment provider"
    )
    
    # Status
    is_active: bool = Field(
        default=True, description="Whether the investment is active"
    )
    opened_date: date | None = Field(
        default=None, description="Date when the investment was opened"
    )
    closed_date: date | None = Field(
        default=None, description="Date when the investment was closed"
    )
    
    # Current value
    current_value: Decimal | None = Field(
        default=None, description="Current value of the investment"
    )
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
        return f"{self.name} ({self.investment_type.value})"


class InvestmentFund(BaseModel):
    """
    Represents a fund within an investment.
    """

    # Fund details
    investment_id: UUID = Field(
        ..., description="ID of the parent investment"
    )
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the fund"
    )
    identifier: str | None = Field(
        default=None, max_length=100, description="Fund identifier (ISIN, SEDOL, etc.)"
    )
    identifier_type: str | None = Field(
        default=None, max_length=50, description="Type of identifier"
    )
    
    # Fund information
    fund_type: str | None = Field(
        default=None, max_length=100, description="Type of fund (equity, bond, etc.)"
    )
    asset_class: str | None = Field(
        default=None, max_length=100, description="Asset class"
    )
    region: str | None = Field(
        default=None, max_length=100, description="Geographic region"
    )
    sector: str | None = Field(
        default=None, max_length=100, description="Sector"
    )
    
    # Current holding
    units: Decimal | None = Field(
        default=None, description="Number of units held"
    )
    unit_price: Decimal | None = Field(
        default=None, description="Current unit price"
    )
    current_value: Decimal | None = Field(
        default=None, description="Current value of the holding"
    )
    currency_code: str = Field(
        default="GBP", min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    
    # Performance
    purchase_price: Decimal | None = Field(
        default=None, description="Purchase price per unit"
    )
    total_contributed: Decimal | None = Field(
        default=None, description="Total amount contributed to this fund"
    )
    
    # Status
    is_active: bool = Field(
        default=True, description="Whether the fund holding is active"
    )
    purchase_date: date | None = Field(
        default=None, description="Date when the fund was purchased"
    )
    sale_date: date | None = Field(
        default=None, description="Date when the fund was sold"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"{self.name} ({self.identifier or 'N/A'})"


class InvestmentTransaction(BaseModel):
    """
    Represents a transaction within an investment.
    """

    # Transaction details
    investment_id: UUID = Field(
        ..., description="ID of the parent investment"
    )
    fund_id: UUID | None = Field(
        default=None, description="ID of the fund (if applicable)"
    )
    transaction_type: InvestmentTransactionType = Field(
        ..., description="Type of investment transaction"
    )
    
    # Amount
    amount: Decimal = Field(
        ..., description="Amount of the transaction"
    )
    units: Decimal | None = Field(
        default=None, description="Number of units (for fund transactions)"
    )
    unit_price: Decimal | None = Field(
        default=None, description="Unit price (for fund transactions)"
    )
    currency_code: str = Field(
        default="GBP", min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    
    # Dates
    transaction_date: date = Field(
        ..., description="Date of the transaction"
    )
    settlement_date: date | None = Field(
        default=None, description="Settlement date"
    )
    
    # Related entities
    account_id: UUID | None = Field(
        default=None, description="ID of the account used for the transaction"
    )
    transaction_id: UUID | None = Field(
        default=None, description="ID of the related transaction"
    )
    
    # Fees
    fee_amount: Decimal | None = Field(
        default=None, description="Fee amount for this transaction"
    )
    fee_type: str | None = Field(
        default=None, max_length=100, description="Type of fee"
    )
    
    # Description
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the transaction"
    )
    reference: str | None = Field(
        default=None, max_length=255, description="Transaction reference"
    )
    
    # Status
    is_verified: bool = Field(
        default=False, description="Whether the transaction has been verified"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"{self.transaction_type.value}: {self.amount} {self.currency_code}"
