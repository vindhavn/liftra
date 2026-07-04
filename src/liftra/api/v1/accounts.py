"""
Account API endpoints for Liftra v1.

This is a placeholder that will be implemented when FastAPI is available.
"""

# Placeholder to avoid import errors when FastAPI is not installed
try:
    from fastapi import APIRouter
    from pydantic import BaseModel
    from typing import Any
    from uuid import UUID
    
    from liftra.core.models import Account, AccountType, AccountStatus
    from liftra.storage.manager import StorageManager
    
    router = APIRouter()
    
    class AccountCreateRequest(BaseModel):
        name: str
        account_type: AccountType = AccountType.BANK
        currency_code: str = "GBP"
        description: str | None = None
    
    class AccountResponse(BaseModel):
        id: UUID
        name: str
        account_type: AccountType
        currency_code: str
        status: AccountStatus = AccountStatus.ACTIVE
        created_at: str
        updated_at: str
        version: int = 1
    
    @router.get("")
    async def list_accounts():
        """List all accounts."""
        raise NotImplementedError("API not yet implemented")
    
    @router.post("")
    async def create_account(request: AccountCreateRequest):
        """Create a new account."""
        raise NotImplementedError("API not yet implemented")
    
    @router.get("/{account_id}")
    async def get_account(account_id: UUID):
        """Get a specific account by ID."""
        raise NotImplementedError("API not yet implemented")
    
    @router.put("/{account_id}")
    async def update_account(account_id: UUID, request: AccountCreateRequest):
        """Update an account."""
        raise NotImplementedError("API not yet implemented")
    
    @router.delete("/{account_id}")
    async def delete_account(account_id: UUID):
        """Delete an account."""
        raise NotImplementedError("API not yet implemented")

except ImportError:
    # FastAPI not available, create dummy router
    class APIRouter:
        def __init__(self, *args, **kwargs):
            pass
    
    router = APIRouter()
