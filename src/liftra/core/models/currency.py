"""
Currency models for Liftra.
"""

from decimal import Decimal
from datetime import date
from typing import Any

from pydantic import Field, field_validator

from liftra.core.models.base import BaseModel


class Currency(BaseModel):
    """
    Represents a currency.
    
    Currencies are identified by ISO 4217 codes.
    """

    # Currency details
    code: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code"
    )
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the currency"
    )
    symbol: str | None = Field(
        default=None, max_length=10, description="Currency symbol"
    )
    
    # Formatting
    decimal_digits: int = Field(
        default=2, ge=0, le=10, description="Number of decimal digits"
    )
    rounding: int = Field(
        default=0, ge=0, le=10, description="Rounding increment"
    )
    
    # Status
    is_active: bool = Field(
        default=True, description="Whether the currency is active"
    )
    is_default: bool = Field(
        default=False, description="Whether this is the default currency"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate that currency code is uppercase."""
        return v.upper()
    
    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
    
    @property
    def display_name(self) -> str:
        """Get display name with symbol."""
        if self.symbol:
            return f"{self.symbol} {self.code}"
        return f"{self.code}"


class ExchangeRate(BaseModel):
    """
    Represents an exchange rate between two currencies.
    
    Exchange rates can be historical or current, and can be sourced
    from various providers or manually entered.
    """

    # Currencies
    from_currency: str = Field(
        ..., min_length=3, max_length=3, description="Source currency code"
    )
    to_currency: str = Field(
        ..., min_length=3, max_length=3, description="Target currency code"
    )
    
    # Rate
    rate: Decimal = Field(
        ..., gt=0, description="Exchange rate (amount in to_currency for 1 unit of from_currency)"
    )
    
    # Date and time
    effective_date: date = Field(
        ..., description="Date when the rate is effective"
    )
    recorded_at: date | None = Field(
        default=None, description="When the rate was recorded"
    )
    
    # Source
    source: str | None = Field(
        default=None, max_length=255, description="Source of the rate (e.g., 'ECB', 'Manual')"
    )
    source_reference: str | None = Field(
        default=None, max_length=500, description="Reference to the source"
    )
    
    # Rate type
    is_direct: bool = Field(
        default=True, description="Whether this is a direct rate (from -> to)"
    )
    is_inverse: bool = Field(
        default=False, description="Whether this is an inverse rate (to -> from)"
    )
    
    # Status
    is_current: bool = Field(
        default=True, description="Whether this is the current rate"
    )
    is_verified: bool = Field(
        default=False, description="Whether the rate has been verified"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    @field_validator("from_currency", "to_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate that currency code is uppercase."""
        return v.upper()
    
    @field_validator("rate")
    @classmethod
    def validate_rate(cls, v: Decimal) -> Decimal:
        """Validate rate precision."""
        return v.quantize(Decimal("0.00000001"))
    
    def __str__(self) -> str:
        return f"{self.from_currency} -> {self.to_currency}: {self.rate}"
    
    @property
    def inverse_rate(self) -> Decimal:
        """Get the inverse rate."""
        return Decimal(1) / self.rate
    
    def convert(self, amount: Decimal, from_currency: str | None = None) -> Decimal:
        """
        Convert an amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency (defaults to self.from_currency)
            
        Returns:
            Converted amount
        """
        source_currency = from_currency or self.from_currency
        
        if source_currency == self.from_currency:
            return amount * self.rate
        elif source_currency == self.to_currency:
            return amount / self.rate
        else:
            raise ValueError(f"Cannot convert from {source_currency} with this rate")
