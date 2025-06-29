"""
mainwindow.py

Main window class for the Alpha application.
Provides the primary interface with tab-based navigation to different modules.
"""

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStatusBar, QMenuBar, QToolBar, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QFont
import sys
import logging

# Import page modules
from .finance_page import FinancePage
from .trading_page import TradingPage
from .positions_page import PositionsPage
from .visualizations_page import VisualizationsPage

# Configure logging
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window for Alpha personal finance application.
    
    Provides a tab-based interface for accessing different modules:
    - Dashboard: Overview and summary information
    - Personal Finance: Expense and savings management
    - Trading Journal: Trade logging and analysis
    - Open Positions: Portfolio tracking with live data
    - Visualizations: Charts and financial simulations
    """
    
    def __init__(self):
        """Initialize the main window with all UI components."""
        super().__init__()
        
        # Initialize business logic dependencies
        self._init_business_logic()
        
        # Window properties
        self.setWindowTitle("Alpha")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # Initialize UI components
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        
        # Set up window state
        self._setup_window_state()
        
        logger.info("Main window initialized successfully")
    
    def _init_business_logic(self):
        """Initialize business logic components."""
        try:
            # Import business logic modules
            from db import AlphaDatabase
            from finance import PersonalFinance
            from trading import TradingJournal
            from positions import OpenPositions
            
            # Initialize database
            self.database = AlphaDatabase()
            logger.info("Database initialized")
            
            # Initialize business logic services
            self.personal_finance = PersonalFinance(self.database)
            self.trading_journal = TradingJournal(self.database)
            self.open_positions = OpenPositions(self.database)
            logger.info("Personal Finance service initialized")
            logger.info("Trading Journal service initialized")
            logger.info("Open Positions service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize business logic: {e}")
            self.database = None
            self.personal_finance = None
            self.trading_journal = None
            self.open_positions = None
    
    def _setup_ui(self):
        """Set up the main user interface with tab widget."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(False)
        
        # Add tabs
        self._setup_tabs()
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _setup_tabs(self):
        """Create and add all application tabs."""
        # Dashboard tab
        self.dashboard_widget = self._create_dashboard_widget()
        self.tab_widget.addTab(self.dashboard_widget, "📊 Dashboard")
        
        # Personal Finance tab
        self.finance_page = FinancePage(self.personal_finance)
        self.tab_widget.addTab(self.finance_page, "💰 Personal Finance")
        
        # Trading Journal tab
        self.trading_page = TradingPage(self.trading_journal)
        self.tab_widget.addTab(self.trading_page, "📈 Trading Journal")
        
        # Open Positions tab
        self.positions_page = PositionsPage(self.open_positions)
        self.tab_widget.addTab(self.positions_page, "🎯 Open Positions")
        
        # Visualizations tab
        self.visualizations_page = VisualizationsPage(
            personal_finance=self.personal_finance,
            trading_journal=self.trading_journal,
            open_positions=self.open_positions
        )
        self.tab_widget.addTab(self.visualizations_page, "📊 Analytics")
        
        logger.info("All tabs created and added to tab widget")
    
    def _create_dashboard_widget(self):
        """Create the dashboard overview page."""
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title = QLabel("Alpha Dashboard")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Personal Finance Management System")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #666666; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Welcome message
        welcome = QLabel(
            "Welcome to Alpha! Use the tabs above to navigate between different modules:\n\n"
            "💰 Personal Finance - Manage expenses and savings\n"
            "📈 Trading Journal - Track your trades and performance\n"
            "🎯 Open Positions - Monitor your portfolio with live data\n"
            "📊 Analytics - Visualize data and run financial simulations"
        )
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setWordWrap(True)
        welcome.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin: 20px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(welcome)
        
        # Status info (placeholder for future dashboard content)
        status_info = QLabel("Dashboard content will be added in future updates")
        status_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_info.setStyleSheet("color: #6c757d; font-style: italic; margin-top: 20px;")
        layout.addWidget(status_info)
        
        return dashboard
    
    def _setup_menu_bar(self):
        """Set up the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Database actions
        refresh_action = QAction("&Refresh Data", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("Refresh all data from database")
        refresh_action.triggered.connect(self._refresh_data)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Tab navigation actions
        for i in range(5):  # We have 5 tabs
            action = QAction(f"Go to Tab {i+1}", self)
            action.setShortcut(f"Ctrl+{i+1}")
            action.triggered.connect(lambda checked, idx=i: self.tab_widget.setCurrentIndex(idx))
            view_menu.addAction(action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About Alpha", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Set up the main toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.setStatusTip("Refresh all data")
        refresh_action.triggered.connect(self._refresh_data)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Quick navigation actions
        dashboard_action = QAction("Dashboard", self)
        dashboard_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        toolbar.addAction(dashboard_action)
        
        finance_action = QAction("Finance", self)
        finance_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        toolbar.addAction(finance_action)
        
        trading_action = QAction("Trading", self)
        trading_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        toolbar.addAction(trading_action)
        
        positions_action = QAction("Positions", self)
        positions_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        toolbar.addAction(positions_action)
        
        analytics_action = QAction("Analytics", self)
        analytics_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
        toolbar.addAction(analytics_action)
    
    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status message
        self.status_bar.showMessage("Ready - Alpha Personal Finance Manager")
        
        # Add permanent widgets for status info
        self.connection_status = QLabel("Database: Connected")
        self.connection_status.setStyleSheet("color: green; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.connection_status)
    
    def _setup_window_state(self):
        """Set up initial window state and appearance."""
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom-color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Center the window on screen
        self._center_on_screen()
    
    def _center_on_screen(self):
        """Center the window on the screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())
    
    def _on_tab_changed(self, index):
        """Handle tab change events."""
        tab_names = ["Dashboard", "Personal Finance", "Trading Journal", "Open Positions", "Analytics"]
        if 0 <= index < len(tab_names):
            self.status_bar.showMessage(f"Switched to {tab_names[index]} tab")
            logger.info(f"User switched to {tab_names[index]} tab")
    
    def _refresh_data(self):
        """Refresh all data across the application."""
        self.status_bar.showMessage("Refreshing data...")
        
        try:
            # Refresh Personal Finance page
            if hasattr(self, 'finance_page') and self.finance_page:
                self.finance_page.refresh_data()
            
            # Refresh Trading Journal page
            if hasattr(self, 'trading_page') and self.trading_page:
                self.trading_page.refresh_data()
            
            # Refresh Open Positions page
            if hasattr(self, 'positions_page') and self.positions_page:
                self.positions_page.refresh_data()
            
            # Refresh Visualizations page
            if hasattr(self, 'visualizations_page') and self.visualizations_page:
                self.visualizations_page.refresh_data()
            
            self.status_bar.showMessage("Data refreshed successfully")
            logger.info("Data refresh completed")
            
        except Exception as e:
            self.status_bar.showMessage(f"Refresh failed: {str(e)}")
            logger.error(f"Data refresh failed: {e}")
    
    def _show_about(self):
        """Show about dialog."""
        from PySide6.QtWidgets import QMessageBox
        
        QMessageBox.about(
            self,
            "About Alpha",
            "Alpha Personal Finance Manager\n\n"
            "A comprehensive desktop application for managing personal finances,\n"
            "tracking investments, and analyzing financial data.\n\n"
            "Built with Python and PySide6."
        )
    
    def closeEvent(self, event):
        """Handle application close event."""
        logger.info("Application closing")
        event.accept() 