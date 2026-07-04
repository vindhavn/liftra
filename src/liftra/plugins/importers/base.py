"""
Base classes for import/export plugins.

This module defines the abstract base classes and data structures for
financial data import and export operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from liftra.core.exceptions import PluginError


class ImportError(PluginError):
    """Error that occurs during import operations."""
    pass


class ExportError(PluginError):
    """Error that occurs during export operations."""
    pass


class FormatType(str, Enum):
    """Supported financial data formats."""
    CSV = "csv"
    OFX = "ofx"
    QIF = "qif"
    HOMEBANK = "homebank"


@dataclass
class ImportedTransaction:
    """Represents a transaction imported from an external format."""
    
    # Core transaction data
    description: str | None = None
    amount: str | None = None  # String to preserve precision
    currency_code: str | None = None
    date: str | None = None  # ISO date string
    
    # Additional transaction data
    payee: str | None = None
    category: str | None = None
    reference: str | None = None
    memo: str | None = None
    
    # Transaction type
    transaction_type: str | None = None  # "debit", "credit", "transfer", etc.
    
    # Account information (if available)
    account_name: str | None = None
    account_number: str | None = None
    
    # Status and metadata
    status: str | None = None
    custom_fields: dict[str, Any] = field(default_factory=dict)
    
    # Source information
    source_format: FormatType | None = None
    source_line: int = 0
    source_file: str | None = None


@dataclass
class ImportedAccount:
    """Represents an account imported from an external format."""
    
    name: str | None = None
    account_type: str | None = None
    account_number: str | None = None
    routing_number: str | None = None
    currency_code: str | None = None
    balance: str | None = None
    
    # Source information
    source_format: FormatType | None = None
    source_line: int = 0
    source_file: str | None = None


@dataclass
class ImportResult:
    """Result of an import operation."""
    
    # Imported data
    accounts: list[ImportedAccount] = field(default_factory=list)
    transactions: list[ImportedTransaction] = field(default_factory=list)
    
    # Statistics
    accounts_imported: int = 0
    transactions_imported: int = 0
    duplicates_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    
    # Format information
    format_type: FormatType | None = None
    source_file: str | None = None
    
    def __post_init__(self) -> None:
        if self.completed_at is None:
            self.completed_at = datetime.utcnow()
        
        # Update statistics
        self.accounts_imported = len(self.accounts)
        self.transactions_imported = len(self.transactions)
    
    @property
    def success(self) -> bool:
        """Check if import was successful (no critical errors)."""
        return len(self.errors) == 0
    
    @property
    def duration(self) -> float:
        """Get import duration in seconds."""
        if self.completed_at is None:
            return 0.0
        return (self.completed_at - self.started_at).total_seconds()


@dataclass 
class ExportResult:
    """Result of an export operation."""
    
    # Export data
    data: str | bytes | None = None
    file_path: str | None = None
    
    # Statistics
    accounts_exported: int = 0
    transactions_exported: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    
    # Format information
    format_type: FormatType | None = None
    
    def __post_init__(self) -> None:
        if self.completed_at is None:
            self.completed_at = datetime.utcnow()
    
    @property
    def success(self) -> bool:
        """Check if export was successful (no critical errors)."""
        return len(self.errors) == 0
    
    @property
    def duration(self) -> float:
        """Get export duration in seconds."""
        if self.completed_at is None:
            return 0.0
        return (self.completed_at - self.started_at).total_seconds()


class BaseImporter(ABC):
    """
    Abstract base class for financial data importers.
    
    All importers must implement this interface to provide consistent
    import functionality across different file formats.
    """
    
    @property
    @abstractmethod
    def format_type(self) -> FormatType:
        """Get the format type this importer supports."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the human-readable name of this importer."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get a description of this importer."""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """Get the file extensions this importer supports."""
        pass
    
    @abstractmethod
    def can_handle_file(self, file_path: str) -> bool:
        """
        Check if this importer can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this importer can handle the file
        """
        pass
    
    @abstractmethod
    def detect_format(self, file_path: str | None = None, content: str | bytes | None = None) -> bool:
        """
        Detect if the given content is in this importer's format.
        
        Args:
            file_path: Optional path to the file
            content: Optional content to check
            
        Returns:
            True if the content is in this format
        """
        pass
    
    @abstractmethod
    def get_options(self) -> dict[str, Any]:
        """
        Get the configuration options for this importer.
        
        Returns:
            Dictionary of option names to their default values and metadata
        """
        pass
    
    @abstractmethod
    def import_file(
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
            preview_only: If True, only preview the data without importing
            limit: Maximum number of transactions to import (for preview)
            
        Returns:
            ImportResult containing the imported data and statistics
            
        Raises:
            ImportError: If import fails
            FileNotFoundError: If file doesn't exist
            PermissionError: If file cannot be read
        """
        pass
    
    @abstractmethod
    def import_string(
        self,
        content: str | bytes,
        options: dict[str, Any] | None = None,
        preview_only: bool = False,
        limit: int | None = None
    ) -> ImportResult:
        """
        Import data from a string or bytes content.
        
        Args:
            content: String or bytes content to import
            options: Optional import options
            preview_only: If True, only preview the data without importing
            limit: Maximum number of transactions to import (for preview)
            
        Returns:
            ImportResult containing the imported data and statistics
            
        Raises:
            ImportError: If import fails
        """
        pass


class BaseExporter(ABC):
    """
    Abstract base class for financial data exporters.
    
    All exporters must implement this interface to provide consistent
    export functionality across different file formats.
    """
    
    @property
    @abstractmethod
    def format_type(self) -> FormatType:
        """Get the format type this exporter supports."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the human-readable name of this exporter."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get a description of this exporter."""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """Get the file extensions this exporter supports."""
        pass
    
    @abstractmethod
    def get_options(self) -> dict[str, Any]:
        """
        Get the configuration options for this exporter.
        
        Returns:
            Dictionary of option names to their default values and metadata
        """
        pass
    
    @abstractmethod
    def export_data(
        self,
        data: dict[str, Any],
        options: dict[str, Any] | None = None
    ) -> ExportResult:
        """
        Export data to the target format.
        
        Args:
            data: Dictionary containing data to export
                - accounts: List of account data
                - transactions: List of transaction data
                - metadata: Optional metadata
            options: Optional export options
            
        Returns:
            ExportResult containing the exported data and statistics
            
        Raises:
            ExportError: If export fails
        """
        pass
    
    @abstractmethod
    def export_to_file(
        self,
        data: dict[str, Any],
        file_path: str,
        options: dict[str, Any] | None = None
    ) -> ExportResult:
        """
        Export data directly to a file.
        
        Args:
            data: Dictionary containing data to export
            file_path: Path to the output file
            options: Optional export options
            
        Returns:
            ExportResult containing statistics and file information
            
        Raises:
            ExportError: If export fails
            PermissionError: If file cannot be written
        """
        pass
