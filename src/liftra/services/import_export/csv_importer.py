"""
CSV importer for Liftra.

Provides functionality to import transactions and accounts from CSV files.
"""

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from liftra.core.models import (
    Account,
    AccountType,
    Transaction,
    TransactionType,
    TransactionDate,
    TransactionDateType,
)
from liftra.services.import_export.format_detector import ImportFormat


class CSVImportError(Exception):
    """Exception raised during CSV import."""
    pass


class CSVImporter:
    """
    Imports financial data from CSV files.
    
    Supports configurable column mapping and can import both accounts and transactions.
    """
    
    # Default column mappings for common CSV formats
    DEFAULT_ACCOUNT_COLUMNS = {
        "name": "name",
        "type": "type",
        "currency": "currency",
        "description": "description",
        "balance": "balance",
    }
    
    DEFAULT_TRANSACTION_COLUMNS = {
        "date": ["date", "transaction_date", "posted_date"],
        "description": ["description", "memo", "payee", "name"],
        "amount": ["amount", "debit", "credit", "value"],
        "type": ["type", "transaction_type"],
        "category": ["category", "cat"],
        "account": ["account", "account_name", "account_id"],
        "currency": ["currency", "currency_code"],
    }
    
    def __init__(self, delimiter: str = ",", quotechar: str = '"') -> None:
        """
        Initialize the CSV importer.
        
        Args:
            delimiter: CSV delimiter character
            quotechar: CSV quote character
        """
        self.delimiter = delimiter
        self.quotechar = quotechar
    
    def import_file(
        self,
        file_path: str | Path,
        entity_type: str = "transaction",
        column_mapping: dict[str, str | list[str]] | None = None,
        account_id: str | None = None,
        preview: bool = False,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Import data from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            entity_type: Type of entity to import ("account" or "transaction")
            column_mapping: Custom column mapping (source -> target)
            account_id: Default account ID for transactions
            preview: If True, only return first few rows without importing
            limit: Maximum number of rows to import
            
        Returns:
            List of imported entity dictionaries
            
        Raises:
            CSVImportError: If import fails
        """
        path = Path(file_path)
        
        if not path.exists():
            raise CSVImportError(f"File not found: {file_path}")
        
        # Get column mapping
        if column_mapping is None:
            if entity_type == "account":
                column_mapping = self.DEFAULT_ACCOUNT_COLUMNS
            else:
                column_mapping = self.DEFAULT_TRANSACTION_COLUMNS
        
        # Read CSV file
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter, quotechar=self.quotechar)
                rows = list(reader)
        except Exception as e:
            raise CSVImportError(f"Failed to read CSV file: {e}")
        
        if not rows:
            return []
        
        # Process rows
        imported_entities = []
        
        for i, row in enumerate(rows):
            if limit and i >= limit:
                break
            
            try:
                if entity_type == "account":
                    entity = self._process_account_row(row, column_mapping)
                else:
                    entity = self._process_transaction_row(row, column_mapping, account_id)
                
                if entity:
                    imported_entities.append(entity)
                    
                if preview and len(imported_entities) >= 10:
                    break
                    
            except Exception as e:
                # Log error but continue with other rows
                continue
        
        return imported_entities
    
    def _find_column_value(
        self,
        row: dict[str, str],
        column_mapping: dict[str, str | list[str]],
        target_field: str,
    ) -> str | None:
        """
        Find a value in a row based on column mapping.
        
        Args:
            row: CSV row as dictionary
            column_mapping: Column mapping dictionary
            target_field: Target field name
            
        Returns:
            The value if found, None otherwise
        """
        if target_field not in column_mapping:
            return None
        
        possible_sources = column_mapping[target_field]
        if isinstance(possible_sources, str):
            possible_sources = [possible_sources]
        
        for source in possible_sources:
            if source in row:
                return row[source].strip()
        
        return None
    
    def _process_account_row(
        self,
        row: dict[str, str],
        column_mapping: dict[str, str | list[str]],
    ) -> dict[str, Any]:
        """
        Process a CSV row into an account dictionary.
        
        Args:
            row: CSV row as dictionary
            column_mapping: Column mapping dictionary
            
        Returns:
            Account dictionary
        """
        account_data: dict[str, Any] = {}
        
        # Map fields
        if name := self._find_column_value(row, column_mapping, "name"):
            account_data["name"] = name
        
        if acc_type := self._find_column_value(row, column_mapping, "type"):
            account_data["account_type"] = self._normalize_account_type(acc_type)
        
        if currency := self._find_column_value(row, column_mapping, "currency"):
            account_data["currency_code"] = currency.upper()
        else:
            account_data["currency_code"] = "GBP"  # Default to GBP
        
        if description := self._find_column_value(row, column_mapping, "description"):
            account_data["description"] = description
        
        if balance := self._find_column_value(row, column_mapping, "balance"):
            try:
                account_data["current_balance"] = Decimal(balance)
            except InvalidOperation:
                pass
        
        return account_data
    
    def _process_transaction_row(
        self,
        row: dict[str, str],
        column_mapping: dict[str, str | list[str]],
        default_account_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Process a CSV row into a transaction dictionary.
        
        Args:
            row: CSV row as dictionary
            column_mapping: Column mapping dictionary
            default_account_id: Default account ID if not in CSV
            
        Returns:
            Transaction dictionary
        """
        transaction_data: dict[str, Any] = {}
        
        # Map fields
        if description := self._find_column_value(row, column_mapping, "description"):
            transaction_data["description"] = description
        
        if amount_str := self._find_column_value(row, column_mapping, "amount"):
            try:
                amount = Decimal(amount_str)
                # Determine if this is income or expense based on sign
                if amount < 0:
                    transaction_data["transaction_type"] = TransactionType.EXPENSE
                    transaction_data["amount"] = abs(amount)
                else:
                    transaction_data["transaction_type"] = TransactionType.INCOME
                    transaction_data["amount"] = amount
            except InvalidOperation:
                pass
        
        if trans_type := self._find_column_value(row, column_mapping, "type"):
            transaction_data["transaction_type"] = self._normalize_transaction_type(trans_type)
        
        if currency := self._find_column_value(row, column_mapping, "currency"):
            transaction_data["currency_code"] = currency.upper()
        else:
            transaction_data["currency_code"] = "GBP"  # Default to GBP
        
        if category := self._find_column_value(row, column_mapping, "category"):
            transaction_data["category_id"] = category
        
        if account := self._find_column_value(row, column_mapping, "account"):
            transaction_data["account_id"] = account
        elif default_account_id:
            transaction_data["account_id"] = default_account_id
        
        # Handle date
        if date_str := self._find_column_value(row, column_mapping, "date"):
            try:
                # Try various date formats
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
                    try:
                        date_obj = datetime.strptime(date_str, fmt).date()
                        transaction_data["dates"] = [{
                            "date_type": TransactionDateType.LOGICAL,
                            "date_value": date_obj.isoformat(),
                            "is_primary": True
                        }]
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        return transaction_data
    
    def _normalize_account_type(self, acc_type: str) -> AccountType:
        """
        Normalize account type string to AccountType enum.
        
        Args:
            acc_type: Account type string
            
        Returns:
            AccountType enum value
        """
        type_mapping = {
            "bank": AccountType.BANK,
            "current": AccountType.BANK,
            "checking": AccountType.BANK,
            "cash": AccountType.CASH,
            "credit": AccountType.CREDIT_CARD,
            "credit_card": AccountType.CREDIT_CARD,
            "savings": AccountType.SAVINGS,
            "investment": AccountType.INVESTMENT,
            "pension": AccountType.PENSION,
            "loan": AccountType.LOAN,
            "mortgage": AccountType.MORTGAGE,
            "other": AccountType.OTHER,
        }
        
        normalized = acc_type.lower().replace(" ", "_").replace("-", "_")
        return type_mapping.get(normalized, AccountType.OTHER)
    
    def _normalize_transaction_type(self, trans_type: str) -> TransactionType:
        """
        Normalize transaction type string to TransactionType enum.
        
        Args:
            trans_type: Transaction type string
            
        Returns:
            TransactionType enum value
        """
        type_mapping = {
            "income": TransactionType.INCOME,
            "expense": TransactionType.EXPENSE,
            "transfer": TransactionType.TRANSFER,
            "refund": TransactionType.REFUND,
            "compensation": TransactionType.COMPENSATION,
            "fee": TransactionType.FEE,
            "interest": TransactionType.INTEREST,
            "dividend": TransactionType.DIVIDEND,
            "capital_gain": TransactionType.CAPITAL_GAIN,
            "tax": TransactionType.TAX,
            "pension": TransactionType.PENSION_CONTRIBUTION,
            "pension_contribution": TransactionType.PENSION_CONTRIBUTION,
            "investment": TransactionType.INVESTMENT,
            "other": TransactionType.OTHER,
        }
        
        normalized = trans_type.lower().replace(" ", "_").replace("-", "_")
        return type_mapping.get(normalized, TransactionType.OTHER)
    
    def validate_data(
        self,
        entities: list[dict[str, Any]],
        entity_type: str = "transaction",
    ) -> list[dict[str, Any]]:
        """
        Validate imported entities.
        
        Args:
            entities: List of entity dictionaries to validate
            entity_type: Type of entity ("account" or "transaction")
            
        Returns:
            List of valid entities
        """
        valid_entities = []
        
        for entity in entities:
            try:
                if entity_type == "account":
                    Account(**entity)
                else:
                    Transaction(**entity)
                valid_entities.append(entity)
            except Exception:
                # Skip invalid entities
                continue
        
        return valid_entities
    
    def preview_import(
        self,
        file_path: str | Path,
        entity_type: str = "transaction",
        column_mapping: dict[str, str | list[str]] | None = None,
        account_id: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Preview data that would be imported.
        
        Args:
            file_path: Path to the CSV file
            entity_type: Type of entity to import
            column_mapping: Custom column mapping
            account_id: Default account ID for transactions
            limit: Maximum number of rows to preview
            
        Returns:
            Dictionary with preview information
        """
        entities = self.import_file(
            file_path,
            entity_type=entity_type,
            column_mapping=column_mapping,
            account_id=account_id,
            preview=True,
            limit=limit,
        )
        
        valid_entities = self.validate_data(entities, entity_type)
        
        return {
            "total_rows": len(entities),
            "valid_rows": len(valid_entities),
            "invalid_rows": len(entities) - len(valid_entities),
            "sample_data": valid_entities[:min(5, len(valid_entities))],
            "format": ImportFormat.CSV,
        }
