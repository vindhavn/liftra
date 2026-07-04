"""
OFX import/export plugin for Liftra.

This module provides OFX (Open Financial Exchange) format support for importing
and exporting financial data. OFX is a standard format used by many banks and
financial institutions.
"""

import os
import re
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


class OFXImporter(BaseImporter):
    """
    OFX file importer for financial data.
    
    Supports OFX 1.0 and 2.0 formats commonly used by banks.
    """
    
    @property
    def format_type(self) -> FormatType:
        return FormatType.OFX
    
    @property
    def name(self) -> str:
        return "OFX Importer"
    
    @property
    def description(self) -> str:
        return "Import financial data from OFX files (bank statement format)"
    
    @property
    def file_extensions(self) -> list[str]:
        return [".ofx", ".qfx"]
    
    def can_handle_file(self, file_path: str) -> bool:
        """Check if this importer can handle the given file."""
        return file_path.lower().endswith(tuple(self.file_extensions))
    
    def detect_format(self, file_path: str | None = None, content: str | bytes | None = None) -> bool:
        """Detect if the given content is in OFX format."""
        if content is None:
            return False
        
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        
        # OFX files typically start with specific headers
        ofx_patterns = [
            r'<OFX>',
            r'<?xml version="1\.0" encoding="UTF-8"?>',
            r'<?OFX',
            r'<SIGNONMSGSRSV1>',
            r'<BANKMSGSRSV1>',
            r'<CREDITCARDMSGSRSV1>',
        ]
        
        content_upper = content.upper()
        for pattern in ofx_patterns:
            if re.search(pattern, content_upper, re.IGNORECASE):
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
            "parse_dates": {
                "default": True,
                "description": "Parse OFX date strings to ISO format",
                "type": "boolean",
            },
            "include_pending": {
                "default": True,
                "description": "Include pending transactions",
                "type": "boolean",
            },
            "account_filter": {
                "default": None,
                "description": "Filter to specific account number (None = all accounts)",
                "type": "string",
            },
        }
    
    def _parse_ofx_date(self, date_str: str) -> str | None:
        """Parse OFX date string to ISO format (YYYY-MM-DD)."""
        if not date_str:
            return None
        
        # OFX date format: YYYYMMDDHHMMSS[.SSS[Zone]]
        try:
            # Remove timezone info if present
            date_clean = date_str.split('[')[0].strip()
            
            if len(date_clean) >= 8:
                year = date_clean[:4]
                month = date_clean[4:6]
                day = date_clean[6:8]
                return f"{year}-{month}-{day}"
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _parse_ofx_amount(self, amount_str: str) -> str | None:
        """Parse OFX amount string (which may have parentheses for negative)."""
        if not amount_str:
            return None
        
        try:
            # Remove parentheses and other formatting
            amount_clean = amount_str.replace('(', '').replace(')', '').replace(',', '')
            amount = float(amount_clean)
            return str(amount)
        except ValueError:
            return None
    
    def _extract_xml_content(self, content: str) -> str:
        """Extract XML content from OFX file (remove SGML headers if present)."""
        # Some OFX files have SGML headers before the XML
        xml_start = content.find('<OFX>')
        if xml_start != -1:
            return content[xml_start:]
        
        # Try to find any XML start
        xml_start = content.find('<?xml')
        if xml_start != -1:
            return content[xml_start:]
        
        return content
    
    def _parse_ofx_file(self, content: str, options: dict[str, Any] | None = None) -> ImportResult:
        """Parse OFX XML content and extract transactions."""
        if options is None:
            options = {}
        
        result = ImportResult(
            format_type=self.format_type,
            source_file=options.get("source_file")
        )
        
        try:
            # Extract XML content
            xml_content = self._extract_xml_content(content)
            
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Find all STMTTRN (statement transaction) elements
            stmttrn_elements = root.findall('.//STMTTRN')
            
            for stmttrn in stmttrn_elements:
                transaction = ImportedTransaction()
                transaction.source_format = self.format_type
                
                # Extract transaction data
                trntype = stmttrn.find('TRNTYPE')
                if trntype is not None and trntype.text:
                    transaction.transaction_type = trntype.text.lower()
                
                dtposted = stmttrn.find('DTPOSTED')
                if dtposted is not None and dtposted.text:
                    transaction.date = self._parse_ofx_date(dtposted.text)
                
                trnamt = stmttrn.find('TRNAMT')
                if trnamt is not None and trnamt.text:
                    transaction.amount = self._parse_ofx_amount(trnamt.text)
                
                name = stmttrn.find('NAME')
                if name is not None and name.text:
                    transaction.payee = unescape(name.text)
                
                memo = stmttrn.find('MEMO')
                if memo is not None and memo.text:
                    transaction.description = unescape(memo.text)
                
                # Try to get currency from the account
                curdef = stmttrn.find('CURDEF')
                if curdef is not None and curdef.text:
                    transaction.currency_code = curdef.text.upper()
                
                # Get reference/check number
                checknum = stmttrn.find('CHECKNUM')
                if checknum is not None and checknum.text:
                    transaction.reference = checknum.text
                
                # Get fitid (unique transaction ID)
                fitid = stmttrn.find('FITID')
                if fitid is not None and fitid.text:
                    transaction.reference = fitid.text
                
                # Set defaults
                if not transaction.currency_code:
                    transaction.currency_code = "GBP"
                if not transaction.transaction_type:
                    transaction.transaction_type = "unknown"
                
                result.transactions.append(transaction)
            
            # Extract account information
            acctfrom_elements = root.findall('.//ACCTFROM')
            for acctfrom in acctfrom_elements:
                account = ImportedAccount()
                account.source_format = self.format_type
                
                acctid = acctfrom.find('ACCTID')
                if acctid is not None and acctid.text:
                    account.account_number = acctid.text
                
                accttype = acctfrom.find('ACCTTYPE')
                if accttype is not None and accttype.text:
                    account.account_type = accttype.text.lower()
                
                # Try to get account name from bank
                bankid = acctfrom.find('BANKID')
                if bankid is not None and bankid.text:
                    account.name = bankid.text
                
                result.accounts.append(account)
            
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
        """Import data from an OFX file."""
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
        """Import data from an OFX string."""
        if isinstance(content, bytes):
            encoding = "utf-8"
            if options and "encoding" in options:
                encoding = options["encoding"]
            content = content.decode(encoding, errors='ignore')
        
        if options is None:
            options = {}
        
        return self._parse_ofx_file(content, options)


