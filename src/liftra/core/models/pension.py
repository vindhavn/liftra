"""
Pension models for Liftra.
"""

from decimal import Decimal
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from liftra.core.models.base import BaseModel


class PensionType(str, Enum):
    """Types of pension schemes."""

    DEFINED_CONTRIBUTION = "defined_contribution"
    DEFINED_BENEFIT = "defined_benefit"
    STATE_PENSION = "state_pension"
    PERSONAL_PENSION = "personal_pension"
    WORKPLACE_PENSION = "workplace_pension"
    SIPP = "sipp"
    STAKEHOLDER = "stakeholder"
    OTHER = "other"


class PensionScheme(BaseModel):
    """
    Represents a pension scheme.
    """

    # Scheme details
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the pension scheme"
    )
    pension_type: PensionType = Field(
        ..., description="Type of pension scheme"
    )
    provider: str | None = Field(
        default=None, max_length=255, description="Pension provider"
    )
    provider_reference: str | None = Field(
        default=None, max_length=255, description="Provider reference number"
    )
    
    # Status
    is_active: bool = Field(
        default=True, description="Whether the scheme is active"
    )
    start_date: date | None = Field(
        default=None, description="Date when the scheme started"
    )
    end_date: date | None = Field(
        default=None, description="Date when the scheme ended"
    )
    
    # Current value
    current_value: Decimal | None = Field(
        default=None, description="Current value of the pension"
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
        return f"{self.name} ({self.pension_type.value})"


class PensionContribution(BaseModel):
    """
    Represents a pension contribution.
    """

    # Contribution details
    scheme_id: UUID = Field(
        ..., description="ID of the pension scheme"
    )
    amount: Decimal = Field(
        ..., gt=0, description="Amount of the contribution"
    )
    currency_code: str = Field(
        default="GBP", min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    
    # Type
    contribution_type: str = Field(
        default="employee", description="Type of contribution (employee, employer, tax_relief)"
    )
    
    # Dates
    contribution_date: date = Field(
        ..., description="Date of the contribution"
    )
    period_start: date | None = Field(
        default=None, description="Start date of the contribution period"
    )
    period_end: date | None = Field(
        default=None, description="End date of the contribution period"
    )
    
    # Related entities
    account_id: UUID | None = Field(
        default=None, description="ID of the account from which contribution was made"
    )
    transaction_id: UUID | None = Field(
        default=None, description="ID of the transaction for this contribution"
    )
    employer_id: UUID | None = Field(
        default=None, description="ID of the employer (if applicable)"
    )
    
    # Tax relief
    tax_relief_amount: Decimal | None = Field(
        default=None, description="Amount of tax relief received"
    )
    tax_relief_method: str | None = Field(
        default=None, max_length=50, description="Method of tax relief (net_pay, relief_at_source, etc.)"
    )
    
    # Status
    is_verified: bool = Field(
        default=False, description="Whether the contribution has been verified"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"Contribution to {self.scheme_id}: {self.amount} {self.currency_code}"
