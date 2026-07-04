"""
Forecast models for Liftra.
"""

from decimal import Decimal
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from liftra.core.models.base import BaseModel


class ForecastType(str, Enum):
    """Types of forecasts."""

    SPEND = "spend"
    INCOME = "income"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    NET_WORTH = "net_worth"
    CASH_FLOW = "cash_flow"


class ForecastFrequency(str, Enum):
    """Frequency of forecast periods."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class Forecast(BaseModel):
    """
    Represents a financial forecast.
    
    Forecasts project future financial values based on historical data
    and user-defined scenarios.
    """

    # Forecast details
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the forecast"
    )
    forecast_type: ForecastType = Field(
        ..., description="Type of forecast"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the forecast"
    )
    
    # Period
    start_date: date = Field(
        ..., description="Start date of the forecast"
    )
    end_date: date = Field(
        ..., description="End date of the forecast"
    )
    frequency: ForecastFrequency = Field(
        default=ForecastFrequency.MONTHLY, description="Frequency of forecast periods"
    )
    
    # Configuration
    method: str = Field(
        default="historical_average", description="Method used for forecasting"
    )
    confidence_level: Decimal | None = Field(
        default=None, ge=0, le=1, description="Confidence level (0-1)"
    )
    
    # Source data
    account_ids: list[UUID] = Field(
        default_factory=list, description="List of account IDs to include"
    )
    category_ids: list[UUID] = Field(
        default_factory=list, description="List of category IDs to include"
    )
    
    # Results
    forecast_values: dict[str, Decimal] = Field(
        default_factory=dict, description="Forecast values by period"
    )
    actual_values: dict[str, Decimal] = Field(
        default_factory=dict, description="Actual values by period (for comparison)"
    )
    
    # Accuracy
    accuracy_score: Decimal | None = Field(
        default=None, ge=0, le=1, description="Accuracy score of the forecast"
    )
    
    # Status
    is_active: bool = Field(
        default=True, description="Whether the forecast is active"
    )
    last_updated: date | None = Field(
        default=None, description="Date when the forecast was last updated"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    def __str__(self) -> str:
        return f"{self.name} ({self.forecast_type.value})"
    
    @property
    def total_forecast(self) -> Decimal:
        """Get total forecast amount."""
        return sum(self.forecast_values.values())
    
    @property
    def total_actual(self) -> Decimal:
        """Get total actual amount."""
        return sum(self.actual_values.values())
