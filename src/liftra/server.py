"""
Server for Liftra.

This module provides the server component for Liftra, allowing
remote access to the application via REST API.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from liftra.core.exceptions import LiftraError, NotFoundError, ValidationError
from liftra.storage.manager import StorageManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global storage manager
_storage_manager: StorageManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _storage_manager
    
    # Startup
    logger.info("Starting Liftra server...")
    
    # Initialize storage
    config = {
        "storage_type": "sqlite",
        "database_path": "liftra_server.db"
    }
    
    _storage_manager = StorageManager(config)
    await _storage_manager.initialize(config)
    
    logger.info("Liftra server started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Liftra server...")
    
    if _storage_manager:
        await _storage_manager.close()
    
    logger.info("Liftra server stopped")


# Create FastAPI application
app = FastAPI(
    title="Liftra API",
    description="REST API for Liftra Personal Finance Application",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(LiftraError)
async def liftra_error_handler(request: Request, exc: LiftraError) -> JSONResponse:
    """Handle Liftra-specific errors."""
    logger.error(f"Liftra error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "LiftraError",
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle not found errors."""
    logger.error(f"Not found: {exc.resource_type} with ID {exc.resource_id}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "NotFoundError",
            "message": f"{exc.resource_type} not found",
            "resource_type": exc.resource_type,
            "resource_id": exc.resource_id
        }
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors."""
    logger.error(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": exc.message,
            "details": exc.details
        }
    )


# Health check endpoint
@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    global _storage_manager
    
    if _storage_manager is None:
        raise HTTPException(status_code=503, detail="Storage not initialized")
    
    connected = await _storage_manager.is_connected()
    
    return {
        "status": "healthy" if connected else "unhealthy",
        "storage_connected": connected,
        "storage_backend": _storage_manager.current_backend_name
    }


# Storage info endpoint
@app.get("/api/storage/info")
async def storage_info() -> dict[str, Any]:
    """Get storage information."""
    global _storage_manager
    
    if _storage_manager is None:
        raise HTTPException(status_code=503, detail="Storage not initialized")
    
    stats = await _storage_manager.get_stats()
    
    return {
        "backend": _storage_manager.current_backend_name,
        "stats": stats
    }


# API v1 endpoints will be mounted here
from liftra.api.v1 import router as v1_router
app.include_router(v1_router, prefix="/api/v1")


def main() -> None:
    """Main entry point for the server."""
    import uvicorn
    
    uvicorn.run(
        "liftra.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
