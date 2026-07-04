"""
API module for Liftra.

This is a placeholder that will be implemented when FastAPI is available.
"""

# Placeholder to avoid import errors when FastAPI is not installed
try:
    from liftra.api.v1 import router
except ImportError:
    # Create a dummy router
    class DummyRouter:
        pass
    router = DummyRouter()
