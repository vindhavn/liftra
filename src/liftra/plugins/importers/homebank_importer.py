"""
HomeBank import/export plugin for Liftra.

This module provides HomeBank XML format support for importing and exporting
financial data. HomeBank is a popular open-source personal finance software.
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any
from xml.sax.saxutils import escape, unescape

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


class HomeBankImporter(BaseImporter):
    """
    HomeBank XML file importer for financial data.
    
    Supports HomeBank XML format used by the HomeBank personal finance software.
    """
    
    @property
    def format_type(self) -> FormatType:
        return FormatType.HOMEBANK
    
    @property
    def name(self) -> str:
        return "HomeBank Importer"
    
    @property
    def description(self) -> str:
        return "Import financial data from HomeBank XML files"
    
    @property
    def file_extensions(self) -> list[str]:
        return [".xhb", ".xml"]
    
    def can_handle_file(self, file_path: str) -> bool:
        """Check if this importer can handle the given file."""
        return file_path.lower().endswith(tuple(self.file_extensions))
    
    def detect_format(self, file_path: str | None = None, content: str | bytes | None = None) -> bool:
        """Detect if the given content is in HomeBank format."""
        if content is None:
            return False
        
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        
        # HomeBank files typically have specific XML structure
        homebank_patterns = [
            r'<homebank-file',
            r'<prop key="version"',
            r'<prop key="uri"',
            r'<account key="',
            r'<trans key="',
        ]
        
        content_lower = content.lower()
        for pattern in homebank_patterns:
            if pattern.lower() in content_lower:
                return True
        
        return False
    
    def get_options(self) -> dict[str, Any]:
        """Get configuration options for this importer."""
        return {
            "encoding": {
                "default": "utf-8",
                "description": "File encoding",
                "type": "string",
                "choices": ["utf-8", "latin-1", "ascii"],
            },
            "parse_dates": {
                "default": True,
                "description": "Parse HomeBank date strings to ISO format",
                "type": "boolean",
            },
            "account_filter": {
                "default": None,
                "description": "Filter to specific account key (None = all accounts)",
                "type": "string",
            },
        }
    
    def _parse_homebank_date(self, date_str: str) -> str | None:
        """Parse HomeBank date string to ISO format (YYYY-MM-DD)."""
        if not date_str:
            return None
        
        # HomeBank date format: typically YYYY-MM-DD or DD/MM/YYYY
        try:
            # Try YYYY-MM-DD first
            if len(date_str) == 10 and date_str.count('-') == 2:
                return date_str
            
            # Try DD/MM/YYYY
            if len(date_str) == 10 and date_str.count('/') == 2:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                return dt.strftime("%Y-%m-%d")
            
            # Try other formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
        except Exception:
            pass
        
        return None
    
    def _parse_homebank_amount(self, amount_str: str) -> str | None:
        """Parse HomeBank amount string."""
        if not amount_str:
            return None
        
        try:
            # Remove commas and other formatting
            amount_clean = amount_str.replace(',', '')
            amount = float(amount_clean)
            return str(amount)
        except ValueError:
            return None
    
    def _parse_homebank_file(self, content: str, options: dict[str, Any] | None = None) -> ImportResult:
        """Parse HomeBank XML content and extract transactions."""
        if options is None:
            options = {}
        
        result = ImportResult(
            format_type=self.format_type,
            source_file=options.get("source_file")
        )
        
        try:
            # Parse XML
            root = ET.fromstring(content)
            
            # Find all account elements
            account_elements = root.findall('.//account')
            for account_elem in account_elements:
                account = ImportedAccount()
                account.source_format = self.format_type
                
                # Extract account data
                for child in account_elem:
                    if child.tag == 'key':
                        account.account_number = child.text
                    elif child.tag == 'name':
                        account.name = unescape(child.text)
                    elif child.tag == 'type':
                        account.account_type = child.text.lower()
                    elif child.tag == 'currency':
                        account.currency_code = child.text.upper()
                    elif child.tag == 'balance':
                        account.balance = self._parse_homebank_amount(child.text)
                
                result.accounts.append(account)
            
            # Find all transaction elements
            trans_elements = root.findall('.//trans')
            for trans_elem in trans_elements:
                transaction = ImportedTransaction()
                transaction.source_format = self.format_type
                
                # Extract transaction data
                for child in trans_elem:
                    if child.tag == 'date':
                        transaction.date = self._parse_homebank_date(child.text)
                    elif child.tag == 'amount':
                        transaction.amount = self._parse_homebank_amount(child.text)
                    elif child.tag == 'currency':
                        transaction.currency_code = child.text.upper()
                    elif child.tag == 'payee':
                        transaction.payee = unescape(child.text)
                    elif child.tag == 'memo':
                        transaction.description = unescape(child.text)
                    elif child.tag == 'category':
                        transaction.category = unescape(child.text)
                    elif child.tag == 'ref':
                        transaction.reference = child.text
                    elif child.tag == 'type':
                        transaction.transaction_type = child.text.lower()
                    elif child.tag == 'account':
                        transaction.account_name = unescape(child.text)
                
                # Set defaults
                if not transaction.currency_code:
                    transaction.currency_code = "GBP"
                if not transaction.transaction_type:
                    transaction.transaction_type = "unknown"
                
                result.transactions.append(transaction)
            
            result.completed_at = datetime.utcnow()
            
        except ET.ParseError as e:
            result.errors.append(f"XML parsing failed: {str(e)}")
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
        """Import data from a HomeBank file."""
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
        """Import data from a HomeBank string."""
        if isinstance(content, bytes):
            encoding = "utf-8"
            if options and "encoding" in options:
                encoding = options["encoding"]
            content = content.decode(encoding, errors='ignore')
        
        if options is None:
            options = {}
        
        return self._parse_homebank_file(content, options)


class HomeBankExporter(BaseExporter):
    """
    HomeBank XML file exporter for financial data.
    
    Exports accounts and transactions to HomeBank XML format.
    """
    
    @property
    def format_type(self) -> FormatType:
        return FormatType.HOMEBANK
    
    @property
    def name(self) -> str:
        return "HomeBank Exporter"
    
    @property
    def description(self) -> str:
        return "Export financial data to HomeBank XML format"
    
    @property
    def file_extensions(self) -> list[str]:
        return [".xhb", ".xml"]
    
    def get_options(self) -> dict[str, Any]:
        """Get configuration options for this exporter."""
        return {
            "encoding": {
                "default": "utf-8",
                "description": "File encoding",
                "type": "string",
                "choices": ["utf-8", "latin-1", "ascii"],
            },
            "version": {
                "default": "1.0",
                "description": "HomeBank file version",
                "type": "string",
            },
            "currency": {
                "default": "GBP",
                "description": "Default currency",
                "type": "string",
            },
        }
    
    def _format_homebank_date(self, date_str: str | None) -> str:
        """Format date for HomeBank (YYYY-MM-DD)."""
        if not date_str:
            return datetime.utcnow().strftime("%Y-%m-%d")
        
        try:
            if len(date_str) == 10:  # YYYY-MM-DD
                return date_str
            
            dt = datetime.strptime(date_str, "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return datetime.utcnow().strftime("%Y-%m-%d")
    
    def _format_homebank_amount(self, amount: str | float | None) -> str:
        """Format amount for HomeBank."""
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
        """Export data to HomeBank XML format."""
        if options is None:
            options = {}
        
        result = ExportResult(
            format_type=self.format_type,
            started_at=datetime.utcnow()
        )
        
        try:
            version = options.get("version", "1.0")
            currency = options.get("currency", "GBP")
            
            # Build HomeBank XML
            xml_lines = []
            xml_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
            xml_lines.append(f'<homebank-file version="{version}">')
            xml_lines.append('  <prop>')
            xml_lines.append(f'    <prop key="version" value="{version}"/>')
            xml_lines.append(f'    <prop key="uri" value="file:///tmp/liftra.xhb"/>')
            xml_lines.append(f'    <prop key="date-format" value="%Y-%m-%d"/>')
            xml_lines.append(f'    <prop key="currency" value="{currency}"/>')
            xml_lines.append('  </prop>')
            
            # Add accounts
            accounts = data.get("accounts", [])
            for i, account in enumerate(accounts):
                xml_lines.append('  <account key="' + str(i+1) + '">')
                xml_lines.append(f'    <name>' + escape(account.get("name", "Account " + str(i+1))) + '</name>')
                xml_lines.append(f'    <type>' + escape(account.get("type", "bank")) + '</type>')
                xml_lines.append(f'    <currency>' + escape(account.get("currency", currency)) + '</currency>')
                balance = account.get("balance", "0.00")
                xml_lines.append(f'    <balance>' + escape(self._format_homebank_amount(balance)) + '</balance>')
                xml_lines.append('  </account>')
            
            # Add transactions
            transactions = data.get("transactions", [])
            for i, transaction in enumerate(transactions):
                xml_lines.append('  <trans key="' + str(i+1) + '">')
                xml_lines.append(f'    <date>' + escape(self._format_homebank_date(transaction.get("date"))) + '</date>')
                xml_lines.append(f'    <amount>' + escape(self._format_homebank_amount(transaction.get("amount"))) + '</amount>')
                xml_lines.append(f'    <currency>' + escape(transaction.get("currency", currency)) + '</currency>')
                
                payee = transaction.get("payee", "")
                if payee:
                    xml_lines.append(f'    <payee>' + escape(payee) + '</payee>')
                
                description = transaction.get("description", "")
                if description:
                    xml_lines.append(f'    <memo>' + escape(description) + '</memo>')
                
                category = transaction.get("category", "")
                if category:
                    xml_lines.append(f'    <category>' + escape(category) + '</category>')
                
                reference = transaction.get("reference", "")
                if reference:
                    xml_lines.append(f'    <ref>' + escape(reference) + '</ref>')
                
                trans_type = transaction.get("type", "debit")
                xml_lines.append(f'    <type>' + escape(trans_type) + '</type>')
                
                account_name = transaction.get("account", "")
                if account_name:
                    xml_lines.append(f'    <account>' + escape(account_name) + '</account>')
                
                xml_lines.append('  </trans>')
            
            xml_lines.append('</homebank-file>')
            
            result.data = '\n'.join(xml_lines)
            result.transactions_exported = len(transactions)
            result.accounts_exported = len(accounts)
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
        """Export data directly to a HomeBank file."""
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
