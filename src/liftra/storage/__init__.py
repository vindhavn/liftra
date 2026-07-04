"""
Storage layer for Liftra.

This module provides the storage abstraction layer that allows switching
between different backends (SQLite, cloud storage, server).
"""

from liftra.storage.backends.base import StorageBackend, Query, QueryResult
from liftra.storage.backends.sqlite import SQLiteBackend
from liftra.storage.backends.cloud import CloudStorageBackend
from liftra.storage.backends.server import ServerBackend
from liftra.storage.manager import StorageManager

__all__ = [
    "StorageBackend",
    "Query",
    "QueryResult",
    "SQLiteBackend",
    "CloudStorageBackend",
    "ServerBackend",
    "StorageManager",
]
