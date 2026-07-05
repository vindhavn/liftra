"""
Report generator for Liftra.

Generates various financial reports from stored data.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from liftra.core.models import Account, Transaction, Budget, Category
from liftra.services.reporting.report_types import ReportType, ReportConfig
from liftra.storage.backends import Query
from liftra.storage.manager import StorageManager


class ReportGenerator:
    """
    Generates financial reports from stored data.
    
    Supports various report types with filtering, grouping, and sorting options.
    """
    
    def __init__(self, storage: StorageManager) -> None:
        """
        Initialize the report generator.
        
        Args:
            storage: Storage manager for accessing data
        """
        self.storage = storage
    
    async def generate_report(
        self,
        report_type: ReportType | str,
        config: ReportConfig | None = None,
    ) -> dict[str, Any]:
        """
        Generate a report of the specified type.
        
        Args:
            report_type: Type of report to generate
            config: Report configuration (optional)
            
        Returns:
            Report data dictionary
        """
        if isinstance(report_type, str):
            report_type = ReportType(report_type)
        
        if config is None:
            config = ReportConfig(report_type)
        
        # Dispatch to specific report generator
        if report_type == ReportType.ACCOUNT_STATEMENT:
            return await self._generate_account_statement(config)
        elif report_type == ReportType.SPENDING_BY_CATEGORY:
            return await self._generate_spending_by_category(config)
        elif report_type == ReportType.SPENDING_BY_PAYEE:
            return await self._generate_spending_by_payee(config)
        elif report_type == ReportType.BUDGET_VS_ACTUAL:
            return await self._generate_budget_vs_actual(config)
        elif report_type == ReportType.NET_WORTH:
            return await self._generate_net_worth(config)
        elif report_type == ReportType.TRANSACTION_HISTORY:
            return await self._generate_transaction_history(config)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
    
    async def _generate_account_statement(
        self,
        config: ReportConfig,
    ) -> dict[str, Any]:
        """
        Generate an account statement report.
        
        Args:
            config: Report configuration
            
        Returns:
            Account statement report data
        """
        # Build query
        filters: dict[str, dict[str, Any]] = {}
        
        if config.account_id:
            filters["account_id"] = {"eq": config.account_id}
        
        if config.start_date:
            filters["dates"] = {
                "any": {
                    "date_type": "logical",
                    "date_value": {"gte": config.start_date}
                }
            }
        
        if config.end_date:
            if "dates" not in filters:
                filters["dates"] = {}
            filters["dates"]["any"] = {
                "date_type": "logical",
                "date_value": {"lte": config.end_date}
            }
        
        query = Query(
            entity_type="Transaction",
            filters=filters,
            limit=1000,
            order_by=[{"field": "dates", "direction": config.sort_direction}],
        )
        
        result = await self.storage.list("Transaction", query)
        transactions = [Transaction.from_dict(t) for t in result.items]
        
        # Get account info
        account = None
        if config.account_id:
            account_data = await self.storage.get("Account", config.account_id)
            account = Account.from_dict(account_data)
        
        # Calculate totals
        total_income = Decimal(0)
        total_expense = Decimal(0)
        
        for transaction in transactions:
            if transaction.is_income:
                total_income += transaction.amount
            elif transaction.is_expense:
                total_expense += transaction.amount
        
        return {
            "report_type": "account_statement",
            "title": f"Account Statement{': ' + account.name if account else ''}",
            "period": {
                "start_date": config.start_date,
                "end_date": config.end_date,
            },
            "account": account.to_dict() if account else None,
            "transactions": [t.to_dict() for t in transactions],
            "totals": {
                "total_income": total_income,
                "total_expense": total_expense,
                "net": total_income - total_expense,
                "transaction_count": len(transactions),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def _generate_spending_by_category(
        self,
        config: ReportConfig,
    ) -> dict[str, Any]:
        """
        Generate a spending by category report.
        
        Args:
            config: Report configuration
            
        Returns:
            Spending by category report data
        """
        # Build query for expenses
        filters: dict[str, dict[str, Any]] = {
            "transaction_type": {"in": ["expense", "fee", "tax"]}
        }
        
        if config.account_id:
            filters["account_id"] = {"eq": config.account_id}
        
        if config.category_id:
            filters["category_id"] = {"eq": config.category_id}
        
        if config.start_date:
            filters["dates"] = {
                "any": {
                    "date_type": "logical",
                    "date_value": {"gte": config.start_date}
                }
            }
        
        if config.end_date:
            if "dates" not in filters:
                filters["dates"] = {}
            filters["dates"]["any"] = {
                "date_type": "logical",
                "date_value": {"lte": config.end_date}
            }
        
        query = Query(
            entity_type="Transaction",
            filters=filters,
            limit=1000,
        )
        
        result = await self.storage.list("Transaction", query)
        transactions = [Transaction.from_dict(t) for t in result.items]
        
        # Group by category
        category_totals: dict[str, dict[str, Any]] = {}
        
        for transaction in transactions:
            category_id = transaction.category_id or "Uncategorized"
            
            if category_id not in category_totals:
                category_totals[category_id] = {
                    "category_id": category_id,
                    "amount": Decimal(0),
                    "transaction_count": 0,
                    "transactions": [],
                }
            
            category_totals[category_id]["amount"] += transaction.amount
            category_totals[category_id]["transaction_count"] += 1
            category_totals[category_id]["transactions"].append(transaction.to_dict())
        
        # Sort by amount (descending by default)
        sorted_categories = sorted(
            category_totals.values(),
            key=lambda x: x["amount"],
            reverse=(config.sort_direction == "desc"),
        )
        
        total_spending = sum(c["amount"] for c in category_totals.values())
        
        return {
            "report_type": "spending_by_category",
            "title": "Spending by Category",
            "period": {
                "start_date": config.start_date,
                "end_date": config.end_date,
            },
            "categories": sorted_categories,
            "totals": {
                "total_spending": total_spending,
                "category_count": len(category_totals),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def _generate_spending_by_payee(
        self,
        config: ReportConfig,
    ) -> dict[str, Any]:
        """
        Generate a spending by payee report.
        
        Args:
            config: Report configuration
            
        Returns:
            Spending by payee report data
        """
        # Build query for expenses
        filters: dict[str, dict[str, Any]] = {
            "transaction_type": {"in": ["expense", "fee", "tax"]}
        }
        
        if config.account_id:
            filters["account_id"] = {"eq": config.account_id}
        
        if config.payee_id:
            filters["payee_id"] = {"eq": config.payee_id}
        
        if config.start_date:
            filters["dates"] = {
                "any": {
                    "date_type": "logical",
                    "date_value": {"gte": config.start_date}
                }
            }
        
        if config.end_date:
            if "dates" not in filters:
                filters["dates"] = {}
            filters["dates"]["any"] = {
                "date_type": "logical",
                "date_value": {"lte": config.end_date}
            }
        
        query = Query(
            entity_type="Transaction",
            filters=filters,
            limit=1000,
        )
        
        result = await self.storage.list("Transaction", query)
        transactions = [Transaction.from_dict(t) for t in result.items]
        
        # Group by payee
        payee_totals: dict[str, dict[str, Any]] = {}
        
        for transaction in transactions:
            payee_id = transaction.payee_id or "Unknown Payee"
            
            if payee_id not in payee_totals:
                payee_totals[payee_id] = {
                    "payee_id": payee_id,
                    "amount": Decimal(0),
                    "transaction_count": 0,
                    "transactions": [],
                }
            
            payee_totals[payee_id]["amount"] += transaction.amount
            payee_totals[payee_id]["transaction_count"] += 1
            payee_totals[payee_id]["transactions"].append(transaction.to_dict())
        
        # Sort by amount (descending by default)
        sorted_payees = sorted(
            payee_totals.values(),
            key=lambda x: x["amount"],
            reverse=(config.sort_direction == "desc"),
        )
        
        total_spending = sum(p["amount"] for p in payee_totals.values())
        
        return {
            "report_type": "spending_by_payee",
            "title": "Spending by Payee",
            "period": {
                "start_date": config.start_date,
                "end_date": config.end_date,
            },
            "payees": sorted_payees,
            "totals": {
                "total_spending": total_spending,
                "payee_count": len(payee_totals),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def _generate_budget_vs_actual(
        self,
        config: ReportConfig,
    ) -> dict[str, Any]:
        """
        Generate a budget vs. actual spending report.
        
        Args:
            config: Report configuration
            
        Returns:
            Budget vs. actual report data
        """
        # Get budgets
        query = Query(
            entity_type="Budget",
            limit=100,
        )
        
        result = await self.storage.list("Budget", query)
        budgets = [Budget.from_dict(b) for b in result.items]
        
        # Get actual spending (expenses)
        filters: dict[str, dict[str, Any]] = {
            "transaction_type": {"in": ["expense", "fee", "tax"]}
        }
        
        if config.start_date:
            filters["dates"] = {
                "any": {
                    "date_type": "logical",
                    "date_value": {"gte": config.start_date}
                }
            }
        
        if config.end_date:
            if "dates" not in filters:
                filters["dates"] = {}
            filters["dates"]["any"] = {
                "date_type": "logical",
                "date_value": {"lte": config.end_date}
            }
        
        query = Query(
            entity_type="Transaction",
            filters=filters,
            limit=1000,
        )
        
        result = await self.storage.list("Transaction", query)
        transactions = [Transaction.from_dict(t) for t in result.items]
        
        # Group actual spending by category
        actual_by_category: dict[str, Decimal] = {}
        
        for transaction in transactions:
            category_id = transaction.category_id or "Uncategorized"
            actual_by_category[category_id] = actual_by_category.get(category_id, Decimal(0)) + transaction.amount
        
        # Compare with budgets
        comparison = []
        
        for budget in budgets:
            category_id = budget.category_id
            budgeted = budget.amount
            actual = actual_by_category.get(category_id, Decimal(0))
            variance = actual - budgeted
            
            comparison.append({
                "category_id": category_id,
                "budgeted": budgeted,
                "actual": actual,
                "variance": variance,
                "variance_percentage": (variance / budgeted * 100) if budgeted != 0 else 0,
            })
        
        # Sort by variance or category
        comparison.sort(
            key=lambda x: x[config.sort_by] if config.sort_by in x else x["category_id"],
            reverse=(config.sort_direction == "desc"),
        )
        
        total_budgeted = sum(c["budgeted"] for c in comparison)
        total_actual = sum(c["actual"] for c in comparison)
        total_variance = total_actual - total_budgeted
        
        return {
            "report_type": "budget_vs_actual",
            "title": "Budget vs. Actual Spending",
            "period": {
                "start_date": config.start_date,
                "end_date": config.end_date,
            },
            "comparison": comparison,
            "totals": {
                "total_budgeted": total_budgeted,
                "total_actual": total_actual,
                "total_variance": total_variance,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def _generate_net_worth(
        self,
        config: ReportConfig,
    ) -> dict[str, Any]:
        """
        Generate a net worth report.
        
        Args:
            config: Report configuration
            
        Returns:
            Net worth report data
        """
        # Get all accounts
        query = Query(
            entity_type="Account",
            limit=100,
        )
        
        result = await self.storage.list("Account", query)
        accounts = [Account.from_dict(a) for a in result.items]
        
        # Calculate net worth by account type
        net_worth_by_type: dict[str, dict[str, Any]] = {}
        
        for account in accounts:
            account_type = account.account_type.value
            balance = account.current_balance or Decimal(0)
            
            if account_type not in net_worth_by_type:
                net_worth_by_type[account_type] = {
                    "account_type": account_type,
                    "balance": Decimal(0),
                    "account_count": 0,
                    "accounts": [],
                }
            
            net_worth_by_type[account_type]["balance"] += balance
            net_worth_by_type[account_type]["account_count"] += 1
            net_worth_by_type[account_type]["accounts"].append(account.to_dict())
        
        # Sort by balance
        sorted_types = sorted(
            net_worth_by_type.values(),
            key=lambda x: x["balance"],
            reverse=True,
        )
        
        total_net_worth = sum(t["balance"] for t in net_worth_by_type.values())
        
        return {
            "report_type": "net_worth",
            "title": "Net Worth",
            "period": {
                "start_date": config.start_date,
                "end_date": config.end_date,
            },
            "by_account_type": sorted_types,
            "totals": {
                "total_net_worth": total_net_worth,
                "account_count": len(accounts),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def _generate_transaction_history(
        self,
        config: ReportConfig,
    ) -> dict[str, Any]:
        """
        Generate a transaction history report.
        
        Args:
            config: Report configuration
            
        Returns:
            Transaction history report data
        """
        # Build query
        filters: dict[str, dict[str, Any]] = {}
        
        if config.account_id:
            filters["account_id"] = {"eq": config.account_id}
        
        if config.category_id:
            filters["category_id"] = {"eq": config.category_id}
        
        if config.payee_id:
            filters["payee_id"] = {"eq": config.payee_id}
        
        if config.start_date:
            filters["dates"] = {
                "any": {
                    "date_type": "logical",
                    "date_value": {"gte": config.start_date}
                }
            }
        
        if config.end_date:
            if "dates" not in filters:
                filters["dates"] = {}
            filters["dates"]["any"] = {
                "date_type": "logical",
                "date_value": {"lte": config.end_date}
            }
        
        query = Query(
            entity_type="Transaction",
            filters=filters,
            limit=1000,
            order_by=[{"field": "dates", "direction": config.sort_direction}],
        )
        
        result = await self.storage.list("Transaction", query)
        transactions = [Transaction.from_dict(t) for t in result.items]
        
        # Calculate totals
        total_income = Decimal(0)
        total_expense = Decimal(0)
        
        for transaction in transactions:
            if transaction.is_income:
                total_income += transaction.amount
            elif transaction.is_expense:
                total_expense += transaction.amount
        
        return {
            "report_type": "transaction_history",
            "title": "Transaction History",
            "period": {
                "start_date": config.start_date,
                "end_date": config.end_date,
            },
            "filters": {
                "account_id": config.account_id,
                "category_id": config.category_id,
                "payee_id": config.payee_id,
            },
            "transactions": [t.to_dict() for t in transactions],
            "totals": {
                "total_income": total_income,
                "total_expense": total_expense,
                "net": total_income - total_expense,
                "transaction_count": len(transactions),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
