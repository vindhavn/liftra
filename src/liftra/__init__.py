"""
Liftra - Comprehensive Personal Finance Tracking Application

This package provides the core functionality for tracking personal finances,
including accounts, transactions, investments, taxes, pensions, and more.
"""

__version__ = "0.1.0"
__author__ = "vindhavn"
__license__ = "MIT"

# Submodules
from liftra.core import models, repositories, exceptions
from liftra.storage import backends
from liftra.services import transaction, account, reporting
from liftra.api import v1
from liftra.plugins import manager as plugin_manager
from liftra.security import encryption, authentication

__all__ = [
    "models",
    "repositories",
    "exceptions",
    "backends",
    "transaction",
    "account",
    "reporting",
    "v1",
    "plugin_manager",
    "encryption",
    "authentication",
]
