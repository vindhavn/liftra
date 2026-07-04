"""
Core domain models for Liftra.

This module contains all the Pydantic models that represent the domain entities
in the Liftra personal finance application.
"""

from liftra.core.models.base import BaseModel, BaseConfig
from liftra.core.models.account import Account, AccountType, AccountStatus
from liftra.core.models.transaction import (
    Transaction,
    TransactionType,
    TransactionDate,
    TransactionDateType,
    TransactionStatus,
)
from liftra.core.models.category import Category
from liftra.core.models.payee import Payee, PayeeLocation
from liftra.core.models.tag import Tag
from liftra.core.models.attachment import Attachment
from liftra.core.models.currency import Currency, ExchangeRate
from liftra.core.models.refund import Refund
from liftra.core.models.compensation import Compensation
from liftra.core.models.tax import TaxDeduction, TaxType
from liftra.core.models.pension import PensionContribution, PensionScheme, PensionType
from liftra.core.models.investment import (
    Investment,
    InvestmentType,
    InvestmentFund,
    InvestmentTransaction,
    InvestmentTransactionType,
)
from liftra.core.models.bill_split import (
    BillSplitGroup,
    BillSplitParticipant,
    BillSplitExpense,
    BillSplitUsage,
)
from liftra.core.models.budget import Budget, BudgetType, BudgetCategory
from liftra.core.models.forecast import Forecast, ForecastType

__all__ = [
    # Base
    "BaseModel",
    "BaseConfig",
    # Account
    "Account",
    "AccountType",
    "AccountStatus",
    # Transaction
    "Transaction",
    "TransactionType",
    "TransactionDate",
    "TransactionDateType",
    "TransactionStatus",
    # Category
    "Category",
    # Payee
    "Payee",
    "PayeeLocation",
    # Tag
    "Tag",
    # Attachment
    "Attachment",
    # Currency
    "Currency",
    "ExchangeRate",
    # Refund
    "Refund",
    # Compensation
    "Compensation",
    # Tax
    "TaxDeduction",
    "TaxType",
    # Pension
    "PensionContribution",
    "PensionScheme",
    "PensionType",
    # Investment
    "Investment",
    "InvestmentType",
    "InvestmentFund",
    "InvestmentTransaction",
    "InvestmentTransactionType",
    # Bill Split
    "BillSplitGroup",
    "BillSplitParticipant",
    "BillSplitExpense",
    "BillSplitUsage",
    # Budget
    "Budget",
    "BudgetType",
    "BudgetCategory",
    # Forecast
    "Forecast",
    "ForecastType",
]