class OFXExporter(BaseExporter):
    """
    OFX file exporter for financial data.
    
    Exports accounts and transactions to OFX format.
    """
    
    @property
    def format_type(self) -> FormatType:
        return FormatType.OFX
    
    @property
    def name(self) -> str:
        return "OFX Exporter"
    
    @property
    def description(self) -> str:
        return "Export financial data to OFX format"
    
    @property
    def file_extensions(self) -> list[str]:
        return [".ofx"]
    
    def get_options(self) -> dict[str, Any]:
        """Get configuration options for this exporter."""
        return {
            "encoding": {
                "default": "utf-8",
                "description": "File encoding",
                "type": "string",
                "choices": ["utf-8", "latin-1", "ascii"],
            },
            "bank_id": {
                "default": "LIFTR",
                "description": "Bank ID for OFX file",
                "type": "string",
            },
            "org": {
                "default": "Liftra",
                "description": "Organization name",
                "type": "string",
            },
            "fid": {
                "default": "LIFTR",
                "description": "Financial Institution ID",
                "type": "string",
            },
        }
    
    def _format_ofx_date(self, date_str: str | None) -> str:
        """Format date for OFX (YYYYMMDDHHMMSS)."""
        if not date_str:
            return datetime.utcnow().strftime("%Y%m%d000000")
        
        try:
            if len(date_str) == 10:  # YYYY-MM-DD
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%Y%m%d000000")
            return date_str
        except ValueError:
            return datetime.utcnow().strftime("%Y%m%d000000")
    
    def _format_ofx_amount(self, amount: str | float | None) -> str:
        """Format amount for OFX (negative amounts in parentheses)."""
        if amount is None:
            return "0.00"
        
        try:
            amount_float = float(amount)
            if amount_float < 0:
                return f"({abs(amount_float):.2f})"
            return f"{amount_float:.2f}"
        except (ValueError, TypeError):
            return "0.00"
    
    def export_data(
        self,
        data: dict[str, Any],
        options: dict[str, Any] | None = None
    ) -> ExportResult:
        """Export data to OFX format."""
        if options is None:
            options = {}
        
        result = ExportResult(
            format_type=self.format_type,
            started_at=datetime.utcnow()
        )
        
        try:
            bank_id = options.get("bank_id", "LIFTR")
            org = options.get("org", "Liftra")
            fid = options.get("fid", "LIFTR")
            
            # Build OFX XML
            ofx_lines = []
            ofx_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
            ofx_lines.append('<?OFX VERSION="211"?>')
            ofx_lines.append(f'<OFX>')
            ofx_lines.append(f'  <SIGNONMSGSRSV1>')
            ofx_lines.append(f'    <SONRS>')
            ofx_lines.append(f'      <STATUS>')
            ofx_lines.append(f'        <CODE>0</CODE>')
            ofx_lines.append(f'        <SEVERITY>INFO</SEVERITY>')
            ofx_lines.append(f'      </STATUS>')
            ofx_lines.append(f'      <DTSERVER>{self._format_ofx_date(None)}</DTSERVER>')
            ofx_lines.append(f'      <LANGUAGE>ENG</LANGUAGE>')
            ofx_lines.append(f'      <FI>')
            ofx_lines.append(f'        <ORG>{escape(org)}</ORG>')
            ofx_lines.append(f'        <FID>{escape(fid)}</FID>')
            ofx_lines.append(f'      </FI>')
            ofx_lines.append(f'    </SONRS>')
            ofx_lines.append(f'  </SIGNONMSGSRSV1>')
            
            # Add bank message
            ofx_lines.append(f'  <BANKMSGSRSV1>')
            ofx_lines.append(f'    <STMTTRNRS>')
            ofx_lines.append(f'      <TRNUID>1</TRNUID>')
            ofx_lines.append(f'      <STATUS>')
            ofx_lines.append(f'        <CODE>0</CODE>')
            ofx_lines.append(f'        <SEVERITY>INFO</SEVERITY>')
            ofx_lines.append(f'      </STATUS>')
            ofx_lines.append(f'      <STMTRS>')
            ofx_lines.append(f'        <CURDEF>GBP</CURDEF>')
            ofx_lines.append(f'        <BANKACCTFROM>')
            ofx_lines.append(f'          <BANKID>{escape(bank_id)}</BANKID>')
            ofx_lines.append(f'          <ACCTID>ACCOUNT1</ACCTID>')
            ofx_lines.append(f'          <ACCTTYPE>CHECKING</ACCTTYPE>')
            ofx_lines.append(f'        </BANKACCTFROM>')
            ofx_lines.append(f'        <BANKTRANLIST>')
            
            # Add transactions
            transactions = data.get("transactions", [])
            for i, transaction in enumerate(transactions):
                ofx_lines.append(f'          <STMTTRN>')
                ofx_lines.append(f'            <TRNTYPE>{transaction.get("type", "DEBIT").upper()}</TRNTYPE>')
                ofx_lines.append(f'            <DTPOSTED>{self._format_ofx_date(transaction.get("date"))}</DTPOSTED>')
                ofx_lines.append(f'            <TRNAMT>{self._format_ofx_amount(transaction.get("amount"))}</TRNAMT>')
                ofx_lines.append(f'            <FITID>{i+1}</FITID>')
                
                name = transaction.get("payee", "")
                if name:
                    ofx_lines.append(f'            <NAME>{escape(name)}</NAME>')
                
                memo = transaction.get("description", "")
                if memo:
                    ofx_lines.append(f'            <MEMO>{escape(memo)}</MEMO>')
                
                ofx_lines.append(f'          </STMTTRN>')
            
            ofx_lines.append(f'        </BANKTRANLIST>')
            ofx_lines.append(f'      </STMTRS>')
            ofx_lines.append(f'    </STMTTRNRS>')
            ofx_lines.append(f'  </BANKMSGSRSV1>')
            ofx_lines.append(f'</OFX>')
            
            result.data = '\n'.join(ofx_lines)
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
        """Export data directly to an OFX file."""
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
