"""
Repository classes for Liftra.

This module provides repository classes for accessing and managing domain entities.
"""

# Repositories will be implemented in future
# For now, we'll create stub classes to allow imports

from typing import Any, Generic, TypeVar
from uuid import UUID

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository class."""
    
    def __init__(self) -> None:
        pass


class AccountRepository(BaseRepository):
    """Repository for Account entities."""
    pass


class TransactionRepository(BaseRepository):
    """Repository for Transaction entities."""
    pass


class CategoryRepository(BaseRepository):
    """Repository for Category entities."""
    pass


class PayeeRepository(BaseRepository):
    """Repository for Payee entities."""
    pass


class CurrencyRepository(BaseRepository):
    """Repository for Currency entities."""
    pass


class ExchangeRateRepository(BaseRepository):
    """Repository for ExchangeRate entities."""
    pass


class InvestmentRepository(BaseRepository):
    """Repository for Investment entities."""
    pass


class BillSplitRepository(BaseRepository):
    """Repository for BillSplit entities."""
    pass


class BudgetRepository(BaseRepository):
    """Repository for Budget entities."""
    pass


class ForecastRepository(BaseRepository):
    """Repository for Forecast entities."""
    pass


__all__ = [
    "BaseRepository",
    "AccountRepository",
    "TransactionRepository",
    "CategoryRepository",
    "PayeeRepository",
    "CurrencyRepository",
    "ExchangeRateRepository",
    "InvestmentRepository",
    "BillSplitRepository",
    "BudgetRepository",
    "ForecastRepository",
]
