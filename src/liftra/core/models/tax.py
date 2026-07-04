"""
Tax models for Liftra.
"""

from decimal import Decimal
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from liftra.core.models.base import BaseModel


class TaxType(str, Enum):
    """Types of UK taxes."""

    INCOME_TAX = "income_tax"
    NATIONAL_INSURANCE = "national_insurance"
    STUDENT_LOAN = "student_loan"
    CAPITAL_GAINS_TAX = "capital_gains_tax"
    DIVIDEND_TAX = "dividend_tax"
    VAT = "vat"
    CORPORATION_TAX = "corporation_tax"
    OTHER = "other"


class TaxDeduction(BaseModel):
    """
    Represents a tax deduction.
    
    This tracks tax deductions from wages, including income tax,
    National Insurance, and student loan repayments.
    """

    # Tax details
    tax_type: TaxType = Field(
        ..., description="Type of tax"
    )
    amount: Decimal = Field(
        ..., gt=0, description="Amount of tax deducted"
    )
    currency_code: str = Field(
        default="GBP", min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    
    # Period
    tax_year: str = Field(
        ..., description="UK tax year (e.g., '2023-24')"
    )
    period_start: date | None = Field(
        default=None, description="Start date of the tax period"
    )
    period_end: date | None = Field(
        default=None, description="End date of the tax period"
    )
    
    # Related entities
    account_id: UUID | None = Field(
        default=None, description="ID of the account from which tax was deducted"
    )
    transaction_id: UUID | None = Field(
        default=None, description="ID of the transaction for this deduction"
    )
    employer_id: UUID | None = Field(
        default=None, description="ID of the employer (payee)"
    )
    
    # Tax code
    tax_code: str | None = Field(
        default=None, max_length=20, description="UK tax code"
    )
    
    # Rates
    rate: Decimal | None = Field(
        default=None, description="Tax rate applied"
    )
    
    # Status
    is_estimated: bool = Field(
        default=False, description="Whether the amount is estimated"
    )
    is_verified: bool = Field(
        default=False, description="Whether the deduction has been verified"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"{self.tax_type.value}: {self.amount} {self.currency_code} ({self.tax_year})"
