"""
Unit tests for Liftra models.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from liftra.core.models import (
    Account,
    AccountType,
    AccountStatus,
    Transaction,
    TransactionType,
    TransactionDate,
    TransactionDateType,
    TransactionStatus,
    Category,
    Payee,
    PayeeLocation,
    Tag,
    Attachment,
    Currency,
    ExchangeRate,
)


class TestAccount:
    """Tests for Account model."""

    def test_create_account(self) -> None:
        """Test creating an account."""
        account = Account(
            name="Test Account",
            account_type=AccountType.BANK,
            currency_code="GBP"
        )
        
        assert account.name == "Test Account"
        assert account.account_type == AccountType.BANK
        assert account.currency_code == "GBP"
        assert account.status == AccountStatus.ACTIVE
        assert account.is_active is True
        assert account.id is not None
        assert account.created_at is not None
        assert account.updated_at is not None

    def test_account_currency_validation(self) -> None:
        """Test that currency code is normalized to uppercase."""
        account = Account(
            name="Test Account",
            currency_code="gbp"
        )
        
        assert account.currency_code == "GBP"

    def test_account_balance_precision(self) -> None:
        """Test that balance precision is limited."""
        account = Account(
            name="Test Account",
            currency_code="GBP",
            current_balance=Decimal("123.456789")
        )
        
        assert account.current_balance == Decimal("123.4568")

    def test_account_display_name(self) -> None:
        """Test account display name."""
        account = Account(
            name="Test Account",
            account_type=AccountType.SAVINGS,
            currency_code="GBP"
        )
        
        assert account.display_name == "Test Account (savings)"


class TestTransaction:
    """Tests for Transaction model."""

    def test_create_transaction(self) -> None:
        """Test creating a transaction."""
        account_id = uuid4()
        transaction = Transaction(
            description="Test Transaction",
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("100.00"),
            currency_code="GBP",
            account_id=account_id
        )
        
        assert transaction.description == "Test Transaction"
        assert transaction.transaction_type == TransactionType.EXPENSE
        assert transaction.amount == Decimal("100.00")
        assert transaction.currency_code == "GBP"
        assert transaction.account_id == account_id
        assert transaction.status == TransactionStatus.CLEARED
        assert transaction.id is not None

    def test_transaction_currency_validation(self) -> None:
        """Test that currency code is normalized to uppercase."""
        transaction = Transaction(
            description="Test Transaction",
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("100.00"),
            currency_code="usd",
            account_id=uuid4()
        )
        
        assert transaction.currency_code == "USD"

    def test_transaction_amount_precision(self) -> None:
        """Test that amount precision is limited."""
        transaction = Transaction(
            description="Test Transaction",
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("100.123456789"),
            currency_code="GBP",
            account_id=uuid4()
        )
        
        assert transaction.amount == Decimal("100.1235")

    def test_transaction_with_dates(self) -> None:
        """Test transaction with multiple dates."""
        account_id = uuid4()
        today = date.today()
        
        transaction = Transaction(
            description="Test Transaction",
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("100.00"),
            currency_code="GBP",
            account_id=account_id,
            dates=[
                TransactionDate(
                    date_type=TransactionDateType.LOGICAL,
                    date_value=today,
                    is_primary=True
                ),
                TransactionDate(
                    date_type=TransactionDateType.CLEARING,
                    date_value=today,
                    is_primary=False
                )
            ]
        )
        
        assert len(transaction.dates) == 2
        assert transaction.logical_date == today
        assert transaction.clearing_date == today

    def test_transaction_type_properties(self) -> None:
        """Test transaction type properties."""
        account_id = uuid4()
        
        # Income transaction
        income = Transaction(
            description="Income",
            transaction_type=TransactionType.INCOME,
            amount=Decimal("100.00"),
            currency_code="GBP",
            account_id=account_id
        )
        assert income.is_income is True
        assert income.is_expense is False
        assert income.is_transfer is False
        
        # Expense transaction
        expense = Transaction(
            description="Expense",
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("50.00"),
            currency_code="GBP",
            account_id=account_id
        )
        assert expense.is_income is False
        assert expense.is_expense is True
        assert expense.is_transfer is False
        
        # Transfer transaction
        transfer = Transaction(
            description="Transfer",
            transaction_type=TransactionType.TRANSFER,
            amount=Decimal("200.00"),
            currency_code="GBP",
            account_id=account_id
        )
        assert transfer.is_income is False
        assert transfer.is_expense is False
        assert transfer.is_transfer is True


class TestCategory:
    """Tests for Category model."""

    def test_create_category(self) -> None:
        """Test creating a category."""
        category = Category(
            name="Food",
            path="Expenses/Food"
        )
        
        assert category.name == "Food"
        assert category.path == "Expenses/Food"
        assert category.is_expense is True
        assert category.is_active is True
        assert category.depth == 2
        assert category.is_root is False

    def test_category_path_validation(self) -> None:
        """Test that category path is normalized."""
        category = Category(
            name="Food",
            path="  Expenses / Food /  "
        )
        
        assert category.path == "Expenses/Food"

    def test_category_display_name(self) -> None:
        """Test category display name."""
        category = Category(
            name="Groceries",
            path="Expenses/Food"
        )
        
        assert category.display_name == "Expenses/Food/Groceries"


class TestPayee:
    """Tests for Payee model."""

    def test_create_payee(self) -> None:
        """Test creating a payee."""
        payee = Payee(
            name="Test Payee",
            is_company=True
        )
        
        assert payee.name == "Test Payee"
        assert payee.is_company is True
        assert payee.is_person is False
        assert payee.is_government is False

    def test_payee_country_validation(self) -> None:
        """Test that country code is normalized to uppercase."""
        payee = Payee(
            name="Test Payee",
            country="gb"
        )
        
        assert payee.country == "GB"

    def test_payee_display_name(self) -> None:
        """Test payee display name."""
        person = Payee(name="John Doe", is_person=True)
        assert person.display_name == "👤 John Doe"
        
        company = Payee(name="Acme Corp", is_company=True)
        assert company.display_name == "🏢 Acme Corp"
        
        government = Payee(name="HMRC", is_government=True)
        assert government.display_name == "🏛️ HMRC"


class TestCurrency:
    """Tests for Currency model."""

    def test_create_currency(self) -> None:
        """Test creating a currency."""
        currency = Currency(
            code="GBP",
            name="British Pound Sterling",
            symbol="£"
        )
        
        assert currency.code == "GBP"
        assert currency.name == "British Pound Sterling"
        assert currency.symbol == "£"
        assert currency.is_active is True

    def test_currency_code_validation(self) -> None:
        """Test that currency code is normalized to uppercase."""
        currency = Currency(
            code="gbp",
            name="British Pound Sterling"
        )
        
        assert currency.code == "GBP"

    def test_currency_display_name(self) -> None:
        """Test currency display name."""
        currency = Currency(
            code="USD",
            name="US Dollar",
            symbol="$"
        )
        
        assert currency.display_name == "$ USD"


class TestExchangeRate:
    """Tests for ExchangeRate model."""

    def test_create_exchange_rate(self) -> None:
        """Test creating an exchange rate."""
        today = date.today()
        rate = ExchangeRate(
            from_currency="GBP",
            to_currency="USD",
            rate=Decimal("1.25"),
            effective_date=today
        )
        
        assert rate.from_currency == "GBP"
        assert rate.to_currency == "USD"
        assert rate.rate == Decimal("1.25")
        assert rate.effective_date == today

    def test_exchange_rate_currency_validation(self) -> None:
        """Test that currency codes are normalized to uppercase."""
        rate = ExchangeRate(
            from_currency="gbp",
            to_currency="usd",
            rate=Decimal("1.25"),
            effective_date=date.today()
        )
        
        assert rate.from_currency == "GBP"
        assert rate.to_currency == "USD"

    def test_exchange_rate_precision(self) -> None:
        """Test that rate precision is limited."""
        rate = ExchangeRate(
            from_currency="GBP",
            to_currency="USD",
            rate=Decimal("1.23456789"),
            effective_date=date.today()
        )
        
        assert rate.rate == Decimal("1.23456789")

    def test_exchange_rate_conversion(self) -> None:
        """Test exchange rate conversion."""
        rate = ExchangeRate(
            from_currency="GBP",
            to_currency="USD",
            rate=Decimal("1.25"),
            effective_date=date.today()
        )
        
        # Convert 100 GBP to USD
        amount = Decimal("100")
        converted = rate.convert(amount, "GBP")
        assert converted == Decimal("125.00")
        
        # Convert 125 USD to GBP
        converted_back = rate.convert(Decimal("125"), "USD")
        assert converted_back == Decimal("100.00")

    def test_exchange_rate_inverse(self) -> None:
        """Test exchange rate inverse."""
        rate = ExchangeRate(
            from_currency="GBP",
            to_currency="USD",
            rate=Decimal("1.25"),
            effective_date=date.today()
        )
        
        assert rate.inverse_rate == Decimal("0.8")


class TestTag:
    """Tests for Tag model."""

    def test_create_tag(self) -> None:
        """Test creating a tag."""
        tag = Tag(
            name="Important",
            color="#FF0000",
            category="Priority"
        )
        
        assert tag.name == "Important"
        assert tag.color == "#FF0000"
        assert tag.category == "Priority"
        assert tag.is_active is True

    def test_tag_name_validation(self) -> None:
        """Test that tag name is normalized."""
        tag = Tag(name="  Important  ")
        
        assert tag.name == "Important"

    def test_tag_display_name(self) -> None:
        """Test tag display name."""
        tag = Tag(name="Important", category="Priority")
        
        assert tag.display_name == "Priority:Important"


class TestAttachment:
    """Tests for Attachment model."""

    def test_create_attachment(self) -> None:
        """Test creating an attachment."""
        attachment = Attachment(
            filename="receipt.pdf",
            mime_type="application/pdf",
            file_size=1024
        )
        
        assert attachment.filename == "receipt.pdf"
        assert attachment.mime_type == "application/pdf"
        assert attachment.file_size == 1024
        assert attachment.is_active is True

    def test_attachment_file_size_display(self) -> None:
        """Test attachment file size display."""
        # Bytes
        attachment1 = Attachment(filename="file.txt", file_size=500)
        assert attachment1.file_size_display == "500 B"
        
        # KB
        attachment2 = Attachment(filename="file.txt", file_size=1536)
        assert attachment2.file_size_display == "1.5 KB"
        
        # MB
        attachment3 = Attachment(filename="file.txt", file_size=1572864)
        assert attachment3.file_size_display == "1.5 MB"
        
        # GB
        attachment4 = Attachment(filename="file.txt", file_size=1610612736)
        assert attachment4.file_size_display == "1.5 GB"
