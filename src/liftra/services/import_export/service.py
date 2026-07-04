"""
Import/Export service for Liftra.

This module provides high-level services for importing and exporting
financial data, connecting the plugin system with the storage layer.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from liftra.core.models import Account, Transaction, AccountType
from liftra.core.models.transaction import TransactionType
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
from liftra.plugins.manager import PluginManager
from liftra.storage.backends.base import StorageBackend


class ImportExportService:
    """
    Service for importing and exporting financial data.
    
    This service provides a high-level interface for:
    - Importing data from various file formats
    - Exporting data to various file formats
    - Converting between formats
    - Previewing import data
    """
    
    def __init__(self, storage_backend: StorageBackend | None = None) -> None:
        """
        Initialize the import/export service.
        
        Args:
            storage_backend: Optional storage backend for saving imported data
        """
        self._storage_backend = storage_backend
        self._plugin_manager = PluginManager()
        self._plugin_manager.discover_and_load_plugins()
    
    @property
    def plugin_manager(self) -> PluginManager:
        """Get the plugin manager."""
        return self._plugin_manager
    
    @property
    def supported_formats(self) -> list[FormatType]:
        """Get all supported format types."""
        return self._plugin_manager.get_supported_formats()
    
    def get_importer(self, format_type: FormatType) -> BaseImporter | None:
        """Get an importer for the specified format."""
        return self._plugin_manager.get_importer(format_type)
    
    def get_exporter(self, format_type: FormatType) -> BaseExporter | None:
        """Get an exporter for the specified format."""
        return self._plugin_manager.get_exporter(format_type)
    
    def detect_format(self, file_path: str | None = None, content: str | bytes | None = None) -> FormatType | None:
        """Detect the format of a file or content."""
        if file_path:
            importer = self._plugin_manager.get_importer_for_file(file_path)
            if importer:
                return importer.format_type
        
        if content:
            return self._plugin_manager.detect_format(content)
        
        return None
    
    def _convert_imported_transaction(self, imported: ImportedTransaction) -> dict[str, Any]:
        """Convert an ImportedTransaction to a dictionary for storage."""
        transaction_data = {
            "description": imported.description or "",
            "amount": imported.amount or "0.00",
            "currency_code": imported.currency_code or "GBP",
            "date": imported.date or datetime.utcnow().strftime("%Y-%m-%d"),
        }
        
        # Map transaction type
        if imported.transaction_type:
            type_mapping = {
                "debit": TransactionType.EXPENSE,
                "credit": TransactionType.INCOME,
                "transfer": TransactionType.TRANSFER,
                "payment": TransactionType.EXPENSE,
                "deposit": TransactionType.INCOME,
                "withdrawal": TransactionType.EXPENSE,
            }
            transaction_data["transaction_type"] = type_mapping.get(
                imported.transaction_type.lower(), 
                TransactionType.EXPENSE
            )
        else:
            # Determine from amount
            try:
                amount = float(imported.amount or "0.00")
                transaction_data["transaction_type"] = (
                    TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE
                )
            except ValueError:
                transaction_data["transaction_type"] = TransactionType.EXPENSE
        
        # Add optional fields
        if imported.payee:
            transaction_data["payee_name"] = imported.payee
        if imported.category:
            transaction_data["category_name"] = imported.category
        if imported.reference:
            transaction_data["reference"] = imported.reference
        if imported.memo:
            transaction_data["notes"] = imported.memo
        if imported.account_name:
            transaction_data["account_name"] = imported.account_name
        
        return transaction_data
    
    def _convert_imported_account(self, imported: ImportedAccount) -> dict[str, Any]:
        """Convert an ImportedAccount to a dictionary for storage."""
        account_data = {
            "name": imported.name or "Unknown Account",
            "currency_code": imported.currency_code or "GBP",
        }
        
        # Map account type
        if imported.account_type:
            type_mapping = {
                "bank": AccountType.BANK,
                "cash": AccountType.CASH,
                "credit_card": AccountType.CREDIT_CARD,
                "savings": AccountType.SAVINGS,
                "investment": AccountType.INVESTMENT,
                "loan": AccountType.LOAN,
                "mortgage": AccountType.MORTGAGE,
            }
            account_data["account_type"] = type_mapping.get(
                imported.account_type.lower(), 
                AccountType.BANK
            )
        else:
            account_data["account_type"] = AccountType.BANK
        
        # Add optional fields
        if imported.account_number:
            account_data["account_number"] = imported.account_number
        if imported.balance:
            account_data["current_balance"] = imported.balance
        
        return account_data
    
    async def import_file(
        self,
        file_path: str,
        options: dict[str, Any] | None = None,
        preview_only: bool = False,
        limit: int | None = None
    ) -> ImportResult:
        """
        Import data from a file.
        
        Args:
            file_path: Path to the file to import
            options: Optional import options
            preview_only: If True, only preview without saving
            limit: Maximum number of transactions to import
            
        Returns:
            ImportResult with imported data and statistics
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Detect format and get importer
        importer = self._plugin_manager.get_importer_for_file(file_path)
        if importer is None:
            raise ImportError(f"No importer found for file: {file_path}")
        
        # Perform import
        result = importer.import_file(file_path, options, preview_only, limit)
        
        if not preview_only and self._storage_backend:
            # Save imported data to storage
            await self._save_imported_data(result)
        
        return result
    
    async def import_string(
        self,
        content: str | bytes,
        format_type: FormatType | None = None,
        options: dict[str, Any] | None = None,
        preview_only: bool = False,
        limit: int | None = None
    ) -> ImportResult:
        """
        Import data from a string.
        
        Args:
            content: String or bytes content to import
            format_type: Optional format type (if None, will be detected)
            options: Optional import options
            preview_only: If True, only preview without saving
            limit: Maximum number of transactions to import
            
        Returns:
            ImportResult with imported data and statistics
        """
        # Detect format if not provided
        if format_type is None:
            format_type = self._plugin_manager.detect_format(content)
            if format_type is None:
                raise ImportError("Could not detect file format")
        
        # Get importer
        importer = self._plugin_manager.get_importer(format_type)
        if importer is None:
            raise ImportError(f"No importer found for format: {format_type}")
        
        # Perform import
        result = importer.import_string(content, options, preview_only, limit)
        
        if not preview_only and self._storage_backend:
            # Save imported data to storage
            await self._save_imported_data(result)
        
        return result
    
    async def _save_imported_data(self, result: ImportResult) -> None:
        """Save imported data to storage."""
        if self._storage_backend is None:
            return
        
        # Save accounts
        for imported_account in result.accounts:
            account_data = self._convert_imported_account(imported_account)
            await self._storage_backend.create("Account", account_data)
        
        # Save transactions
        for imported_transaction in result.transactions:
            transaction_data = self._convert_imported_transaction(imported_transaction)
            await self._storage_backend.create("Transaction", transaction_data)
    
    async def export_data(
        self,
        data: dict[str, Any],
        format_type: FormatType,
        options: dict[str, Any] | None = None
    ) -> ExportResult:
        """
        Export data to a specific format.
        
        Args:
            data: Data to export (accounts, transactions, etc.)
            format_type: The format to export to
            options: Optional export options
            
        Returns:
            ExportResult with exported data
        """
        exporter = self._plugin_manager.get_exporter(format_type)
        if exporter is None:
            raise ExportError(f"No exporter found for format: {format_type}")
        
        return exporter.export_data(data, options)
    
    async def export_to_file(
        self,
        data: dict[str, Any],
        file_path: str,
        format_type: FormatType | None = None,
        options: dict[str, Any] | None = None
    ) -> ExportResult:
        """
        Export data directly to a file.
        
        Args:
            data: Data to export
            file_path: Path to the output file
            format_type: Optional format type (if None, detected from file extension)
            options: Optional export options
            
        Returns:
            ExportResult with export statistics
        """
        # Detect format from file extension if not provided
        if format_type is None:
            exporter = self._plugin_manager.get_exporter_by_extension(file_path)
            if exporter is None:
                raise ExportError(f"Could not determine format for file: {file_path}")
            format_type = exporter.format_type
        
        exporter = self._plugin_manager.get_exporter(format_type)
        if exporter is None:
            raise ExportError(f"No exporter found for format: {format_type}")
        
        return exporter.export_to_file(data, file_path, options)
    
    async def convert_file(
        self,
        input_path: str,
        output_path: str,
        options: dict[str, Any] | None = None
    ) -> ExportResult:
        """
        Convert a file from one format to another.
        
        Args:
            input_path: Path to the input file
            output_path: Path to the output file
            options: Optional conversion options
            
        Returns:
            ExportResult with conversion statistics
        """
        # Import the input file
        import_result = await self.import_file(input_path, options, preview_only=True)
        
        if not import_result.success:
            raise ImportError(f"Failed to import input file: {import_result.errors}")
        
        # Prepare data for export
        data = {
            "accounts": [
                {
                    "name": acc.name,
                    "type": acc.account_type,
                    "currency": acc.currency_code,
                    "balance": acc.balance
                }
                for acc in import_result.accounts
            ],
            "transactions": [
                {
                    "date": txn.date,
                    "description": txn.description,
                    "payee": txn.payee,
                    "category": txn.category,
                    "amount": txn.amount,
                    "currency": txn.currency_code,
                    "type": txn.transaction_type,
                    "reference": txn.reference
                }
                for txn in import_result.transactions
            ]
        }
        
        # Export to output format
        return await self.export_to_file(data, output_path, options=options)
    
    async def preview_import(
        self,
        file_path: str,
        options: dict[str, Any] | None = None,
        limit: int = 10
    ) -> ImportResult:
        """
        Preview data that would be imported from a file.
        
        Args:
            file_path: Path to the file to preview
            options: Optional import options
            limit: Maximum number of transactions to preview
            
        Returns:
            ImportResult with preview data
        """
        return await self.import_file(file_path, options, preview_only=True, limit=limit)
    
    def get_format_info(self, format_type: FormatType) -> dict[str, Any]:
        """
        Get information about a specific format.
        
        Args:
            format_type: The format to get information about
            
        Returns:
            Dictionary with format information
        """
        importer = self._plugin_manager.get_importer(format_type)
        exporter = self._plugin_manager.get_exporter(format_type)
        
        info = {
            "format_type": format_type.value,
            "name": format_type.value.upper(),
            "can_import": importer is not None,
            "can_export": exporter is not None,
            "extensions": [],
            "description": "",
        }
        
        if importer:
            info["name"] = importer.name
            info["description"] = importer.description
            info["extensions"] = importer.file_extensions
            info["importer_options"] = importer.get_options()
        
        if exporter:
            if not info["name"]:
                info["name"] = exporter.name
            if not info["description"]:
                info["description"] = exporter.description
            if not info["extensions"]:
                info["extensions"] = exporter.file_extensions
            info["exporter_options"] = exporter.get_options()
        
        return info
    
    def get_all_format_info(self) -> list[dict[str, Any]]:
        """Get information about all supported formats."""
        formats = self.supported_formats
        return [self.get_format_info(fmt) for fmt in formats]
