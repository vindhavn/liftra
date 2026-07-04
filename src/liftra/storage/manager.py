"""
Storage manager for Liftra.

This module provides a high-level interface for managing storage backends
and handling the current storage configuration.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from liftra.core.exceptions import StorageError, ConfigurationError
from liftra.storage.backends.base import StorageBackend, Query, QueryResult
from liftra.storage.backends.sqlite import SQLiteBackend


class StorageManager:
    """
    Manages storage backends and provides a unified interface.
    
    The StorageManager handles:
    - Creating and managing storage backends
    - Switching between different backends
    - Providing a consistent API for data access
    - Managing encryption and security
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Initialize the StorageManager.
        
        Args:
            config: Configuration dictionary with storage settings
        """
        self.config = config or {}
        self._backends: dict[str, StorageBackend] = {}
        self._current_backend: StorageBackend | None = None
        self._current_backend_name: str | None = None
        self._lock = asyncio.Lock()

    async def initialize(self, config: dict[str, Any] | None = None) -> None:
        """
        Initialize the storage manager with configuration.
        
        Args:
            config: Configuration dictionary with storage settings
        """
        if config:
            self.config = config
        
        # Determine storage type from config
        storage_type = self.config.get("storage_type", "sqlite")
        
        # Create the appropriate backend
        backend = self._create_backend(storage_type, self.config)
        self._backends[storage_type] = backend
        self._current_backend = backend
        self._current_backend_name = storage_type
        
        # Connect to the backend
        await self._current_backend.connect()

    def _create_backend(self, backend_type: str, config: dict[str, Any]) -> StorageBackend:
        """Create a storage backend of the specified type."""
        if backend_type == "sqlite":
            return SQLiteBackend(config)
        elif backend_type == "cloud":
            from liftra.storage.backends.cloud import CloudStorageBackend
            return CloudStorageBackend(config)
        elif backend_type == "server":
            from liftra.storage.backends.server import ServerBackend
            return ServerBackend(config)
        else:
            raise ConfigurationError(f"Unknown storage backend type: {backend_type}")

    @property
    def current_backend(self) -> StorageBackend:
        """Get the current storage backend."""
        if self._current_backend is None:
            raise StorageError("No storage backend initialized")
        return self._current_backend

    @property
    def current_backend_name(self) -> str | None:
        """Get the name of the current storage backend."""
        return self._current_backend_name

    async def switch_backend(self, backend_name: str) -> None:
        """
        Switch to a different storage backend.
        
        Args:
            backend_name: Name of the backend to switch to
        """
        async with self._lock:
            if backend_name not in self._backends:
                # Create the backend if it doesn't exist
                backend_config = self.config.get(f"{backend_name}_config", {})
                self._backends[backend_name] = self._create_backend(backend_name, backend_config)
            
            # Disconnect from current backend
            if self._current_backend:
                await self._current_backend.disconnect()
            
            # Switch to new backend
            self._current_backend = self._backends[backend_name]
            self._current_backend_name = backend_name
            
            # Connect to new backend
            await self._current_backend.connect()

    async def get_backend(self, backend_name: str) -> StorageBackend:
        """
        Get a specific storage backend.
        
        Args:
            backend_name: Name of the backend to get
            
        Returns:
            The requested storage backend
        """
        if backend_name not in self._backends:
            backend_config = self.config.get(f"{backend_name}_config", {})
            self._backends[backend_name] = self._create_backend(backend_name, backend_config)
        
        return self._backends[backend_name]

    async def close(self) -> None:
        """Close all storage backends."""
        async with self._lock:
            for backend in self._backends.values():
                try:
                    await backend.disconnect()
                except Exception:
                    pass
            self._backends.clear()
            self._current_backend = None
            self._current_backend_name = None

    # Delegate storage operations to the current backend
    
    async def connect(self) -> None:
        """Connect to the current storage backend."""
        await self.current_backend.connect()

    async def disconnect(self) -> None:
        """Disconnect from the current storage backend."""
        await self.current_backend.disconnect()

    async def is_connected(self) -> bool:
        """Check if the current storage backend is connected."""
        return await self.current_backend.is_connected()

    async def get(self, entity_type: str, entity_id: Any) -> dict[str, Any]:
        """Get a single entity by ID."""
        return await self.current_backend.get(entity_type, entity_id)

    async def list(
        self, entity_type: str, query: Query | None = None
    ) -> QueryResult[dict[str, Any]]:
        """List entities of a given type."""
        return await self.current_backend.list(entity_type, query)

    async def create(self, entity_type: str, data: dict[str, Any]) -> Any:
        """Create a new entity."""
        return await self.current_backend.create(entity_type, data)

    async def update(self, entity_type: str, entity_id: Any, data: dict[str, Any]) -> None:
        """Update an existing entity."""
        await self.current_backend.update(entity_type, entity_id, data)

    async def delete(self, entity_type: str, entity_id: Any) -> None:
        """Delete an entity."""
        await self.current_backend.delete(entity_type, entity_id)

    async def query(self, query: Query) -> QueryResult[dict[str, Any]]:
        """Execute a custom query."""
        return await self.current_backend.query(query)

    async def count(self, entity_type: str, filters: dict[str, Any] | None = None) -> int:
        """Count entities of a given type."""
        return await self.current_backend.count(entity_type, filters)

    async def exists(self, entity_type: str, entity_id: Any) -> bool:
        """Check if an entity exists."""
        return await self.current_backend.exists(entity_type, entity_id)

    async def backup(
        self, destination: str, backup_name: str | None = None
    ) -> str:
        """Create a backup of the current storage."""
        return await self.current_backend.backup(destination, backup_name)

    async def restore(self, source: str) -> None:
        """Restore current storage from a backup."""
        await self.current_backend.restore(source)

    async def get_schema_version(self) -> str:
        """Get the current schema version."""
        return await self.current_backend.get_schema_version()

    async def migrate(self, target_version: str | None = None) -> str:
        """Migrate the current storage schema."""
        return await self.current_backend.migrate(target_version)

    async def get_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        return await self.current_backend.get_stats()

    async def clear(self, entity_type: str | None = None) -> None:
        """Clear all data from current storage."""
        await self.current_backend.clear(entity_type)


# Global storage manager instance
_storage_manager: StorageManager | None = None


async def get_storage_manager(config: dict[str, Any] | None = None) -> StorageManager:
    """
    Get the global storage manager instance.
    
    Args:
        config: Optional configuration to initialize with
        
    Returns:
        The global StorageManager instance
    """
    global _storage_manager
    
    if _storage_manager is None:
        _storage_manager = StorageManager(config)
        if config:
            await _storage_manager.initialize(config)
    
    return _storage_manager


async def close_storage_manager() -> None:
    """Close the global storage manager."""
    global _storage_manager
    
    if _storage_manager is not None:
        await _storage_manager.close()
        _storage_manager = None


@asynccontextmanager
async def storage_context(config: dict[str, Any] | None = None):
    """
    Context manager for storage operations.
    
    Args:
        config: Optional configuration for the storage manager
        
    Yields:
        The storage manager instance
    """
    manager = StorageManager(config)
    if config:
        await manager.initialize(config)
    
    try:
        yield manager
    finally:
        await manager.close()
