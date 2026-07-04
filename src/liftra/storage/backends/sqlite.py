"""
SQLite storage backend for Liftra.

This backend provides local file-based storage using SQLite database.
For now, this is a simplified version that uses sqlite3 directly.
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from liftra.core.exceptions import (
    StorageError,
    NotFoundError,
    DuplicateError,
    ValidationError,
)
from liftra.storage.backends.base import StorageBackend, Query, QueryResult


# Current schema version
SCHEMA_VERSION = "1.0.0"

# SQL for creating tables
CREATE_TABLES_SQL = """
-- Schema version table
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    description TEXT
);

-- Entities table (for storing JSON data)
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    UNIQUE(entity_type, id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_entities_entity_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_created_at ON entities(created_at);
CREATE INDEX IF NOT EXISTS idx_entities_updated_at ON entities(updated_at);
"""


class SQLiteBackend(StorageBackend):
    """
    SQLite storage backend for Liftra.
    
    This backend stores all data in a single SQLite database file,
    with each entity stored as JSON in the entities table.
    
    Note: This is a simplified version that uses sqlite3 directly.
    In production, you may want to use aiosqlite for async operations.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize the SQLite backend.
        
        Args:
            config: Configuration dictionary with:
                - database_path: Path to the SQLite database file
                - encryption_key: Optional encryption key for data
        """
        super().__init__(config)
        
        self.database_path = config.get("database_path", "liftra.db")
        self.encryption_key = config.get("encryption_key")
        self._connection: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()
        
        # Ensure database directory exists
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

    async def connect(self) -> None:
        """Connect to the SQLite database."""
        async with self._lock:
            if self._connection is not None:
                return
            
            try:
                self._connection = sqlite3.connect(self.database_path)
                self._connection.row_factory = sqlite3.Row
                
                # Enable foreign keys
                self._connection.execute("PRAGMA foreign_keys = ON")
                
                # Initialize schema
                await self._initialize_schema()
                
            except Exception as e:
                raise StorageError(f"Failed to connect to SQLite database: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from the SQLite database."""
        async with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    async def is_connected(self) -> bool:
        """Check if the backend is connected."""
        return self._connection is not None

    async def _initialize_schema(self) -> None:
        """Initialize the database schema."""
        if self._connection is None:
            raise StorageError("Database not connected")
        
        # Create tables
        self._connection.executescript(CREATE_TABLES_SQL)
        
        # Check current schema version directly (avoid circular dependency)
        cursor = self._connection.cursor()
        cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        row = cursor.fetchone()
        current_version = row["version"] if row else None
        
        # If no schema version, insert current
        if current_version is None:
            self._connection.execute(
                "INSERT INTO schema_version (version, created_at, description) VALUES (?, ?, ?)",
                (SCHEMA_VERSION, datetime.utcnow().isoformat(), "Initial schema")
            )
            self._connection.commit()
        elif current_version != SCHEMA_VERSION:
            # For now, just recreate the schema
            # In a real implementation, this would handle incremental migrations
            self._connection.executescript(CREATE_TABLES_SQL)
            self._connection.commit()

    async def _ensure_connected(self) -> None:
        """Ensure the backend is connected."""
        if not await self.is_connected():
            await self.connect()

    def _execute_sync(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a synchronous SQL query."""
        if self._connection is None:
            raise StorageError("Database not connected")
        
        cursor = self._connection.cursor()
        cursor.execute(sql, params)
        return cursor

    async def get(self, entity_type: str, entity_id: UUID | str) -> dict[str, Any]:
        """Get a single entity by ID."""
        await self._ensure_connected()
        
        entity_id_str = str(entity_id)
        
        cursor = self._execute_sync(
            "SELECT data FROM entities WHERE entity_type = ? AND id = ?",
            (entity_type, entity_id_str)
        )
        row = cursor.fetchone()
        
        if row is None:
            raise NotFoundError(entity_type, entity_id_str)
        
        try:
            data = json.loads(row["data"])
            data["id"] = entity_id_str
            return data
        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to decode entity data: {e}") from e

    async def list(
        self, entity_type: str, query: Query | None = None
    ) -> QueryResult[dict[str, Any]]:
        """List entities of a given type."""
        await self._ensure_connected()
        
        # Build SQL query
        sql = "SELECT id, data FROM entities WHERE entity_type = ?"
        params: list[Any] = [entity_type]
        
        # Add pagination
        if query and query.limit is not None:
            sql += " LIMIT ?"
            params.append(query.limit)
            if query.offset > 0:
                sql += " OFFSET ?"
                params.append(query.offset)
        
        # Execute query
        cursor = self._execute_sync(sql, tuple(params))
        rows = cursor.fetchall()
        
        # Get total count
        count_cursor = self._execute_sync(
            "SELECT COUNT(*) FROM entities WHERE entity_type = ?",
            (entity_type,)
        )
        count_row = count_cursor.fetchone()
        total = count_row[0] if count_row else 0
        
        # Parse results
        items = []
        for row in rows:
            try:
                data = json.loads(row["data"])
                data["id"] = row["id"]
                items.append(data)
            except json.JSONDecodeError:
                continue
        
        return QueryResult[
            dict[str, Any]
        ](
            items=items,
            total=total,
            has_more=len(items) < total if query and query.limit else False,
            offset=query.offset if query else 0,
            limit=query.limit if query else None,
        )

    async def create(self, entity_type: str, data: dict[str, Any]) -> UUID:
        """Create a new entity."""
        await self._ensure_connected()
        
        entity_id = str(data.get("id") or str(uuid4()))
        
        # Check for duplicates
        cursor = self._execute_sync(
            "SELECT id FROM entities WHERE entity_type = ? AND id = ?",
            (entity_type, entity_id)
        )
        if cursor.fetchone():
            raise DuplicateError(entity_type, "id", entity_id)
        
        # Prepare data for storage
        storage_data = {
            "id": entity_id,
            **{k: v for k, v in data.items() if k != "id"}
        }
        
        try:
            json_data = json.dumps(storage_data, default=str)
        except TypeError as e:
            raise ValidationError(f"Failed to serialize entity data: {e}") from e
        
        now = datetime.utcnow().isoformat()
        
        try:
            self._execute_sync(
                """INSERT INTO entities (id, entity_type, data, created_at, updated_at, version) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (entity_id, entity_type, json_data, now, now, data.get("version", 1))
            )
            self._connection.commit()
            
            return UUID(entity_id)
        except sqlite3.IntegrityError as e:
            raise DuplicateError(entity_type, "id", entity_id) from e
        except Exception as e:
            raise StorageError(f"Failed to create entity: {e}") from e

    async def update(
        self, entity_type: str, entity_id: UUID | str, data: dict[str, Any]
    ) -> None:
        """Update an existing entity."""
        await self._ensure_connected()
        
        entity_id_str = str(entity_id)
        
        # Check if entity exists
        cursor = self._execute_sync(
            "SELECT id, version FROM entities WHERE entity_type = ? AND id = ?",
            (entity_type, entity_id_str)
        )
        row = cursor.fetchone()
        
        if row is None:
            raise NotFoundError(entity_type, entity_id_str)
        
        # Get current version for optimistic locking
        current_version = row["version"]
        new_version = current_version + 1
        
        # Prepare data for storage
        storage_data = {
            "id": entity_id_str,
            **{k: v for k, v in data.items() if k != "id"}
        }
        
        try:
            json_data = json.dumps(storage_data, default=str)
        except TypeError as e:
            raise ValidationError(f"Failed to serialize entity data: {e}") from e
        
        now = datetime.utcnow().isoformat()
        
        try:
            self._execute_sync(
                """UPDATE entities SET data = ?, updated_at = ?, version = ? 
                   WHERE entity_type = ? AND id = ? AND version = ?""",
                (json_data, now, new_version, entity_type, entity_id_str, current_version)
            )
            
            # Check if update was successful
            if self._connection.total_changes == 0:
                raise StorageError("Entity was modified by another process (optimistic lock)")
            
            self._connection.commit()
        except Exception as e:
            raise StorageError(f"Failed to update entity: {e}") from e

    async def delete(self, entity_type: str, entity_id: UUID | str) -> None:
        """Delete an entity."""
        await self._ensure_connected()
        
        entity_id_str = str(entity_id)
        
        try:
            self._execute_sync(
                "DELETE FROM entities WHERE entity_type = ? AND id = ?",
                (entity_type, entity_id_str)
            )
            
            if self._connection.total_changes == 0:
                raise NotFoundError(entity_type, entity_id_str)
            
            self._connection.commit()
        except Exception as e:
            raise StorageError(f"Failed to delete entity: {e}") from e

    async def query(self, query: Query) -> QueryResult[dict[str, Any]]:
        """Execute a custom query."""
        # For SQLite, we can use the list method with the provided query
        return await self.list(query.entity_type, query)

    async def count(
        self, entity_type: str, filters: dict[str, Any] | None = None
    ) -> int:
        """Count entities of a given type."""
        await self._ensure_connected()
        
        sql = "SELECT COUNT(*) FROM entities WHERE entity_type = ?"
        params: list[Any] = [entity_type]
        
        cursor = self._execute_sync(sql, tuple(params))
        row = cursor.fetchone()
        
        return row[0] if row else 0

    async def exists(self, entity_type: str, entity_id: UUID | str) -> bool:
        """Check if an entity exists."""
        try:
            await self.get(entity_type, entity_id)
            return True
        except NotFoundError:
            return False

    async def backup(
        self, destination: str, backup_name: str | None = None
    ) -> str:
        """Create a backup of the storage."""
        await self._ensure_connected()
        
        # Create destination directory if it doesn't exist
        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)
        
        # Generate backup filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = backup_name or f"liftra_backup_{timestamp}.db"
        backup_path = dest_path / backup_filename
        
        # Close current connection
        await self.disconnect()
        
        # Copy database file
        source_path = Path(self.database_path)
        if source_path.exists():
            import shutil
            shutil.copy2(source_path, backup_path)
        
        # Reconnect
        await self.connect()
        
        return str(backup_path)

    async def restore(self, source: str) -> None:
        """Restore storage from a backup."""
        source_path = Path(source)
        if not source_path.exists():
            raise StorageError(f"Backup file not found: {source}")
        
        # Close current connection
        await self.disconnect()
        
        # Copy backup file to database location
        dest_path = Path(self.database_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(source_path, dest_path)
        
        # Reconnect
        await self.connect()

    async def get_schema_version(self) -> str:
        """Get the current schema version."""
        await self._ensure_connected()
        
        cursor = self._execute_sync(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
        )
        row = cursor.fetchone()
        
        return row["version"] if row else "0.0.0"

    async def migrate(self, target_version: str | None = None) -> str:
        """Migrate the storage schema to a target version."""
        current_version = await self.get_schema_version()
        
        if target_version is None:
            target_version = SCHEMA_VERSION
        
        if current_version == target_version:
            return current_version
        
        # For now, just recreate the schema
        # In a real implementation, this would handle incremental migrations
        await self._initialize_schema()
        
        return await self.get_schema_version()

    async def get_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        await self._ensure_connected()
        
        # Get database file size
        db_path = Path(self.database_path)
        file_size = db_path.stat().st_size if db_path.exists() else 0
        
        # Get entity counts
        cursor = self._execute_sync(
            "SELECT entity_type, COUNT(*) as count FROM entities GROUP BY entity_type"
        )
        rows = cursor.fetchall()
        
        entity_counts = {}
        total_entities = 0
        for row in rows:
            entity_counts[row["entity_type"]] = row["count"]
            total_entities += row["count"]
        
        return {
            "database_path": self.database_path,
            "file_size_bytes": file_size,
            "total_entities": total_entities,
            "entity_counts": entity_counts,
            "schema_version": await self.get_schema_version(),
        }

    async def clear(self, entity_type: str | None = None) -> None:
        """Clear all data from storage."""
        await self._ensure_connected()
        
        if entity_type:
            self._execute_sync(
                "DELETE FROM entities WHERE entity_type = ?",
                (entity_type,)
            )
        else:
            self._execute_sync("DELETE FROM entities")
        
        self._connection.commit()
