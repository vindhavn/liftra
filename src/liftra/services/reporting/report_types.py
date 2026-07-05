"""
Report types and configurations for Liftra.
"""

from enum import Enum
from typing import Any


class ReportType(str, Enum):
    """Types of reports available in Liftra."""

    ACCOUNT_STATEMENT = "account_statement"
    SPENDING_BY_CATEGORY = "spending_by_category"
    SPENDING_BY_PAYEE = "spending_by_payee"
    BUDGET_VS_ACTUAL = "budget_vs_actual"
    NET_WORTH = "net_worth"
    INVESTMENT_PERFORMANCE = "investment_performance"
    TAX_SUMMARY = "tax_summary"
    BILL_SPLITTING_SUMMARY = "bill_splitting_summary"
    TRANSACTION_HISTORY = "transaction_history"
    REFUND_COMPENSATION = "refund_compensation"


# Report configurations
REPORT_CONFIG = {
    ReportType.ACCOUNT_STATEMENT: {
        "name": "Account Statement",
        "description": "Transactions for an account over a period",
        "entity_type": "Transaction",
        "default_period": "month",
        "supports_pdf": True,
        "supports_charts": True,
    },
    ReportType.SPENDING_BY_CATEGORY: {
        "name": "Spending by Category",
        "description": "Breakdown of spending by category",
        "entity_type": "Transaction",
        "default_period": "month",
        "supports_pdf": True,
        "supports_charts": True,
    },
    ReportType.SPENDING_BY_PAYEE: {
        "name": "Spending by Payee",
        "description": "Breakdown of spending by payee",
        "entity_type": "Transaction",
        "default_period": "month",
        "supports_pdf": True,
        "supports_charts": True,
    },
    ReportType.BUDGET_VS_ACTUAL: {
        "name": "Budget vs. Actual",
        "description": "Comparison of budgeted vs. actual spending",
        "entity_type": "Budget",
        "default_period": "month",
        "supports_pdf": True,
        "supports_charts": True,
    },
    ReportType.NET_WORTH: {
        "name": "Net Worth",
        "description": "Net worth over time",
        "entity_type": "Account",
        "default_period": "year",
        "supports_pdf": True,
        "supports_charts": True,
    },
    ReportType.INVESTMENT_PERFORMANCE: {
        "name": "Investment Performance",
        "description": "Investment returns and fees",
        "entity_type": "Investment",
        "default_period": "year",
        "supports_pdf": True,
        "supports_charts": True,
    },
    ReportType.TAX_SUMMARY: {
        "name": "Tax Summary",
        "description": "Annual tax deductions and pension contributions",
        "entity_type": "Tax",
        "default_period": "year",
        "supports_pdf": True,
        "supports_charts": False,
    },
    ReportType.BILL_SPLITTING_SUMMARY: {
        "name": "Bill Splitting Summary",
        "description": "Group expense summaries and balances",
        "entity_type": "BillSplit",
        "default_period": "month",
        "supports_pdf": True,
        "supports_charts": True,
    },
    ReportType.TRANSACTION_HISTORY: {
        "name": "Transaction History",
        "description": "Full transaction history with filtering",
        "entity_type": "Transaction",
        "default_period": "all",
        "supports_pdf": True,
        "supports_charts": False,
    },
    ReportType.REFUND_COMPENSATION: {
        "name": "Refund & Compensation",
        "description": "Refund and compensation tracking",
        "entity_type": "Refund",
        "default_period": "year",
        "supports_pdf": True,
        "supports_charts": False,
    },
}


class ReportConfig:
    """Configuration for a specific report."""
    
    def __init__(
        self,
        report_type: ReportType,
        start_date: str | None = None,
        end_date: str | None = None,
        account_id: str | None = None,
        category_id: str | None = None,
        payee_id: str | None = None,
        group_by: str = "month",
        sort_by: str = "date",
        sort_direction: str = "desc",
        include_charts: bool = True,
        output_format: str = "pdf",
    ) -> None:
        """
        Initialize report configuration.
        
        Args:
            report_type: Type of report to generate
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            account_id: Filter by account ID
            category_id: Filter by category ID
            payee_id: Filter by payee ID
            group_by: Group results by (day, week, month, year, category, payee)
            sort_by: Sort results by field
            sort_direction: Sort direction (asc or desc)
            include_charts: Whether to include charts in PDF
            output_format: Output format (pdf, html, csv, json)
        """
        self.report_type = report_type
        self.start_date = start_date
        self.end_date = end_date
        self.account_id = account_id
        self.category_id = category_id
        self.payee_id = payee_id
        self.group_by = group_by
        self.sort_by = sort_by
        self.sort_direction = sort_direction
        self.include_charts = include_charts
        self.output_format = output_format
    
    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "report_type": self.report_type.value,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "account_id": self.account_id,
            "category_id": self.category_id,
            "payee_id": self.payee_id,
            "group_by": self.group_by,
            "sort_by": self.sort_by,
            "sort_direction": self.sort_direction,
            "include_charts": self.include_charts,
            "output_format": self.output_format,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReportConfig":
        """Create configuration from dictionary."""
        return cls(
            report_type=ReportType(data.get("report_type", "account_statement")),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            account_id=data.get("account_id"),
            category_id=data.get("category_id"),
            payee_id=data.get("payee_id"),
            group_by=data.get("group_by", "month"),
            sort_by=data.get("sort_by", "date"),
            sort_direction=data.get("sort_direction", "desc"),
            include_charts=data.get("include_charts", True),
            output_format=data.get("output_format", "pdf"),
        )
