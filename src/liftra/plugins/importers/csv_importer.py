"""
CSV import/export plugin for Liftra.

This module provides CSV format support for importing and exporting financial data.
CSV is a simple, widely-supported format that's ideal for basic data exchange.
"""

import csv
import io
import os
from datetime import datetime
from typing import Any

from liftra.plugins.importers.base import (
    BaseImporter,
    BaseExporter,
    ImportResult,
    ExportResult,
    ImportedTransaction,
    ImportedAccount,
    FormatType,
    ImportError,
    ExportError,
)


class CSVImporter(BaseImporter):
    """
    CSV file importer for financial data.
    
    Supports flexible CSV formats with configurable column mapping.
    """
    
    @property
    def format_type(self) -> FormatType:
        return FormatType.CSV
    
    @property
    def name(self) -> str:
        return "CSV Importer"
    
    @property
    def description(self) -> str:
        return "Import financial data from CSV files with configurable column mapping"
    
    @property
    def file_extensions(self) -> list[str]:
        return [".csv", ".txt"]
    
    def __init__(self) -> None:
        self._default_column_mapping = {
            "date": ["date", "transaction_date", "posted_date", "date_posted"],
            "description": ["description", "memo", "notes", "details"],
            "amount": ["amount", "value", "transaction_amount"],
            "payee": ["payee", "merchant", "vendor", "to_from"],
            "category": ["category", "class", "type"],
            "reference": ["reference", "check_number", "ref", "id"],
            "account": ["account", "account_name", "bank_account"],
            "currency": ["currency", "currency_code", "iso_currency"],
            "type": ["type", "transaction_type", "debit_credit"],
        }
    
    def can_handle_file(self, file_path: str) -> bool:
        """Check if this importer can handle the given file."""
        return file_path.lower().endswith(tuple(self.file_extensions))
    
    def detect_format(self, file_path: str | None = None, content: str | bytes | None = None) -> bool:
        """Detect if the given content is in CSV format."""
        if content is None:
            return False
        
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        
        # Simple CSV detection - look for commas and newlines
        lines = content.strip().split('\n')
        if len(lines) < 2:
            return False
        
        # Check if first line looks like headers (letters and underscores)
        first_line = lines[0].strip()
        if not first_line:
            return False
        
        # Check if it has commas or other delimiters
        has_delimiter = ',' in first_line or ';' in first_line or '\t' in first_line or '|' in first_line
        return has_delimiter
    
    def get_options(self) -> dict[str, Any]:
        """Get configuration options for this importer."""
        return {
            "delimiter": {
                "default": ",",
                "description": "CSV field delimiter",
                "type": "string",
                "choices": [",", ";", "\t", "|"],
            },
            "quotechar": {
                "default": '"',
                "description": "CSV quote character",
                "type": "string",
                "choices": ['"', "'", "`"],
            },
            "encoding": {
                "default": "utf-8",
                "description": "File encoding",
                "type": "string",
                "choices": ["utf-8", "latin-1", "ascii"],
            },
            "header_row": {
                "default": 0,
                "description": "Row number containing headers (0-based)",
                "type": "integer",
                "min": 0,
            },
            "skip_rows": {
                "default": 0,
                "description": "Number of rows to skip at the beginning",
                "type": "integer",
                "min": 0,
            },
            "column_mapping": {
                "default": {},
                "description": "Manual column mapping (column_name -> field_name)",
                "type": "dict",
            },
            "date_format": {
                "default": "%Y-%m-%d",
                "description": "Date format for parsing dates",
                "type": "string",
            },
            "amount_column": {
                "default": "amount",
                "description": "Column containing transaction amounts",
                "type": "string",
            },
            "debit_credit_columns": {
                "default": None,
                "description": "Separate debit and credit columns (tuple of column names)",
                "type": "tuple",
            },
        }
    
    def _detect_column_mapping(
        self, 
        headers: list[str], 
        custom_mapping: dict[str, str] | None = None
    ) -> dict[str, str]:
        """
        Detect the column mapping based on header names.
        
        Args:
            headers: List of header names from CSV
            custom_mapping: Optional custom column mapping
            
        Returns:
            Dictionary mapping field names to column indices
        """
        mapping: dict[str, str] = {}
        
        # Use custom mapping if provided
        if custom_mapping:
            for field_name, column_name in custom_mapping.items():
                if column_name in headers:
                    mapping[field_name] = column_name
        
        # Auto-detect for remaining fields
        for field_name, possible_columns in self._default_column_mapping.items():
            if field_name not in mapping:
                for possible_column in possible_columns:
                    if possible_column in headers:
                        mapping[field_name] = possible_column
                        break
        
        return mapping
    
    def _parse_csv_content(
        self, 
        content: str, 
        options: dict[str, Any] | None = None
    ) -> tuple[list[str], list[list[str]]]:
        """
        Parse CSV content and return headers and rows.
        
        Args:
            content: CSV content as string
            options: Import options
            
        Returns:
            Tuple of (headers, rows)
        """
        if options is None:
            options = {}
        
        delimiter = options.get("delimiter", ",")
        quotechar = options.get("quotechar", '"')
        encoding = options.get("encoding", "utf-8")
        header_row = options.get("header_row", 0)
        skip_rows = options.get("skip_rows", 0)
        
        # Parse CSV
        reader = csv.reader(
            io.StringIO(content),
            delimiter=delimiter,
            quotechar=quotechar
        )
        
        rows = list(reader)
        
        if not rows:
            return [], []
        
        # Skip rows
        if skip_rows > 0:
            rows = rows[skip_rows:]
        
        if not rows:
            return [], []
        
        # Extract headers
        if header_row < len(rows):
            headers = rows[header_row]
            data_rows = rows[header_row + 1:]
        else:
            headers = []
            data_rows = rows
        
        return headers, data_rows
    
    def _parse_row(
        self, 
        row: list[str], 
        headers: list[str],
        column_mapping: dict[str, str],
        options: dict[str, Any] | None = None
    ) -> ImportedTransaction | None:
        """
        Parse a single CSV row into an ImportedTransaction.
        
        Args:
            row: CSV row data
            headers: CSV headers
            column_mapping: Mapping of field names to column names
            options: Import options
            
        Returns:
            ImportedTransaction or None if row is invalid
        """
        if options is None:
            options = {}
        
        transaction = ImportedTransaction()
        date_format = options.get("date_format", "%Y-%m-%d")
        debit_credit_columns = options.get("debit_credit_columns")
        
        # Create a mapping from column name to column index
        col_to_index = {}
        for i, header in enumerate(headers):
            header_clean = header.strip()
            if header_clean:
                col_to_index[header_clean] = i
        
        # Extract data from row
        for field_name, column_name in column_mapping.items():
            if column_name in col_to_index:
                col_index = col_to_index[column_name]
                if col_index < len(row):
                    value = row[col_index].strip()
                    
                    # Handle specific field parsing
                    if field_name == "date" and value:
                        try:
                            # Try multiple date formats
                            for fmt in [date_format, "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m-%d-%Y"]:
                                try:
                                    parsed_date = datetime.strptime(value, fmt)
                                    transaction.date = parsed_date.strftime("%Y-%m-%d")
                                    break
                                except ValueError:
                                    continue
                        except (ValueError, TypeError):
                            pass
                    elif field_name == "amount" and value:
                        # Handle debit/credit columns
                        if debit_credit_columns and isinstance(debit_credit_columns, (list, tuple)) and len(debit_credit_columns) == 2:
                            debit_col, credit_col = debit_credit_columns
                            if debit_col in col_to_index and credit_col in col_to_index:
                                debit_idx = col_to_index[debit_col]
                                credit_idx = col_to_index[credit_col]
                                if debit_idx < len(row) and credit_idx < len(row):
                                    debit_val = row[debit_idx].strip()
                                    credit_val = row[credit_idx].strip()
                                    try:
                                        debit_amount = float(debit_val) if debit_val else 0.0
                                        credit_amount = float(credit_val) if credit_val else 0.0
                                        # Negative for debit, positive for credit
                                        transaction.amount = str(credit_amount - debit_amount)
                                    except ValueError:
                                        pass
                        else:
                            # Handle regular amount column
                            try:
                                transaction.amount = str(float(value))
                            except ValueError:
                                pass
                    elif field_name == "payee":
                        transaction.payee = value
                    elif field_name == "description":
                        transaction.description = value
                    elif field_name == "category":
                        transaction.category = value
                    elif field_name == "reference":
                        transaction.reference = value
                    elif field_name == "currency":
                        transaction.currency_code = value.upper() if value else "GBP"
                    elif field_name == "type":
                        transaction.transaction_type = value.lower()
                    elif field_name == "account":
                        transaction.account_name = value
        
        # Handle debit/credit logic if amount is negative
        if transaction.amount:
            try:
                amount = float(transaction.amount)
                if amount < 0:
                    transaction.transaction_type = "debit"
                elif amount > 0:
                    transaction.transaction_type = "credit"
                else:
                    transaction.transaction_type = "transfer"
            except ValueError:
                pass
        
        # Set default values
        if not transaction.currency_code:
            transaction.currency_code = "GBP"
        if not transaction.transaction_type:
            transaction.transaction_type = "unknown"
        
        return transaction
    
    def import_file(
        self, 
        file_path: str, 
        options: dict[str, Any] | None = None,
        preview_only: bool = False,
        limit: int | None = None
    ) -> ImportResult:
        """Import data from a CSV file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not os.path.isfile(file_path):
            raise ImportError(f"Not a file: {file_path}")
        
        if options is None:
            options = {}
        
        encoding = options.get("encoding", "utf-8")
        
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
        except (IOError, UnicodeDecodeError) as e:
            raise ImportError(f"Failed to read file: {e}")
        
        return self.import_string(content, options, preview_only, limit)
    
    def import_string(
        self,
        content: str | bytes,
        options: dict[str, Any] | None = None,
        preview_only: bool = False,
        limit: int | None = None
    ) -> ImportResult:
        """Import data from a CSV string."""
        if isinstance(content, bytes):
            encoding = "utf-8"
            if options and "encoding" in options:
                encoding = options["encoding"]
            content = content.decode(encoding, errors='ignore')
        
        if options is None:
            options = {}
        
        result = ImportResult(
            format_type=self.format_type,
            source_file=options.get("source_file")
        )
        
        try:
            # Parse CSV content
            headers, rows = self._parse_csv_content(content, options)
            
            if not headers:
                result.errors.append("No headers found in CSV file")
                return result
            
            # Detect column mapping
            custom_mapping = options.get("column_mapping", {})
            column_mapping = self._detect_column_mapping(headers, custom_mapping)
            
            # Parse each row
            for i, row in enumerate(rows):
                if limit and i >= limit:
                    break
                
                transaction = self._parse_row(row, headers, column_mapping, options)
                if transaction:
                    transaction.source_format = self.format_type
                    transaction.source_line = i + 1  # 1-based line number
                    result.transactions.append(transaction)
            
            result.completed_at = datetime.utcnow()
            
        except Exception as e:
            result.errors.append(f"Import failed: {str(e)}")
        
        return result


class CSVExporter(BaseExporter):
    """
    CSV file exporter for financial data.
    
    Exports accounts and transactions to CSV format with configurable options.
    """
    
    @property
    def format_type(self) -> FormatType:
        return FormatType.CSV
    
    @property
    def name(self) -> str:
        return "CSV Exporter"
    
    @property
    def description(self) -> str:
        return "Export financial data to CSV files with configurable format"
    
    @property
    def file_extensions(self) -> list[str]:
        return [".csv", ".txt"]
    
    def get_options(self) -> dict[str, Any]:
        """Get configuration options for this exporter."""
        return {
            "delimiter": {
                "default": ",",
                "description": "CSV field delimiter",
                "type": "string",
                "choices": [",", ";", "\t", "|"],
            },
            "quotechar": {
                "default": '"',
                "description": "CSV quote character",
                "type": "string",
                "choices": ['"', "'", "`"],
            },
            "encoding": {
                "default": "utf-8",
                "description": "File encoding",
                "type": "string",
                "choices": ["utf-8", "latin-1", "ascii"],
            },
            "include_header": {
                "default": True,
                "description": "Include header row",
                "type": "boolean",
            },
            "date_format": {
                "default": "%Y-%m-%d",
                "description": "Date format for output",
                "type": "string",
            },
            "amount_format": {
                "default": "%.2f",
                "description": "Amount format (Python format string)",
                "type": "string",
            },
            "columns": {
                "default": [
                    "date", "description", "payee", "category", 
                    "amount", "currency", "type", "reference"
                ],
                "description": "Columns to include in export",
                "type": "list",
            },
            "account_columns": {
                "default": ["name", "type", "currency", "balance"],
                "description": "Columns to include for accounts",
                "type": "list",
            },
        }
    
    def _format_value(self, value: Any, options: dict[str, Any] | None = None) -> str:
        """Format a value for CSV export."""
        if options is None:
            options = {}
        
        if value is None:
            return ""
        
        if isinstance(value, (list, dict)):
            return str(value)
        
        if isinstance(value, bool):
            return "Yes" if value else "No"
        
        return str(value)
    
    def _format_transaction(self, transaction: dict[str, Any], options: dict[str, Any]) -> list[str]:
        """Format a transaction as a CSV row."""
        columns = options.get("columns", [
            "date", "description", "payee", "category", 
            "amount", "currency", "type", "reference"
        ])
        date_format = options.get("date_format", "%Y-%m-%d")
        amount_format = options.get("amount_format", "%.2f")
        
        row = []
        for col in columns:
            if col in transaction:
                value = transaction[col]
                
                # Format specific types
                if col == "date" and value:
                    try:
                        from datetime import datetime
                        if isinstance(value, str):
                            # Try to parse and reformat
                            try:
                                dt = datetime.strptime(value, "%Y-%m-%d")
                                value = dt.strftime(date_format)
                            except ValueError:
                                pass
                        row.append(value)
                    except Exception:
                        row.append(self._format_value(value))
                elif col == "amount" and value is not None:
                    try:
                        amount = float(value)
                        row.append(amount_format % amount)
                    except (ValueError, TypeError):
                        row.append(self._format_value(value))
                else:
                    row.append(self._format_value(value))
            else:
                row.append("")
        
        return row
    
    def _format_account(self, account: dict[str, Any], options: dict[str, Any]) -> list[str]:
        """Format an account as a CSV row."""
        columns = options.get("account_columns", ["name", "type", "currency", "balance"])
        amount_format = options.get("amount_format", "%.2f")
        
        row = []
        for col in columns:
            if col in account:
                value = account[col]
                
                # Format specific types
                if col == "balance" and value is not None:
                    try:
                        amount = float(value)
                        row.append(amount_format % amount)
                    except (ValueError, TypeError):
                        row.append(self._format_value(value))
                else:
                    row.append(self._format_value(value))
            else:
                row.append("")
        
        return row
    
    def export_data(
        self,
        data: dict[str, Any],
        options: dict[str, Any] | None = None
    ) -> ExportResult:
        """Export data to CSV format."""
        if options is None:
            options = {}
        
        result = ExportResult(
            format_type=self.format_type,
            started_at=datetime.utcnow()
        )
        
        try:
            delimiter = options.get("delimiter", ",")
            quotechar = options.get("quotechar", '"')
            include_header = options.get("include_header", True)
            
            output = io.StringIO()
            writer = csv.writer(output, delimiter=delimiter, quotechar=quotechar)
            
            # Export transactions
            transactions = data.get("transactions", [])
            if transactions:
                # Write header
                columns = options.get("columns", [
                    "date", "description", "payee", "category", 
                    "amount", "currency", "type", "reference"
                ])
                if include_header:
                    writer.writerow(columns)
                
                # Write transaction rows
                for transaction in transactions:
                    row = self._format_transaction(transaction, options)
                    writer.writerow(row)
                
                result.transactions_exported = len(transactions)
            
            # Export accounts
            accounts = data.get("accounts", [])
            if accounts:
                # Write header
                account_columns = options.get("account_columns", ["name", "type", "currency", "balance"])
                if include_header:
                    writer.writerow(account_columns)
                
                # Write account rows
                for account in accounts:
                    row = self._format_account(account, options)
                    writer.writerow(row)
                
                result.accounts_exported = len(accounts)
            
            result.data = output.getvalue()
            result.completed_at = datetime.utcnow()
            
        except Exception as e:
            result.errors.append(f"Export failed: {str(e)}")
        
        return result
    
    def export_to_file(
        self,
        data: dict[str, Any],
        file_path: str,
        options: dict[str, Any] | None = None
    ) -> ExportResult:
        """Export data directly to a CSV file."""
        if options is None:
            options = {}
        
        result = self.export_data(data, options)
        
        if result.data and isinstance(result.data, str):
            encoding = options.get("encoding", "utf-8")
            
            try:
                with open(file_path, 'w', encoding=encoding) as f:
                    f.write(result.data)
                result.file_path = file_path
            except (IOError, OSError) as e:
                result.errors.append(f"Failed to write file: {e}")
        
        return result
