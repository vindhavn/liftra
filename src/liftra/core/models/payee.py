"""
Payee models for Liftra.
"""

from typing import Any

from pydantic import Field, field_validator

from liftra.core.models.base import BaseModel


class PayeeLocation(BaseModel):
    """
    Represents a location or branch for a payee.
    
    This is particularly useful for supermarkets and banks with multiple branches.
    """

    # Location details
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the location/branch"
    )
    address: str | None = Field(
        default=None, max_length=1000, description="Full address of the location"
    )
    city: str | None = Field(
        default=None, max_length=255, description="City"
    )
    region: str | None = Field(
        default=None, max_length=255, description="Region/state"
    )
    postal_code: str | None = Field(
        default=None, max_length=50, description="Postal code"
    )
    country: str | None = Field(
        default=None, min_length=2, max_length=2, description="ISO country code"
    )
    
    # Contact information
    phone: str | None = Field(
        default=None, max_length=50, description="Phone number"
    )
    email: str | None = Field(
        default=None, max_length=255, description="Email address"
    )
    website: str | None = Field(
        default=None, max_length=500, description="Website URL"
    )
    
    # Geographic coordinates
    latitude: float | None = Field(
        default=None, ge=-90, le=90, description="Latitude"
    )
    longitude: float | None = Field(
        default=None, ge=-180, le=180, description="Longitude"
    )
    
    # Branch-specific information
    branch_code: str | None = Field(
        default=None, max_length=50, description="Branch code"
    )
    branch_number: str | None = Field(
        default=None, max_length=50, description="Branch number"
    )
    
    # Metadata
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str | None) -> str | None:
        """Validate country code."""
        if v is None:
            return None
        return v.upper()
    
    def __str__(self) -> str:
        if self.city:
            return f"{self.name}, {self.city}"
        return self.name


class Payee(BaseModel):
    """
    Represents a payee (person or organization) for transactions.
    
    Payees can be individuals, companies, organizations, or any entity
    that receives or sends money.
    """

    # Payee details
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the payee"
    )
    description: str | None = Field(
        default=None, max_length=1000, description="Description of the payee"
    )
    
    # Payee type
    is_person: bool = Field(
        default=False, description="Whether the payee is a person"
    )
    is_company: bool = Field(
        default=True, description="Whether the payee is a company"
    )
    is_government: bool = Field(
        default=False, description="Whether the payee is a government entity"
    )
    
    # Contact information
    phone: str | None = Field(
        default=None, max_length=50, description="Primary phone number"
    )
    email: str | None = Field(
        default=None, max_length=255, description="Primary email address"
    )
    website: str | None = Field(
        default=None, max_length=500, description="Website URL"
    )
    
    # Address
    address: str | None = Field(
        default=None, max_length=1000, description="Primary address"
    )
    city: str | None = Field(
        default=None, max_length=255, description="City"
    )
    region: str | None = Field(
        default=None, max_length=255, description="Region/state"
    )
    postal_code: str | None = Field(
        default=None, max_length=50, description="Postal code"
    )
    country: str | None = Field(
        default=None, min_length=2, max_length=2, description="ISO country code"
    )
    
    # Locations/Branches
    location_ids: list[str] = Field(
        default_factory=list, 
        description="List of location IDs for this payee"
    )
    default_location_id: str | None = Field(
        default=None, description="ID of the default location"
    )
    
    # Tax information
    tax_id: str | None = Field(
        default=None, max_length=100, description="Tax identification number"
    )
    vat_number: str | None = Field(
        default=None, max_length=100, description="VAT number"
    )
    
    # Category
    category_id: str | None = Field(
        default=None, description="ID of the category for this payee"
    )
    
    # Status
    is_active: bool = Field(
        default=True, description="Whether the payee is active"
    )
    is_verified: bool = Field(
        default=False, description="Whether the payee information is verified"
    )
    
    # Metadata
    aliases: list[str] = Field(
        default_factory=list, 
        description="Alternative names for this payee"
    )
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for extensibility"
    )
    notes: str | None = Field(
        default=None, max_length=5000, description="Additional notes"
    )
    
    # Attachments
    attachment_ids: list[str] = Field(
        default_factory=list, description="List of attachment IDs"
    )
    
    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str | None) -> str | None:
        """Validate country code."""
        if v is None:
            return None
        return v.upper()
    
    @property
    def display_name(self) -> str:
        """Get display name with type indicator."""
        if self.is_person:
            return f"👤 {self.name}"
        elif self.is_government:
            return f"🏛️ {self.name}"
        else:
            return f"🏢 {self.name}"
    
    def __str__(self) -> str:
        return self.name
