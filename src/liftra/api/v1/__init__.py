"""
API v1 endpoints for Liftra.

This is a placeholder that will be implemented when FastAPI is available.
"""

# Placeholder to avoid import errors when FastAPI is not installed
try:
    from fastapi import APIRouter
    
    # Create the v1 router
    router = APIRouter(prefix="/v1")
    
except ImportError:
    # FastAPI not available, create dummy router
    class APIRouter:
        def __init__(self, *args, **kwargs):
            pass
        
        def include_router(self, *args, **kwargs):
            pass
    
    router = APIRouter(prefix="/v1")
