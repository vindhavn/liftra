# Liftra

Helping keep track of the important things in life

## Overview

Liftra is a comprehensive personal finance tracking application designed for UK users but built to be easily adaptable to other countries' systems. It provides robust tracking for accounts, transactions, investments, taxes, pensions, and more, with a focus on security, extensibility, and cross-platform support.

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

### Additional Features (Phase 2)
- Holiday/trip/travel planning
- Shopping lists and consumable tracking
- Inventory tracking
- Task management
- Case and correspondence tracking
- Job search and application tracking

### Platform Support
- **Phase 1**: Linux (native), Android (native)
- **Phase 2**: Web interface, Windows, macOS, iOS

### Storage Options
- Local single-file storage (SQLite)
- Cloud storage (Nextcloud, Google Drive, OneDrive)
- Dedicated server (PostgreSQL)

## Architecture

```
liftra/
├── src/
│   └── liftra/
│       ├── core/           # Core domain models and business logic
│       ├── storage/       # Storage backends (SQLite, cloud, server)
│       ├── services/      # Application services
│       ├── api/           # Internal APIs
│       ├── plugins/       # Plugin system
│       └── security/      # Encryption and authentication
├── clients/
│   ├── linux/           # Linux desktop application
│   ├── android/         # Android mobile application
│   ├── web/             # Web interface
│   └── shared/          # Shared UI components
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

## Technology Stack

- **Language**: Python 3.10+
- **Packaging**: Poetry (for dependency management)
- **Database**: SQLite (local), PostgreSQL (server)
- **Encryption**: AES-256-GCM with Argon2 key derivation
- **UI Frameworks**: 
  - Linux: GTK or Qt (Python bindings)
  - Android: Native (Kotlin/Java) or cross-platform
  - Web: Modern web framework (TBD)
- **Visualization**: Matplotlib/Plotly (Python), Chart.js (Web)
- **PDF Export**: WeasyPrint or ReportLab

## Project Structure

### Epics (Major Feature Areas)
1. **Core Architecture & Project Setup** - Foundation for the entire project
2. **Data Model & Storage Layer** - Data structures and storage backends
3. **Account & Transaction Tracking** - MVP core functionality
4. **Categorization & Payee Tracking** - Organizing financial data
5. **Refund & Compensation Tracking** - UK-specific financial tracking
6. **UK Tax & Pension Tracking** - UK-specific requirements
7. **Investment Tracking** - Comprehensive investment management
8. **Multi-Currency Support** - International transaction support
9. **Bill Splitting & Debt Tracking** - Shared expense management
10. **Budget Management** - Financial planning tools
11. **Forecasting** - Future financial projections
12. **Reports & Graphs** - Data analysis and visualization
13. **Security & Data Protection** - Encryption and authentication
14. **User Interface & Cross-Platform Support** - Native applications
15. **Plugin System & Extensibility** - Extensible architecture
16. **Additional Features** - Phase 2 features

### Development Priority

See GitHub Issues for detailed task breakdown and priorities.

## Getting Started

### Prerequisites
- Python 3.10+
- Poetry (for dependency management)
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/vindhavn/liftra.git
cd liftra

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linting
poetry run ruff check
poetry run mypy .
```

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.

## Roadmap

### Phase 1: MVP (3-6 months)
- [ ] Core architecture and project setup
- [ ] Data model and storage layer
- [ ] Account and transaction tracking
- [ ] Categorization and payee tracking
- [ ] Refund and compensation tracking
- [ ] UK tax and pension tracking
- [ ] Investment tracking
- [ ] Multi-currency support
- [ ] Linux desktop application
- [ ] Android mobile application
- [ ] Basic reports and PDF export

### Phase 2: Enhanced Features (6-12 months)
- [ ] Bill splitting and debt tracking
- [ ] Budget management
- [ ] Forecasting
- [ ] Advanced reports and graphs
- [ ] Web interface
- [ ] Windows and macOS applications
- [ ] iOS application
- [ ] Plugin system
- [ ] Additional features (holiday planning, etc.)

### Phase 3: Polish and Optimization (Ongoing)
- [ ] Performance optimization
- [ ] Advanced features
- [ ] Community plugins
- [ ] Localization

## Contact

For questions or discussions, please open an issue or discussion in the GitHub repository.
