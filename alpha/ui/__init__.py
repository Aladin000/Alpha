"""
ui package

This package contains all GUI (PySide6/Qt) code and widgets for the Alpha application.
Provides modular UI components for financial management, trading, and analytics.
"""

# Import main UI components for easier access
from .mainwindow import MainWindow
from .finance_page import FinancePage
from .trading_page import TradingPage
from .positions_page import PositionsPage
from .visualizations_page import VisualizationsPage

__all__ = [
    'MainWindow',
    'FinancePage', 
    'TradingPage',
    'PositionsPage',
    'VisualizationsPage'
] 