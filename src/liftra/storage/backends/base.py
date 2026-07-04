"""
Base storage backend interface for Liftra.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar, Protocol
from uuid import UUID

from liftra.core.exceptions import StorageError, NotFoundError, DuplicateError


# Type variable for entity types
T = TypeVar("T")


@dataclass
class Query:
    """
    Represents a query for the storage backend.
    
    This class provides a flexible way to query data from the storage backend
    with filtering, sorting, pagination, and aggregation.
    """

    # Entity type to query
    entity_type: str
    
    # Filter conditions: {"field": {"operator": value}}
    # Operator can be: eq, ne, gt, gte, lt, lte, in, nin, contains, icontains, startswith, istartswith, etc.
    filters: dict[str, dict[str, Any]] = field(default_factory=dict)
    
    # Fields to include in results (None = all fields)
    include: list[str] | None = None
    
    # Fields to exclude from results
    exclude: list[str] | None = None
    
    # Sorting: [{"field": "name", "direction": "asc" | "desc"}]
    order_by: list[dict[str, str]] = field(default_factory=list)
    
    # Pagination
    offset: int = 0
    limit: int | None = None
    
    # Aggregation
    group_by: list[str] | None = None
    aggregate: dict[str, str] | None = None  # {"field": "sum" | "avg" | "count" | "min" | "max"}
    
    # Join conditions
    joins: list[dict[str, Any]] = field(default_factory=list)
    
    # Distinct results
    distinct: bool = False
    
    # Count only
    count: bool = False
    
    def __post_init__(self) -> None:
        """Validate query parameters."""
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")
        if self.limit is not None and self.limit <= 0:
            raise ValueError("Limit must be positive")


@dataclass
class QueryResult(Generic[T]):
    """
    Represents the result of a query.
    """

    # List of entities returned
    items: list[T]
    
    # Total count of items matching the query (before pagination)
    total: int
    
    # Whether there are more items available
    has_more: bool
    
    # Offset used for this query
    offset: int
    
    # Limit used for this query
    limit: int | None


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.
    
    All storage backends must implement this interface to provide
    consistent data access across different storage types.
    """

    @abstractmethod
    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize the storage backend with configuration.
        
        Args:
            config: Configuration dictionary for the backend
        """
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the storage backend."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the storage backend."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if the backend is connected."""
        pass

    @abstractmethod
    async def get(self, entity_type: str, entity_id: UUID | str) -> dict[str, Any]:
        """
        Get a single entity by ID.
        
        Args:
            entity_type: Type of entity to get
            entity_id: ID of the entity
            
        Returns:
            Dictionary representing the entity
            
        Raises:
            NotFoundError: If entity is not found
            StorageError: If there is an error accessing storage
        """
        pass

    @abstractmethod
    async def list(self, entity_type: str, query: Query | None = None) -> QueryResult[dict[str, Any]]:
        """
        List entities of a given type.
        
        Args:
            entity_type: Type of entity to list
            query: Optional query parameters
            
        Returns:
            QueryResult containing matching entities
        """
        pass

    @abstractmethod
    async def create(self, entity_type: str, data: dict[str, Any]) -> UUID:
        """
        Create a new entity.
        
        Args:
            entity_type: Type of entity to create
            data: Dictionary containing entity data
            
        Returns:
            ID of the created entity
            
        Raises:
            ValidationError: If data is invalid
            DuplicateError: If entity already exists
            StorageError: If there is an error accessing storage
        """
        pass

    @abstractmethod
    async def update(self, entity_type: str, entity_id: UUID | str, data: dict[str, Any]) -> None:
        """
        Update an existing entity.
        
        Args:
            entity_type: Type of entity to update
            entity_id: ID of the entity to update
            data: Dictionary containing updated data
            
        Raises:
            NotFoundError: If entity is not found
            ValidationError: If data is invalid
            StorageError: If there is an error accessing storage
        """
        pass

    @abstractmethod
    async def delete(self, entity_type: str, entity_id: UUID | str) -> None:
        """
        Delete an entity.
        
        Args:
            entity_type: Type of entity to delete
            entity_id: ID of the entity to delete
            
        Raises:
            NotFoundError: If entity is not found
            StorageError: If there is an error accessing storage
        """
        pass

    @abstractmethod
    async def query(self, query: Query) -> QueryResult[dict[str, Any]]:
        """
        Execute a custom query.
        
        Args:
            query: Query to execute
            
        Returns:
            QueryResult containing matching entities
        """
        pass

    @abstractmethod
    async def count(self, entity_type: str, filters: dict[str, Any] | None = None) -> int:
        """
        Count entities of a given type.
        
        Args:
            entity_type: Type of entity to count
            filters: Optional filter conditions
            
        Returns:
            Count of matching entities
        """
        pass

    @abstractmethod
    async def exists(self, entity_type: str, entity_id: UUID | str) -> bool:
        """
        Check if an entity exists.
        
        Args:
            entity_type: Type of entity to check
            entity_id: ID of the entity to check
            
        Returns:
            True if entity exists, False otherwise
        """
        pass

    @abstractmethod
    async def backup(self, destination: str, backup_name: str | None = None) -> str:
        """
        Create a backup of the storage.
        
        Args:
            destination: Destination path or URL for the backup
            backup_name: Optional name for the backup
            
        Returns:
            Path or URL of the created backup
        """
        pass

    @abstractmethod
    async def restore(self, source: str) -> None:
        """
        Restore storage from a backup.
        
        Args:
            source: Path or URL of the backup to restore
            
        Raises:
            StorageError: If there is an error restoring the backup
        """
        pass

    @abstractmethod
    async def get_schema_version(self) -> str:
        """Get the current schema version."""
        pass

    @abstractmethod
    async def migrate(self, target_version: str | None = None) -> str:
        """
        Migrate the storage schema to a target version.
        
        Args:
            target_version: Target schema version (None = latest)
            
        Returns:
            Version migrated to
        """
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Get storage statistics (counts, sizes, etc.)."""
        pass

    @abstractmethod
    async def clear(self, entity_type: str | None = None) -> None:
        """
        Clear all data from storage.
        
        Args:
            entity_type: Optional entity type to clear (None = all entities)
        """
        pass
