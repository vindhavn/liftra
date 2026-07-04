"""
Plugin manager for Liftra.

This module provides the plugin management system for Liftra, allowing
for extensible functionality through plugins.
"""

import importlib
import pkgutil
from typing import Any

from liftra.plugins.importers.base import BaseImporter, BaseExporter, FormatType


class PluginManager:
    """
    Manages plugins for Liftra.
    
    This class provides functionality to:
    - Discover and load plugins
    - Register and manage importers/exporters
    - Handle plugin configuration
    """
    
    def __init__(self) -> None:
        """Initialize the plugin manager."""
        self._importers: dict[FormatType, type[BaseImporter]] = {}
        self._exporters: dict[FormatType, type[BaseExporter]] = {}
        self._loaded_plugins: dict[str, Any] = {}
    
    def register_importer(self, format_type: FormatType, importer_class: type[BaseImporter]) -> None:
        """
        Register an importer for a specific format.
        
        Args:
            format_type: The format type this importer handles
            importer_class: The importer class to register
        """
        self._importers[format_type] = importer_class
    
    def register_exporter(self, format_type: FormatType, exporter_class: type[BaseExporter]) -> None:
        """
        Register an exporter for a specific format.
        
        Args:
            format_type: The format type this exporter handles
            exporter_class: The exporter class to register
        """
        self._exporters[format_type] = exporter_class
    
    def get_importer(self, format_type: FormatType) -> BaseImporter | None:
        """
        Get an importer for the specified format.
        
        Args:
            format_type: The format type to get an importer for
            
        Returns:
            An instance of the importer, or None if not found
        """
        importer_class = self._importers.get(format_type)
        if importer_class:
            return importer_class()
        return None
    
    def get_exporter(self, format_type: FormatType) -> BaseExporter | None:
        """
        Get an exporter for the specified format.
        
        Args:
            format_type: The format type to get an exporter for
            
        Returns:
            An instance of the exporter, or None if not found
        """
        exporter_class = self._exporters.get(format_type)
        if exporter_class:
            return exporter_class()
        return None
    
    def get_importer_by_extension(self, file_path: str) -> BaseImporter | None:
        """
        Get an importer based on file extension.
        
        Args:
            file_path: The file path to check
            
        Returns:
            An instance of the appropriate importer, or None if not found
        """
        for importer_class in self._importers.values():
            importer = importer_class()
            if importer.can_handle_file(file_path):
                return importer
        return None
    
    def get_exporter_by_extension(self, file_path: str) -> BaseExporter | None:
        """
        Get an exporter based on file extension.
        
        Args:
            file_path: The file path to check
            
        Returns:
            An instance of the appropriate exporter, or None if not found
        """
        for exporter_class in self._exporters.values():
            exporter = exporter_class()
            if file_path.lower().endswith(tuple(exporter.file_extensions)):
                return exporter
        return None
    
    def detect_format(self, content: str | bytes) -> FormatType | None:
        """
        Detect the format of the given content.
        
        Args:
            content: The content to analyze
            
        Returns:
            The detected format type, or None if not recognized
        """
        for importer_class in self._importers.values():
            importer = importer_class()
            if importer.detect_format(content=content):
                return importer.format_type
        return None
    
    def get_all_importers(self) -> list[type[BaseImporter]]:
        """Get all registered importer classes."""
        return list(self._importers.values())
    
    def get_all_exporters(self) -> list[type[BaseExporter]]:
        """Get all registered exporter classes."""
        return list(self._exporters.values())
    
    def get_supported_formats(self) -> list[FormatType]:
        """Get all supported format types."""
        formats = set(self._importers.keys())
        formats.update(self._exporters.keys())
        return list(formats)
    
    def load_plugin(self, module_name: str) -> bool:
        """
        Load a plugin module.
        
        Args:
            module_name: The module name to load
            
        Returns:
            True if plugin loaded successfully, False otherwise
        """
        try:
            module = importlib.import_module(module_name)
            self._loaded_plugins[module_name] = module
            
            # Auto-register importers and exporters if they exist
            if hasattr(module, 'register_plugins'):
                module.register_plugins(self)
            
            return True
        except ImportError:
            return False
    
    def load_plugins_from_package(self, package_name: str) -> int:
        """
        Load all plugins from a package.
        
        Args:
            package_name: The package name to load plugins from
            
        Returns:
            Number of plugins loaded successfully
        """
        count = 0
        try:
            package = importlib.import_module(package_name)
            
            # Find all modules in the package
            for _, module_name, _ in pkgutil.iter_modules(package.__path__):
                full_name = f"{package_name}.{module_name}"
                if self.load_plugin(full_name):
                    count += 1
                    
        except ImportError:
            pass
            
        return count
    
    def discover_and_load_plugins(self) -> int:
        """
        Discover and load all available plugins.
        
        Returns:
            Number of plugins loaded
        """
        count = 0
        
        # Load built-in importers
        try:
            from liftra.plugins.importers import (
                CSVImporter, CSVExporter,
                OFXImporter, OFXExporter,
                QIFImporter, QIFExporter,
                HomeBankImporter, HomeBankExporter
            )
            
            # Register CSV
            self.register_importer(FormatType.CSV, CSVImporter)
            self.register_exporter(FormatType.CSV, CSVExporter)
            
            # Register OFX
            self.register_importer(FormatType.OFX, OFXImporter)
            self.register_exporter(FormatType.OFX, OFXExporter)
            
            # Register QIF
            self.register_importer(FormatType.QIF, QIFImporter)
            self.register_exporter(FormatType.QIF, QIFExporter)
            
            # Register HomeBank
            self.register_importer(FormatType.HOMEBANK, HomeBankImporter)
            self.register_exporter(FormatType.HOMEBANK, HomeBankExporter)
            
            count = 8  # 4 formats * 2 (importer + exporter)
            
        except ImportError as e:
            # Plugin import failed, but that's okay
            pass
        
        return count
    
    def get_importer_for_file(self, file_path: str) -> BaseImporter | None:
        """
        Get the appropriate importer for a file based on its extension or content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            An importer instance, or None if no suitable importer found
        """
        # First try by extension
        importer = self.get_importer_by_extension(file_path)
        if importer:
            return importer
        
        # If extension doesn't match, try to read content and detect format
        try:
            with open(file_path, 'rb') as f:
                content = f.read(1024)  # Read first 1KB for detection
            
            format_type = self.detect_format(content)
            if format_type:
                return self.get_importer(format_type)
        except (IOError, OSError):
            pass
        
        return None


# Global plugin manager instance
plugin_manager = PluginManager()
