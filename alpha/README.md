# Alpha

A modular, efficient, desktop app for personal finance management, trading journal, and open position monitoring.
I needed one, and here it is.


## Features

- **Personal Finance Management**: Track expenses, income, and savings with categorization and visualization
- **Trading Journal**: Complete trade logging with search, filter, and analysis capabilities
- **Open Position Monitoring**: Real-time tracking of current positions with P&L calculations
- **Data Visualization**: Interactive charts and graphs using PyQtGraph and Matplotlib
- **Offline Capability**: Fully functional without internet connection using local SQLite database
- **Live Market Data**: Integration with yfinance (stocks/ETFs) and ccxt (crypto)

## Stack

- **Python 3.10+** - Core language
- **PySide6** - Modern Qt-based GUI framework
- **SQLite** - Local database storage
- **PyQtGraph** - High-performance interactive visualization
- **yfinance** - Stock and ETF market data
- **ccxt** - Cryptocurrency market data
- **Additional libraries**: Pandas, NumPy, Matplotlib, Seaborn, Plotly

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone or download the project
cd alpha/

# Run the setup script
python setup.py

# Launch the application
./launch_alpha.sh
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python alpha.py
```

## Project Structure

```
alpha/
├── alpha.py          # Main entry point
├── db.py             # Database operations (SQLite)
├── finance.py        # Personal finance management
├── trading.py        # Trading journal functionality
├── positions.py      # Open position tracking
├── datafetch.py      # Market data API integration
├── utils.py          # Utility functions
├── ui/               # PySide6 GUI components
│   └── __init__.py
├── config.yaml       # Application configuration
├── requirements.txt  # Python dependencies
├── setup.py          # Automated setup script
├── test_dependencies.py  # Dependency verification
└── launch_alpha.sh   # Application launcher
```

## Configuration

The application can be configured through `config.yaml`:

- **Offline Mode**: Enable/disable internet connectivity
- **UI Theme**: Dark/light mode
- **Database Settings**: Backup intervals and storage options
- **API Configuration**: Market data source settings
- **Categories**: Customize expense and income categories

## Offline Capabilities

Alpha is designed to work completely offline:

- ✅ **Local Database**: All data stored in SQLite
- ✅ **Cached Market Data**: Previous price data available offline
- ✅ **Full GUI**: Complete interface functionality
- ✅ **Calculations**: P&L and analytics work without internet
- ✅ **Data Export**: Excel and CSV export capabilities

## Dependencies Verification

Run the dependency test to ensure everything is working:

```bash
python test_dependencies.py
```

This will verify:
- GUI Framework (PySide6)
- Visualization libraries
- Data handling capabilities
- Market data APIs
- Database operations
- Packaging tools



## Key Features 

### Personal Finance
- Expense and income tracking
- Category-based organization
- Monthly/yearly summaries
- Savings projections
- "What-if" financial scenarios

### Trading Journal
- Complete trade history
- Performance analytics
- Tag-based organization
- Search and filter capabilities
- Risk management tracking

### Position Monitoring
- Real-time P&L calculations
- Multi-asset support (stocks, ETFs, crypto)
- Portfolio overview
- Performance metrics

### Data Visualization
- Interactive charts and graphs
- Trend analysis
- Performance comparisons
- Export capabilities

## Requirements

- Python 3.10 or higher
- macOS, Linux, or Windows
- 500MB+ free disk space
- Internet connection (optional, for live market data)

## Contributing

The application is built with modularity in mind. Each feature is developed as a standalone module:

- `db.py` - Database operations
- `finance.py` - Finance management
- `trading.py` - Trading functionality
- `positions.py` - Position tracking
- `datafetch.py` - Market data
- `ui/` - User interface components

## License

This project is for personal use and development.

## Support

For issues or questions:
1. Check the dependency verification: `python test_dependencies.py`
2. Review the configuration: `config.yaml`
3. Check the application logs: `alpha.log`

---

**Alpha** - comprehensive personal finance management solution. 
