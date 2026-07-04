"""
QIF import/export plugin for Liftra.

This module provides QIF (Quicken Interchange Format) support for importing
and exporting financial data. QIF is a simple text-based format used by
Quicken and other financial software.
"""

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


class QIFImporter(BaseImporter):
    """
    QIF file importer for financial data.
    
    Supports QIF format commonly used by Quicken and other financial software.
    """
    
    @property
    def format_type(self) -> FormatType:
        return FormatType.QIF
    
    @property
    def name(self) -> str:
        return "QIF Importer"
    
    @property
    def description(self) -> str:
        return "Import financial data from QIF files (Quicken Interchange Format)"
    
    @property
    def file_extensions(self) -> list[str]:
        return [".qif"]
    
    def can_handle_file(self, file_path: str) -> bool:
        """Check if this importer can handle the given file."""
        return file_path.lower().endswith(tuple(self.file_extensions))
    
    def detect_format(self, file_path: str | None = None, content: str | bytes | None = None) -> bool:
        """Detect if the given content is in QIF format."""
        if content is None:
            return False
        
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        
        # QIF files typically start with a version line and have specific patterns
        lines = content.strip().split('\n')
        if not lines:
            return False
        
        # Check for QIF version header
        first_line = lines[0].strip().upper()
        if first_line.startswith('V') and len(first_line) > 1:
            return True
        
        # Check for QIF field codes
        qif_fields = ['!Type:', '!Account', '^', 'D', 'T', 'M', 'P', 'A', 'C', 'N', 'S']
        for line in lines[:10]:  # Check first 10 lines
            if any(field in line for field in qif_fields):
                return True
        
        return False
    
    def get_options(self) -> dict[str, Any]:
        """Get configuration options for this importer."""
        return {
            "encoding": {
                "default": "utf-8",
                "description": "File encoding",
                "type": "string",
                "choices": ["utf-8", "latin-1", "ascii", "cp1252"],
            },
            "date_format": {
                "default": "%d/%m/%Y",
                "description": "Date format for parsing QIF dates",
                "type": "string",
            },
            "account_filter": {
                "default": None,
                "description": "Filter to specific account name (None = all accounts)",
                "type": "string",
            },
        }
    
    def _parse_qif_date(self, date_str: str, date_format: str) -> str | None:
        """Parse QIF date string to ISO format (YYYY-MM-DD)."""
        if not date_str:
            return None
        
        # QIF dates can be in various formats
        formats = [
            date_format,
            "%d/%m/%Y",
            "%m/%d/%Y", 
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%Y-%m-%d",
            "%d/%m/%y",
            "%m/%d/%y",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        return None
    
    def _parse_qif_amount(self, amount_str: str) -> str | None:
        """Parse QIF amount string."""
        if not amount_str:
            return None
        
        try:
            # Remove commas and other formatting
            amount_clean = amount_str.replace(',', '')
            amount = float(amount_clean)
            return str(amount)
        except ValueError:
            return None
    
    def _parse_qif_section(self, lines: list[str], start_idx: int, options: dict[str, Any]) -> tuple[ImportedAccount | None, list[ImportedTransaction], int]:
        """
        Parse a QIF section (account or category).
        
        Args:
            lines: All lines from the QIF file
            start_idx: Starting line index
            options: Import options
            
        Returns:
            Tuple of (account, transactions, end_index)
        """
        account = None
        transactions: list[ImportedTransaction] = []
        current_transaction = None
        date_format = options.get("date_format", "%d/%m/%Y")
        
        i = start_idx
        while i < len(lines):
            line = lines[i].strip()
            
            # End of section
            if line == '^':
                if current_transaction:
                    transactions.append(current_transaction)
                    current_transaction = None
                return account, transactions, i + 1
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check for section header
            if line.startswith('!Type:'):
                section_type = line[6:].strip()
                if section_type == 'Bank':
                    account = ImportedAccount()
                    account.account_type = 'bank'
                elif section_type == 'Cash':
                    account = ImportedAccount()
                    account.account_type = 'cash'
                elif section_type == 'CCard':
                    account = ImportedAccount()
                    account.account_type = 'credit_card'
                elif section_type == 'Invst':
                    account = ImportedAccount()
                    account.account_type = 'investment'
                elif section_type == 'Oth A':
                    account = ImportedAccount()
                    account.account_type = 'other'
                elif section_type == 'Oth L':
                    account = ImportedAccount()
                    account.account_type = 'loan'
                i += 1
                continue
            
            # Check for account name
            if line.startswith('!Account') and account:
                account.name = line[8:].strip()
                i += 1
                continue
            
            # Check for description
            if line.startswith('!Clear:Auto') and account:
                # This indicates auto-clearing
                i += 1
                continue
            
            # Parse transaction fields
            if line.startswith('D'):  # Date
                if current_transaction is None:
                    current_transaction = ImportedTransaction()
                    current_transaction.source_format = self.format_type
                date_str = line[1:].strip()
                current_transaction.date = self._parse_qif_date(date_str, date_format)
            elif line.startswith('T'):  # Amount
                if current_transaction is None:
                    current_transaction = ImportedTransaction()
                    current_transaction.source_format = self.format_type
                amount_str = line[1:].strip()
                current_transaction.amount = self._parse_qif_amount(amount_str)
            elif line.startswith('M'):  # Memo/Description
                if current_transaction is None:
                    current_transaction = ImportedTransaction()
                    current_transaction.source_format = self.format_type
                current_transaction.description = line[1:].strip()
            elif line.startswith('P'):  # Payee
                if current_transaction is None:
                    current_transaction = ImportedTransaction()
                    current_transaction.source_format = self.format_type
                current_transaction.payee = line[1:].strip()
            elif line.startswith('N'):  # Check number/Reference
                if current_transaction is None:
                    current_transaction = ImportedTransaction()
                    current_transaction.source_format = self.format_type
                current_transaction.reference = line[1:].strip()
            elif line.startswith('C'):  # Category
                if current_transaction is None:
                    current_transaction = ImportedTransaction()
                    current_transaction.source_format = self.format_type
                current_transaction.category = line[1:].strip()
            elif line.startswith('S'):  # Split category
                # Handle split transactions (simplified for now)
                if current_transaction and current_transaction.category:
                    current_transaction.category += "/" + line[1:].strip()
            elif line.startswith('E'):  # End of split
                pass
            elif line.startswith('L'):  # Address (multi-line)
                # Skip address lines for now
                pass
            
            i += 1
        
        # Don't forget the last transaction
        if current_transaction:
            transactions.append(current_transaction)
        
        return account, transactions, i
    
    def _parse_qif_file(self, content: str, options: dict[str, Any] | None = None) -> ImportResult:
        """Parse QIF content and extract transactions."""
        if options is None:
            options = {}
        
        result = ImportResult(
            format_type=self.format_type,
            source_file=options.get("source_file")
        )
        
        try:
            lines = content.split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines
                if not line:
                    i += 1
                    continue
                
                # Check for section start
                if line.startswith('!Type:') or line.startswith('!Account'):
                    account, transactions, end_idx = self._parse_qif_section(lines, i, options)
                    
                    if account:
                        result.accounts.append(account)
                    result.transactions.extend(transactions)
                    i = end_idx
                else:
                    i += 1
            
            # Set defaults for transactions
            for transaction in result.transactions:
                if not transaction.currency_code:
                    transaction.currency_code = "GBP"
                if not transaction.transaction_type:
                    # Determine type from amount
                    if transaction.amount:
                        try:
                            amount = float(transaction.amount)
                            transaction.transaction_type = "credit" if amount > 0 else "debit"
                        except ValueError:
                            transaction.transaction_type = "unknown"
                    else:
                        transaction.transaction_type = "unknown"
            
            result.completed_at = datetime.utcnow()
            
        except Exception as e:
            result.errors.append(f"Import failed: {str(e)}")
        
        return result
    
    def import_file(
        self, 
        file_path: str, 
        options: dict[str, Any] | None = None,
        preview_only: bool = False,
        limit: int | None = None
    ) -> ImportResult:
        """Import data from a QIF file."""
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
        """Import data from a QIF string."""
        if isinstance(content, bytes):
            encoding = "utf-8"
            if options and "encoding" in options:
                encoding = options["encoding"]
            content = content.decode(encoding, errors='ignore')
        
        if options is None:
            options = {}
        
        return self._parse_qif_file(content, options)


class QIFExporter(BaseExporter):
    """
    QIF file exporter for financial data.
    
    Exports accounts and transactions to QIF format.
    """
    
    @property
    def format_type(self) -> FormatType:
        return FormatType.QIF
    
    @property
    def name(self) -> str:
        return "QIF Exporter"
    
    @property
    def description(self) -> str:
        return "Export financial data to QIF format (Quicken Interchange Format)"
    
    @property
    def file_extensions(self) -> list[str]:
        return [".qif"]
    
    def get_options(self) -> dict[str, Any]:
        """Get configuration options for this exporter."""
        return {
            "encoding": {
                "default": "utf-8",
                "description": "File encoding",
                "type": "string",
                "choices": ["utf-8", "latin-1", "ascii"],
            },
            "date_format": {
                "default": "%d/%m/%Y",
                "description": "Date format for QIF output",
                "type": "string",
            },
            "account_type": {
                "default": "Bank",
                "description": "QIF account type",
                "type": "string",
                "choices": ["Bank", "Cash", "CCard", "Invst", "Oth A", "Oth L"],
            },
            "include_header": {
                "default": True,
                "description": "Include QIF header information",
                "type": "boolean",
            },
        }
    
    def _format_qif_date(self, date_str: str | None, date_format: str) -> str:
        """Format date for QIF output."""
        if not date_str:
            return datetime.utcnow().strftime(date_format)
        
        try:
            if len(date_str) == 10:  # YYYY-MM-DD
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime(date_format)
            return date_str
        except ValueError:
            return datetime.utcnow().strftime(date_format)
    
    def _format_qif_amount(self, amount: str | float | None) -> str:
        """Format amount for QIF (negative amounts are fine as-is)."""
        if amount is None:
            return "0.00"
        
        try:
            amount_float = float(amount)
            return f"{amount_float:.2f}"
        except (ValueError, TypeError):
            return "0.00"
    
    def export_data(
        self,
        data: dict[str, Any],
        options: dict[str, Any] | None = None
    ) -> ExportResult:
        """Export data to QIF format."""
        if options is None:
            options = {}
        
        result = ExportResult(
            format_type=self.format_type,
            started_at=datetime.utcnow()
        )
        
        try:
            date_format = options.get("date_format", "%d/%m/%Y")
            account_type = options.get("account_type", "Bank")
            include_header = options.get("include_header", True)
            
            qif_lines = []
            
            # Add header if requested
            if include_header:
                qif_lines.append(f"!Type:{account_type}")
                qif_lines.append("!Clear:Auto")
                qif_lines.append("!Option:AutoSwitch")
                qif_lines.append("")
            
            # Add transactions
            transactions = data.get("transactions", [])
            for transaction in transactions:
                qif_lines.append("D" + self._format_qif_date(transaction.get("date"), date_format))
                qif_lines.append("T" + self._format_qif_amount(transaction.get("amount")))
                
                payee = transaction.get("payee", "")
                if payee:
                    qif_lines.append("P" + payee)
                
                description = transaction.get("description", "")
                if description:
                    qif_lines.append("M" + description)
                
                category = transaction.get("category", "")
                if category:
                    qif_lines.append("C" + category)
                
                reference = transaction.get("reference", "")
                if reference:
                    qif_lines.append("N" + reference)
                
                qif_lines.append("^")  # End of transaction
            
            result.data = '\n'.join(qif_lines)
            result.transactions_exported = len(transactions)
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
        """Export data directly to a QIF file."""
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
