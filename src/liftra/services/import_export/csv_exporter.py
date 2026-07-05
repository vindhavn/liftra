"""
CSV exporter for Liftra.

Provides functionality to export transactions and accounts to CSV files.
"""

import csv
from datetime import date
from pathlib import Path
from typing import Any

from liftra.core.models import Account, Transaction
from liftra.services.import_export.format_detector import ImportFormat


class CSVExportError(Exception):
    """Exception raised during CSV export."""
    pass


class CSVExporter:
    """
    Exports financial data to CSV files.
    
    Supports exporting both accounts and transactions with configurable columns.
    """
    
    # Default columns for export
    DEFAULT_ACCOUNT_COLUMNS = [
        "id",
        "name",
        "account_type",
        "currency_code",
        "current_balance",
        "available_balance",
        "status",
        "description",
        "institution_name",
        "account_number",
        "opened_date",
        "closed_date",
        "created_at",
        "updated_at",
    ]
    
    DEFAULT_TRANSACTION_COLUMNS = [
        "id",
        "description",
        "transaction_type",
        "amount",
        "currency_code",
        "account_id",
        "category_id",
        "payee_id",
        "logical_date",
        "clearing_date",
        "status",
        "notes",
        "tags",
        "created_at",
        "updated_at",
    ]
    
    def __init__(self, delimiter: str = ",", quotechar: str = '"') -> None:
        """
        Initialize the CSV exporter.
        
        Args:
            delimiter: CSV delimiter character
            quotechar: CSV quote character
        """
        self.delimiter = delimiter
        self.quotechar = quotechar
    
    def export_file(
        self,
        file_path: str | Path,
        entities: list[dict[str, Any]],
        entity_type: str = "transaction",
        columns: list[str] | None = None,
        include_header: bool = True,
    ) -> Path:
        """
        Export entities to a CSV file.
        
        Args:
            file_path: Path to the output CSV file
            entities: List of entity dictionaries to export
            entity_type: Type of entity ("account" or "transaction")
            columns: List of columns to include (None for defaults)
            include_header: Whether to include header row
            
        Returns:
            Path to the exported file
            
        Raises:
            CSVExportError: If export fails
        """
        path = Path(file_path)
        
        # Get columns
        if columns is None:
            if entity_type == "account":
                columns = self.DEFAULT_ACCOUNT_COLUMNS
            else:
                columns = self.DEFAULT_TRANSACTION_COLUMNS
        
        # Filter columns to only those present in entities
        available_columns = set()
        for entity in entities:
            available_columns.update(entity.keys())
        
        columns = [c for c in columns if c in available_columns]
        
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=columns,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar,
                    quoting=csv.QUOTE_MINIMAL,
                )
                
                if include_header:
                    writer.writeheader()
                
                for entity in entities:
                    # Flatten nested structures
                    flat_entity = self._flatten_entity(entity, entity_type)
                    row = {k: v for k, v in flat_entity.items() if k in columns}
                    writer.writerow(row)
        except Exception as e:
            raise CSVExportError(f"Failed to export CSV file: {e}")
        
        return path
    
    def _flatten_entity(self, entity: dict[str, Any], entity_type: str) -> dict[str, Any]:
        """
        Flatten nested entity structures for CSV export.
        
        Args:
            entity: Entity dictionary
            entity_type: Type of entity
            
        Returns:
            Flattened entity dictionary
        """
        flat_entity = entity.copy()
        
        if entity_type == "transaction":
            # Extract dates
            if "dates" in flat_entity and isinstance(flat_entity["dates"], list):
                for date_info in flat_entity["dates"]:
                    if isinstance(date_info, dict):
                        date_type = date_info.get("date_type", "")
                        date_value = date_info.get("date_value", "")
                        
                        if date_type == "logical":
                            flat_entity["logical_date"] = date_value
                        elif date_type == "clearing":
                            flat_entity["clearing_date"] = date_value
            
            # Remove nested dates
            flat_entity.pop("dates", None)
        
        # Convert complex types to strings
        for key, value in flat_entity.items():
            if isinstance(value, (date,)):
                flat_entity[key] = value.isoformat()
            elif isinstance(value, list):
                flat_entity[key] = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                flat_entity[key] = str(value)
        
        return flat_entity
    
    def export_to_string(
        self,
        entities: list[dict[str, Any]],
        entity_type: str = "transaction",
        columns: list[str] | None = None,
        include_header: bool = True,
    ) -> str:
        """
        Export entities to a CSV string.
        
        Args:
            entities: List of entity dictionaries to export
            entity_type: Type of entity ("account" or "transaction")
            columns: List of columns to include (None for defaults)
            include_header: Whether to include header row
            
        Returns:
            CSV content as string
        """
        import io
        
        output = io.StringIO()
        
        # Get columns
        if columns is None:
            if entity_type == "account":
                columns = self.DEFAULT_ACCOUNT_COLUMNS
            else:
                columns = self.DEFAULT_TRANSACTION_COLUMNS
        
        # Filter columns to only those present in entities
        available_columns = set()
        for entity in entities:
            available_columns.update(entity.keys())
        
        columns = [c for c in columns if c in available_columns]
        
        writer = csv.DictWriter(
            output,
            fieldnames=columns,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            quoting=csv.QUOTE_MINIMAL,
        )
        
        if include_header:
            writer.writeheader()
        
        for entity in entities:
            flat_entity = self._flatten_entity(entity, entity_type)
            row = {k: v for k, v in flat_entity.items() if k in columns}
            writer.writerow(row)
        
        return output.getvalue()
    
    def export_accounts(
        self,
        file_path: str | Path,
        accounts: list[Account],
        columns: list[str] | None = None,
        include_header: bool = True,
    ) -> Path:
        """
        Export accounts to CSV file.
        
        Args:
            file_path: Path to the output CSV file
            accounts: List of Account objects
            columns: List of columns to include
            include_header: Whether to include header row
            
        Returns:
            Path to the exported file
        """
        account_dicts = [account.to_dict() for account in accounts]
        return self.export_file(file_path, account_dicts, "account", columns, include_header)
    
    def export_transactions(
        self,
        file_path: str | Path,
        transactions: list[Transaction],
        columns: list[str] | None = None,
        include_header: bool = True,
    ) -> Path:
        """
        Export transactions to CSV file.
        
        Args:
            file_path: Path to the output CSV file
            transactions: List of Transaction objects
            columns: List of columns to include
            include_header: Whether to include header row
            
        Returns:
            Path to the exported file
        """
        transaction_dicts = [transaction.to_dict() for transaction in transactions]
        return self.export_file(file_path, transaction_dicts, "transaction", columns, include_header)
