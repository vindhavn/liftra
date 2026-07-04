"""
Base models and configuration for Liftra domain models.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field


class BaseConfig:
    """Base configuration for all Liftra models."""

    # Use enum values for validation
    use_enum_values = True
    # Allow population by field name (alias)
    populate_by_name = True
    # Extra fields are not allowed by default
    extra = "forbid"
    # Use UUID strings for IDs
    str_strip_whitespace = True
    # JSON schema extra for OpenAPI
    json_schema_extra = {
        "examples": [{"id": str(uuid4()), "created_at": datetime.now().isoformat()}]
    }


class BaseModel(PydanticBaseModel):
    """Base model for all Liftra domain entities."""

    model_config = ConfigDict(**BaseConfig.__dict__)

    # Common fields for all entities
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the entity")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the entity was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the entity was last updated"
    )
    version: int = Field(default=1, description="Version of the entity for optimistic locking")

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BaseModel):
            return False
        return self.id == other.id

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary, excluding None values."""
        return self.model_dump(exclude_none=True, by_alias=True)

    def to_dict_for_storage(self) -> dict[str, Any]:
        """Convert model to dictionary for storage, including all fields."""
        data = self.model_dump(by_alias=True)
        # Convert UUID to string for storage
        if "id" in data:
            data["id"] = str(data["id"])
        # Convert datetime to ISO format strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, UUID):
                data[key] = str(value)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseModel":
        """Create model instance from dictionary."""
        # Convert string IDs to UUID
        if "id" in data and isinstance(data["id"], str):
            data["id"] = UUID(data["id"])
        # Convert ISO format strings to datetime
        for key, value in data.items():
            if isinstance(value, str) and key.endswith("_at"):
                try:
                    data[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
        return cls(**data)


# Type aliases for common fields
EntityId = UUID
CreatedAt = datetime
UpdatedAt = datetime
Version = int
