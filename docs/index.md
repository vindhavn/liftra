# Liftra - Personal Finance Tracking

**Liftra** is a comprehensive personal finance tracking application designed for UK users but built to be easily adaptable to other countries' systems. It provides robust tracking for accounts, transactions, investments, taxes, pensions, and more, with a focus on security, extensibility, and cross-platform support.

## Features

### Core Financial Tracking (MVP)
- **Account Management**: Track bank accounts, cash, and investment accounts
- **Transaction Tracking**: Record transactions with multiple dates, currencies, and custom data
- **Categorization**: Hierarchical categories with auto-categorization rules
- **Payee Management**: Track payees with location and branch information
- **Multi-Currency**: Support for multiple currencies with conversion rates
- **Refund & Compensation**: Track refunds and compensation linked to original transactions
- **UK Tax & Pension Tracking**: Income tax, National Insurance, student loans, pension contributions
- **Investment Tracking**: Contributions, fees, fund splits, and values
- **Bill Splitting**: Manage shared expenses with usage-based splitting
- **Budgets**: Flexible budgeting with various types and periods
- **Forecasts**: Project future spend, income, savings, and investments
- **Reports & Graphs**: Pre-built reports with PDF export and interactive visualizations

### Platform Support
- **Phase 1**: Linux (native), Android (native)
- **Phase 2**: Web interface, Windows, macOS, iOS

### Storage Options
- Local single-file storage (SQLite)
- Cloud storage (Nextcloud, Google Drive, OneDrive)
- Dedicated server (PostgreSQL)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/vindhavn/liftra.git
cd liftra

# Install dependencies using Poetry
poetry install

# Run the CLI
poetry run liftra --help
```

### Basic Usage

```bash
# Create an account
liftra account create --name "My Bank Account" --currency GBP

# List accounts
liftra account list

# Create a transaction
liftra transaction create --account <account-id> --amount 100.00 --description "Groceries"

# List transactions
liftra transaction list

# Generate a report
liftra report balance
```

## Project Status

This project is currently in active development. See the [Roadmap](#roadmap) section for details on planned features and release timelines.

## Getting Help

- **Documentation**: Browse the [User Guide](user-guide/installation.md) and [Developer Guide](developer-guide/architecture.md)
- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/vindhavn/liftra/issues)
- **Discussions**: Join the conversation on [GitHub Discussions](https://github.com/vindhavn/liftra/discussions)

## Contributing

We welcome contributions! Please see our [Contributing Guide](developer-guide/contributing.md) for details on how to get involved.

## License

Liftra is licensed under the MIT License. See [License](about/license.md) for details.
