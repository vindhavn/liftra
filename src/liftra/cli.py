"""
Command-line interface for Liftra.

This module provides the CLI for managing Liftra from the command line.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from liftra.core.models import Account, Transaction
from liftra.storage.manager import StorageManager
from liftra.storage.backends import Query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CLI:
    """Command-line interface for Liftra."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.parser = argparse.ArgumentParser(
            prog="liftra",
            description="Liftra - Personal Finance Tracking Application",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  liftra account list
  liftra account create --name "My Bank Account" --currency GBP
  liftra transaction list --account <account-id>
  liftra transaction create --account <account-id> --amount 100.00 --description "Groceries"
  liftra backup create --destination ./backups
  liftra restore --source ./backups/liftra_backup_20240101.db
"""
        )
        
        # Global arguments
        self.parser.add_argument(
            "--config",
            type=str,
            default=None,
            help="Path to configuration file"
        )
        self.parser.add_argument(
            "--storage-type",
            type=str,
            default=None,
            choices=["sqlite", "cloud", "server"],
            help="Storage backend type"
        )
        self.parser.add_argument(
            "--database-path",
            type=str,
            default=None,
            help="Path to SQLite database file"
        )
        self.parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose output"
        )
        
        # Subcommands
        self.subparsers = self.parser.add_subparsers(
            dest="command",
            title="commands",
            description="Available commands"
        )
        
        # Account commands
        self._setup_account_commands()
        self._setup_transaction_commands()
        self._setup_storage_commands()
        self._setup_backup_commands()
        self._setup_report_commands()
        self._setup_import_export_commands()

    def _setup_account_commands(self) -> None:
        """Set up account-related commands."""
        account_parser = self.subparsers.add_parser(
            "account",
            help="Manage accounts"
        )
        account_subparsers = account_parser.add_subparsers(
            dest="account_command",
            title="account commands"
        )
        
        # List accounts
        list_parser = account_subparsers.add_parser(
            "list",
            help="List all accounts"
        )
        list_parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of accounts to list"
        )
        list_parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Offset for pagination"
        )
        list_parser.set_defaults(func=self._list_accounts)
        
        # Create account
        create_parser = account_subparsers.add_parser(
            "create",
            help="Create a new account"
        )
        create_parser.add_argument(
            "--name",
            required=True,
            help="Name of the account"
        )
        create_parser.add_argument(
            "--type",
            type=str,
            default="bank",
            choices=["bank", "cash", "credit_card", "savings", "investment", "pension", "loan", "mortgage", "other"],
            help="Type of account"
        )
        create_parser.add_argument(
            "--currency",
            type=str,
            default="GBP",
            help="Currency code (ISO 4217)"
        )
        create_parser.add_argument(
            "--description",
            type=str,
            default=None,
            help="Description of the account"
        )
        create_parser.add_argument(
            "--institution",
            type=str,
            default=None,
            help="Name of the financial institution"
        )
        create_parser.set_defaults(func=self._create_account)
        
        # Get account
        get_parser = account_subparsers.add_parser(
            "get",
            help="Get account details"
        )
        get_parser.add_argument(
            "account_id",
            help="ID of the account to get"
        )
        get_parser.set_defaults(func=self._get_account)
        
        # Update account
        update_parser = account_subparsers.add_parser(
            "update",
            help="Update an account"
        )
        update_parser.add_argument(
            "account_id",
            help="ID of the account to update"
        )
        update_parser.add_argument(
            "--name",
            type=str,
            default=None,
            help="New name for the account"
        )
        update_parser.add_argument(
            "--description",
            type=str,
            default=None,
            help="New description for the account"
        )
        update_parser.set_defaults(func=self._update_account)
        
        # Delete account
        delete_parser = account_subparsers.add_parser(
            "delete",
            help="Delete an account"
        )
        delete_parser.add_argument(
            "account_id",
            help="ID of the account to delete"
        )
        delete_parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="Force deletion without confirmation"
        )
        delete_parser.set_defaults(func=self._delete_account)

    def _setup_transaction_commands(self) -> None:
        """Set up transaction-related commands."""
        transaction_parser = self.subparsers.add_parser(
            "transaction",
            help="Manage transactions"
        )
        transaction_subparsers = transaction_parser.add_subparsers(
            dest="transaction_command",
            title="transaction commands"
        )
        
        # List transactions
        list_parser = transaction_subparsers.add_parser(
            "list",
            help="List transactions"
        )
        list_parser.add_argument(
            "--account",
            type=str,
            default=None,
            help="Filter by account ID"
        )
        list_parser.add_argument(
            "--category",
            type=str,
            default=None,
            help="Filter by category ID"
        )
        list_parser.add_argument(
            "--payee",
            type=str,
            default=None,
            help="Filter by payee ID"
        )
        list_parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of transactions to list"
        )
        list_parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Offset for pagination"
        )
        list_parser.set_defaults(func=self._list_transactions)
        
        # Create transaction
        create_parser = transaction_subparsers.add_parser(
            "create",
            help="Create a new transaction"
        )
        create_parser.add_argument(
            "--account",
            required=True,
            help="ID of the account for the transaction"
        )
        create_parser.add_argument(
            "--amount",
            type=float,
            required=True,
            help="Transaction amount"
        )
        create_parser.add_argument(
            "--currency",
            type=str,
            default="GBP",
            help="Currency code (ISO 4217)"
        )
        create_parser.add_argument(
            "--description",
            type=str,
            required=True,
            help="Description of the transaction"
        )
        create_parser.add_argument(
            "--type",
            type=str,
            default="expense",
            choices=["income", "expense", "transfer", "refund", "compensation", "fee", "interest", "dividend", "capital_gain", "tax", "pension_contribution", "investment", "other"],
            help="Type of transaction"
        )
        create_parser.add_argument(
            "--category",
            type=str,
            default=None,
            help="ID of the category for the transaction"
        )
        create_parser.add_argument(
            "--payee",
            type=str,
            default=None,
            help="ID of the payee for the transaction"
        )
        create_parser.add_argument(
            "--date",
            type=str,
            default=None,
            help="Date of the transaction (YYYY-MM-DD)"
        )
        create_parser.set_defaults(func=self._create_transaction)

    def _setup_storage_commands(self) -> None:
        """Set up storage-related commands."""
        storage_parser = self.subparsers.add_parser(
            "storage",
            help="Manage storage"
        )
        storage_subparsers = storage_parser.add_subparsers(
            dest="storage_command",
            title="storage commands"
        )
        
        # Info
        info_parser = storage_subparsers.add_parser(
            "info",
            help="Show storage information"
        )
        info_parser.set_defaults(func=self._storage_info)
        
        # Stats
        stats_parser = storage_subparsers.add_parser(
            "stats",
            help="Show storage statistics"
        )
        stats_parser.set_defaults(func=self._storage_stats)

    def _setup_backup_commands(self) -> None:
        """Set up backup-related commands."""
        backup_parser = self.subparsers.add_parser(
            "backup",
            help="Manage backups"
        )
        backup_subparsers = backup_parser.add_subparsers(
            dest="backup_command",
            title="backup commands"
        )
        
        # Create backup
        create_parser = backup_subparsers.add_parser(
            "create",
            help="Create a backup"
        )
        create_parser.add_argument(
            "--destination",
            type=str,
            default="./backups",
            help="Destination directory for the backup"
        )
        create_parser.add_argument(
            "--name",
            type=str,
            default=None,
            help="Name for the backup file"
        )
        create_parser.set_defaults(func=self._create_backup)
        
        # Restore backup
        restore_parser = backup_subparsers.add_parser(
            "restore",
            help="Restore from a backup"
        )
        restore_parser.add_argument(
            "--source",
            type=str,
            required=True,
            help="Path to the backup file to restore"
        )
        restore_parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="Force restore without confirmation"
        )
        restore_parser.set_defaults(func=self._restore_backup)
        
        # List backups
        list_parser = backup_subparsers.add_parser(
            "list",
            help="List available backups"
        )
        list_parser.add_argument(
            "--directory",
            type=str,
            default="./backups",
            help="Directory containing backups"
        )
        list_parser.set_defaults(func=self._list_backups)

    def _setup_report_commands(self) -> None:
        """Set up report-related commands."""
        report_parser = self.subparsers.add_parser(
            "report",
            help="Generate reports"
        )
        report_subparsers = report_parser.add_subparsers(
            dest="report_command",
            title="report commands"
        )
        
        # Account balance report
        balance_parser = report_subparsers.add_parser(
            "balance",
            help="Show account balances"
        )
        balance_parser.add_argument(
            "--account",
            type=str,
            default=None,
            help="Specific account ID (all accounts if not specified)"
        )
        balance_parser.add_argument(
            "--format",
            type=str,
            default="table",
            choices=["table", "json", "csv"],
            help="Output format"
        )
        balance_parser.set_defaults(func=self._report_balance)
        
        # Transaction report
        transaction_parser = report_subparsers.add_parser(
            "transactions",
            help="Show transaction report"
        )
        transaction_parser.add_argument(
            "--account",
            type=str,
            default=None,
            help="Filter by account ID"
        )
        transaction_parser.add_argument(
            "--start-date",
            type=str,
            default=None,
            help="Start date (YYYY-MM-DD)"
        )
        transaction_parser.add_argument(
            "--end-date",
            type=str,
            default=None,
            help="End date (YYYY-MM-DD)"
        )
        transaction_parser.add_argument(
            "--format",
            type=str,
            default="table",
            choices=["table", "json", "csv"],
            help="Output format"
        )
        transaction_parser.set_defaults(func=self._report_transactions)

    def _setup_import_export_commands(self) -> None:
        """Set up import/export commands."""
        import_parser = self.subparsers.add_parser(
            "import",
            help="Import data"
        )
        import_parser.add_argument(
            "file",
            help="File to import"
        )
        import_parser.add_argument(
            "--format",
            type=str,
            default=None,
            choices=["csv", "ofx", "qif", "homebank"],
            help="Format of the file (auto-detected if not specified)"
        )
        import_parser.add_argument(
            "--account",
            type=str,
            default=None,
            help="Account ID to import into"
        )
        import_parser.set_defaults(func=self._import_data)
        
        export_parser = self.subparsers.add_parser(
            "export",
            help="Export data"
        )
        export_parser.add_argument(
            "--format",
            type=str,
            default="csv",
            choices=["csv", "ofx", "qif", "homebank", "json"],
            help="Export format"
        )
        export_parser.add_argument(
            "--output",
            "-o",
            type=str,
            default=None,
            help="Output file path"
        )
        export_parser.add_argument(
            "--account",
            type=str,
            default=None,
            help="Account ID to export"
        )
        export_parser.add_argument(
            "--start-date",
            type=str,
            default=None,
            help="Start date for transactions (YYYY-MM-DD)"
        )
        export_parser.add_argument(
            "--end-date",
            type=str,
            default=None,
            help="End date for transactions (YYYY-MM-DD)"
        )
        export_parser.set_defaults(func=self._export_data)

    async def run(self, args: list[str] | None = None) -> int:
        """
        Run the CLI with the given arguments.
        
        Args:
            args: Command-line arguments (defaults to sys.argv[1:])
            
        Returns:
            Exit code
        """
        if args is None:
            args = sys.argv[1:]
        
        try:
            parsed_args = self.parser.parse_args(args)
        except SystemExit as e:
            return e.code if e.code is not None else 0
        
        # Set up logging
        if getattr(parsed_args, "verbose", False):
            logger.setLevel(logging.DEBUG)
        
        # Build configuration
        config = self._build_config(parsed_args)
        
        # Initialize storage
        storage_manager = StorageManager(config)
        
        try:
            await storage_manager.initialize(config)
            
            # Call the appropriate function
            if hasattr(parsed_args, "func"):
                result = await parsed_args.func(parsed_args, storage_manager)
                return result if result is not None else 0
            else:
                self.parser.print_help()
                return 0
                
        except Exception as e:
            logger.error(f"Error: {e}")
            if getattr(parsed_args, "verbose", False):
                import traceback
                traceback.print_exc()
            return 1
        finally:
            await storage_manager.close()

    def _build_config(self, args: Any) -> dict[str, Any]:
        """Build configuration dictionary from command-line arguments."""
        config: dict[str, Any] = {}
        
        # Storage configuration
        if getattr(args, "storage_type", None):
            config["storage_type"] = args.storage_type
        else:
            config["storage_type"] = "sqlite"
        
        if getattr(args, "database_path", None):
            config["database_path"] = args.database_path
        
        # Load from config file if specified
        if getattr(args, "config", None):
            config_file = Path(args.config)
            if config_file.exists():
                import yaml
                with open(config_file) as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        config.update(file_config)
        
        return config

    async def _list_accounts(self, args: Any, storage: StorageManager) -> int:
        """List all accounts."""
        query = Query(
            entity_type="Account",
            limit=args.limit,
            offset=args.offset,
            order_by=[{"field": "name", "direction": "asc"}]
        )
        
        result = await storage.list("Account", query)
        
        if not result.items:
            print("No accounts found.")
            return 0
        
        print(f"Found {result.total} accounts:")
        print()
        
        for account_data in result.items:
            account = Account.from_dict(account_data)
            print(f"  {account.id}: {account.name} ({account.account_type.value}) - {account.currency_code}")
            if account.description:
                print(f"    Description: {account.description}")
            if account.current_balance is not None:
                print(f"    Balance: {account.current_balance} {account.currency_code}")
            print()
        
        return 0

    async def _create_account(self, args: Any, storage: StorageManager) -> int:
        """Create a new account."""
        account_data = {
            "name": args.name,
            "account_type": args.type,
            "currency_code": args.currency.upper(),
        }
        
        if args.description:
            account_data["description"] = args.description
        if args.institution:
            account_data["institution_name"] = args.institution
        
        account_id = await storage.create("Account", account_data)
        print(f"Created account with ID: {account_id}")
        return 0

    async def _get_account(self, args: Any, storage: StorageManager) -> int:
        """Get account details."""
        account_data = await storage.get("Account", args.account_id)
        account = Account.from_dict(account_data)
        
        print(f"Account: {account.name}")
        print(f"  ID: {account.id}")
        print(f"  Type: {account.account_type.value}")
        print(f"  Currency: {account.currency_code}")
        print(f"  Status: {account.status.value}")
        
        if account.description:
            print(f"  Description: {account.description}")
        if account.institution_name:
            print(f"  Institution: {account.institution_name}")
        if account.current_balance is not None:
            print(f"  Current Balance: {account.current_balance} {account.currency_code}")
        if account.available_balance is not None:
            print(f"  Available Balance: {account.available_balance} {account.currency_code}")
        
        if account.opened_date:
            print(f"  Opened: {account.opened_date}")
        if account.closed_date:
            print(f"  Closed: {account.closed_date}")
        
        return 0

    async def _update_account(self, args: Any, storage: StorageManager) -> int:
        """Update an account."""
        update_data: dict[str, Any] = {}
        
        if args.name:
            update_data["name"] = args.name
        if args.description:
            update_data["description"] = args.description
        
        if not update_data:
            print("No fields to update.")
            return 0
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        await storage.update("Account", args.account_id, update_data)
        print(f"Updated account {args.account_id}")
        return 0

    async def _delete_account(self, args: Any, storage: StorageManager) -> int:
        """Delete an account."""
        if not args.force:
            response = input(f"Are you sure you want to delete account {args.account_id}? (y/N): ")
            if response.lower() != "y":
                print("Deletion cancelled.")
                return 0
        
        await storage.delete("Account", args.account_id)
        print(f"Deleted account {args.account_id}")
        return 0

    async def _list_transactions(self, args: Any, storage: StorageManager) -> int:
        """List transactions."""
        filters: dict[str, dict[str, Any]] = {}
        
        if args.account:
            filters["account_id"] = {"eq": args.account}
        if args.category:
            filters["category_id"] = {"eq": args.category}
        if args.payee:
            filters["payee_id"] = {"eq": args.payee}
        
        query = Query(
            entity_type="Transaction",
            filters=filters,
            limit=args.limit,
            offset=args.offset,
            order_by=[{"field": "created_at", "direction": "desc"}]
        )
        
        result = await storage.list("Transaction", query)
        
        if not result.items:
            print("No transactions found.")
            return 0
        
        print(f"Found {result.total} transactions:")
        print()
        
        for transaction_data in result.items:
            transaction = Transaction.from_dict(transaction_data)
            date_str = transaction.logical_date.isoformat() if transaction.logical_date else "?"
            print(f"  {date_str}: {transaction.description}")
            print(f"    Amount: {transaction.amount} {transaction.currency_code}")
            print(f"    Type: {transaction.transaction_type.value}")
            print(f"    Account: {transaction.account_id}")
            if transaction.category_id:
                print(f"    Category: {transaction.category_id}")
            if transaction.payee_id:
                print(f"    Payee: {transaction.payee_id}")
            print()
        
        return 0

    async def _create_transaction(self, args: Any, storage: StorageManager) -> int:
        """Create a new transaction."""
        from datetime import date
        from decimal import Decimal
        
        transaction_data: dict[str, Any] = {
            "account_id": args.account,
            "amount": Decimal(str(args.amount)),
            "currency_code": args.currency.upper(),
            "description": args.description,
            "transaction_type": args.type,
        }
        
        if args.category:
            transaction_data["category_id"] = args.category
        if args.payee:
            transaction_data["payee_id"] = args.payee
        
        # Add logical date
        if args.date:
            try:
                date_obj = date.fromisoformat(args.date)
                transaction_data["dates"] = [
                    {
                        "date_type": "logical",
                        "date_value": args.date,
                        "is_primary": True
                    }
                ]
            except ValueError:
                print(f"Invalid date format: {args.date}. Using current date.")
        
        transaction_id = await storage.create("Transaction", transaction_data)
        print(f"Created transaction with ID: {transaction_id}")
        return 0

    async def _storage_info(self, args: Any, storage: StorageManager) -> int:
        """Show storage information."""
        info = await storage.get_stats()
        
        print("Storage Information:")
        print(f"  Backend: {storage.current_backend_name}")
        print(f"  Database Path: {info.get('database_path', 'N/A')}")
        print(f"  Schema Version: {info.get('schema_version', 'N/A')}")
        print(f"  File Size: {info.get('file_size_bytes', 0)} bytes")
        print(f"  Total Entities: {info.get('total_entities', 0)}")
        
        if info.get("entity_counts"):
            print("\nEntity Counts:")
            for entity_type, count in info["entity_counts"].items():
                print(f"  {entity_type}: {count}")
        
        return 0

    async def _storage_stats(self, args: Any, storage: StorageManager) -> int:
        """Show storage statistics."""
        # This could be enhanced with more detailed statistics
        return await self._storage_info(args, storage)

    async def _create_backup(self, args: Any, storage: StorageManager) -> int:
        """Create a backup."""
        backup_path = await storage.backup(args.destination, args.name)
        print(f"Created backup: {backup_path}")
        return 0

    async def _restore_backup(self, args: Any, storage: StorageManager) -> int:
        """Restore from a backup."""
        if not args.force:
            response = input(f"Are you sure you want to restore from {args.source}? This will overwrite existing data. (y/N): ")
            if response.lower() != "y":
                print("Restore cancelled.")
                return 0
        
        await storage.restore(args.source)
        print(f"Restored from backup: {args.source}")
        return 0

    async def _list_backups(self, args: Any, storage: StorageManager) -> int:
        """List available backups."""
        backup_dir = Path(args.directory)
        
        if not backup_dir.exists():
            print(f"Backup directory not found: {backup_dir}")
            return 1
        
        backups = list(backup_dir.glob("liftra_backup_*.db"))
        
        if not backups:
            print("No backups found.")
            return 0
        
        print(f"Found {len(backups)} backups:")
        for backup in sorted(backups, reverse=True):
            size = backup.stat().st_size
            print(f"  {backup.name} ({size} bytes)")
        
        return 0

    async def _report_balance(self, args: Any, storage: StorageManager) -> int:
        """Show account balances report."""
        if args.account:
            # Single account
            account_data = await storage.get("Account", args.account)
            account = Account.from_dict(account_data)
            
            print(f"Account Balance: {account.name}")
            print(f"  Current Balance: {account.current_balance or 0} {account.currency_code}")
            if account.available_balance:
                print(f"  Available Balance: {account.available_balance} {account.currency_code}")
        else:
            # All accounts
            query = Query(entity_type="Account")
            result = await storage.list("Account", query)
            
            print("Account Balances:")
            total_balance = Decimal(0)
            
            for account_data in result.items:
                account = Account.from_dict(account_data)
                balance = account.current_balance or Decimal(0)
                total_balance += balance
                print(f"  {account.name}: {balance} {account.currency_code}")
            
            print(f"\nTotal: {total_balance} GBP")
        
        return 0

    async def _report_transactions(self, args: Any, storage: StorageManager) -> int:
        """Show transaction report."""
        filters: dict[str, dict[str, Any]] = {}
        
        if args.account:
            filters["account_id"] = {"eq": args.account}
        
        query = Query(
            entity_type="Transaction",
            filters=filters,
            limit=100,
            order_by=[{"field": "created_at", "direction": "desc"}]
        )
        
        result = await storage.list("Transaction", query)
        
        if not result.items:
            print("No transactions found.")
            return 0
        
        print(f"Transaction Report ({result.total} transactions):")
        print()
        
        total_income = Decimal(0)
        total_expense = Decimal(0)
        
        for transaction_data in result.items:
            transaction = Transaction.from_dict(transaction_data)
            date_str = transaction.logical_date.isoformat() if transaction.logical_date else "?"
            
            if transaction.is_income:
                total_income += transaction.amount
            elif transaction.is_expense:
                total_expense += transaction.amount
            
            print(f"{date_str} | {transaction.description}")
            print(f"  {transaction.amount} {transaction.currency_code} | {transaction.transaction_type.value}")
            if args.format == "table":
                print(f"  Account: {transaction.account_id}")
                if transaction.category_id:
                    print(f"  Category: {transaction.category_id}")
                if transaction.payee_id:
                    print(f"  Payee: {transaction.payee_id}")
            print()
        
        print(f"Summary:")
        print(f"  Total Income: {total_income}")
        print(f"  Total Expense: {total_expense}")
        print(f"  Net: {total_income - total_expense}")
        
        return 0

    async def _import_data(self, args: Any, storage: StorageManager) -> int:
        """Import data from a file."""
        print(f"Import from {args.file} (format: {args.format or 'auto'})")
        print("Note: Import functionality will be implemented in a future update.")
        return 0

    async def _export_data(self, args: Any, storage: StorageManager) -> int:
        """Export data to a file."""
        print(f"Export to {args.output or 'stdout'} (format: {args.format})")
        print("Note: Export functionality will be implemented in a future update.")
        return 0


def main() -> None:
    """Main entry point for the CLI."""
    cli = CLI()
    
    # Run the CLI
    exit_code = asyncio.run(cli.run())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
