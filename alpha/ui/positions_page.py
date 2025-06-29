"""
positions_page.py

Open Positions page UI for the Alpha application.
Handles the user interface for portfolio tracking and live position monitoring.
Integrates with OpenPositions business logic while maintaining separation of concerns.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QGroupBox, 
    QFormLayout, QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, 
    QTextEdit, QSplitter, QProgressBar, QScrollArea, QMessageBox,
    QHeaderView, QAbstractItemView, QFrame, QDialog
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

# Import business logic
from positions import OpenPositions, PositionsError
from db import AlphaDatabase

# Configure logging
logger = logging.getLogger(__name__)


class PositionsPage(QWidget):
    """
    Open Positions management page.
    
    Provides UI for:
    - Viewing current positions with live prices
    - Portfolio allocation and performance
    - P&L tracking and analytics
    - Position management and alerts
    
    Integrates with OpenPositions business logic while maintaining
    strict separation between UI and business logic.
    """
    
    # Signals for data updates
    data_updated = Signal()
    
    def __init__(self, open_positions: Optional[OpenPositions] = None):
        """
        Initialize the Open Positions page.
        
        Args:
            open_positions: OpenPositions instance for business logic
        """
        super().__init__()
        
        # Store business logic reference
        self.open_positions = open_positions
        
        # Data storage for tables
        self.positions_data = []
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_live_data)
        self.auto_refresh_enabled = False
        
        self._setup_ui()
        
        # Load initial data if business logic is available
        if self.open_positions:
            self.refresh_data()
        
        logger.info("Open Positions page initialized")
    
    def set_open_positions(self, open_positions: OpenPositions):
        """Set the OpenPositions instance for business logic operations."""
        self.open_positions = open_positions
        self.refresh_data()
    
    def _setup_ui(self):
        """Set up the main UI layout and components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Page title
        title_label = QLabel("Open Positions & Portfolio Tracking")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create tab widget for different position views
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Add tabs
        self._setup_positions_tab()
        self._setup_portfolio_tab()
        self._setup_performance_tab()
    
    def _setup_positions_tab(self):
        """Set up the positions overview tab."""
        positions_widget = QWidget()
        layout = QVBoxLayout(positions_widget)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Current Positions")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # CRUD buttons
        self.add_position_btn = QPushButton("Add Position")
        self.add_position_btn.clicked.connect(self._add_position)
        header_layout.addWidget(self.add_position_btn)
        
        self.edit_position_btn = QPushButton("Edit Position")
        self.edit_position_btn.clicked.connect(self._edit_position)
        self.edit_position_btn.setEnabled(False)
        header_layout.addWidget(self.edit_position_btn)
        
        self.delete_position_btn = QPushButton("Delete Position")
        self.delete_position_btn.clicked.connect(self._delete_position)
        self.delete_position_btn.setEnabled(False)
        header_layout.addWidget(self.delete_position_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        header_layout.addWidget(separator)
        
        # Control buttons
        self.refresh_prices_btn = QPushButton("Refresh Prices")
        self.refresh_prices_btn.clicked.connect(self.refresh_live_data)
        header_layout.addWidget(self.refresh_prices_btn)
        
        self.auto_refresh_btn = QPushButton("Auto-Refresh OFF")
        self.auto_refresh_btn.clicked.connect(self._toggle_auto_refresh)
        header_layout.addWidget(self.auto_refresh_btn)
        
        self.refresh_positions_btn = QPushButton("Refresh")
        self.refresh_positions_btn.clicked.connect(self.refresh_positions)
        header_layout.addWidget(self.refresh_positions_btn)
        
        layout.addLayout(header_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Symbol filter
        filter_layout.addWidget(QLabel("Symbol:"))
        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("Filter by symbol...")
        self.symbol_filter.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.symbol_filter)
        
        # Asset type filter
        filter_layout.addWidget(QLabel("Asset Type:"))
        self.asset_type_filter = QComboBox()
        self.asset_type_filter.addItem("All")
        self.asset_type_filter.addItems(["stock", "crypto", "etf", "forex", "commodity", "bond", "option", "future"])
        self.asset_type_filter.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.asset_type_filter)
        
        # Clear filters button
        clear_filters_btn = QPushButton("Clear Filters")
        clear_filters_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(clear_filters_btn)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Status label
        self.status_label = QLabel("Ready to load positions...")
        self.status_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Positions table
        self.positions_table = QTableWidget()
        self.positions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.positions_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.positions_table.setAlternatingRowColors(True)
        self.positions_table.setSortingEnabled(True)
        
        # Connect selection changed signal
        self.positions_table.selectionModel().selectionChanged.connect(self._on_position_selection_changed)
        
        # Table headers
        headers = [
            "ID", "Symbol", "Asset Type", "Entry Date", "Entry Price", "Quantity", 
            "Entry Value", "Live Price", "Current Value", "P&L", "P&L %", "Price Change %", "Last Updated"
        ]
        self.positions_table.setColumnCount(len(headers))
        self.positions_table.setHorizontalHeaderLabels(headers)
        
        # Hide ID column
        self.positions_table.setColumnHidden(0, True)
        
        # Resize columns
        header = self.positions_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Symbol
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Asset Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Entry Date
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Entry Price
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Quantity
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Entry Value
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Live Price
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Current Value
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # P&L
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents) # P&L %
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.ResizeToContents) # Price Change %
        header.setSectionResizeMode(12, QHeaderView.ResizeMode.Stretch)          # Last Updated
        
        layout.addWidget(self.positions_table)
        
        # Add to tab widget
        self.tab_widget.addTab(positions_widget, "🎯 Positions")
    
    def _setup_portfolio_tab(self):
        """Set up the portfolio overview tab."""
        portfolio_widget = QWidget()
        layout = QVBoxLayout(portfolio_widget)
        
        # Portfolio section header
        header_label = QLabel("Portfolio Overview")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Portfolio content
        self.portfolio_content = QLabel("Loading portfolio overview...")
        self.portfolio_content.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.portfolio_content.setWordWrap(True)
        self.portfolio_content.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.portfolio_content)
        
        # Refresh button
        refresh_portfolio_btn = QPushButton("Refresh Portfolio")
        refresh_portfolio_btn.clicked.connect(self.refresh_portfolio)
        layout.addWidget(refresh_portfolio_btn)
        
        # Add to tab widget
        self.tab_widget.addTab(portfolio_widget, "📊 Portfolio")
    
    def _setup_performance_tab(self):
        """Set up the performance tracking tab."""
        performance_widget = QWidget()
        layout = QVBoxLayout(performance_widget)
        
        # Performance section header
        header_label = QLabel("Performance Tracking")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Performance content
        self.performance_content = QLabel("Loading performance metrics...")
        self.performance_content.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.performance_content.setWordWrap(True)
        self.performance_content.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.performance_content)
        
        # Refresh button
        refresh_performance_btn = QPushButton("Refresh Performance")
        refresh_performance_btn.clicked.connect(self.refresh_performance)
        layout.addWidget(refresh_performance_btn)
        
        # Add to tab widget
        self.tab_widget.addTab(performance_widget, "📈 Performance")
    
    def _toggle_auto_refresh(self):
        """Toggle auto-refresh for live prices."""
        if self.auto_refresh_enabled:
            self.refresh_timer.stop()
            self.auto_refresh_enabled = False
            self.auto_refresh_btn.setText("Auto-Refresh OFF")
            self.status_label.setText("Auto-refresh disabled")
            logger.info("Auto-refresh disabled")
        else:
            self.refresh_timer.start(30000)  # Refresh every 30 seconds
            self.auto_refresh_enabled = True
            self.auto_refresh_btn.setText("Auto-Refresh ON")
            self.status_label.setText("Auto-refresh enabled (30s interval)")
            logger.info("Auto-refresh enabled")
    
    def _apply_filters(self):
        """Apply filters to the positions table."""
        if not self.positions_data:
            return
        
        symbol_filter = self.symbol_filter.text().strip().upper()
        asset_type_filter = self.asset_type_filter.currentText()
        
        # Filter the data
        filtered_data = []
        for position in self.positions_data:
            # Symbol filter
            if symbol_filter and symbol_filter not in position.get('symbol', '').upper():
                continue
            
            # Asset type filter
            if asset_type_filter != "All" and position.get('asset_type', '') != asset_type_filter:
                continue
            
            filtered_data.append(position)
        
        # Update the table with filtered data
        self._populate_positions_table(filtered_data)
        logger.info(f"Applied filters: {len(filtered_data)}/{len(self.positions_data)} positions shown")
    
    def _clear_filters(self):
        """Clear all filters and show all positions."""
        self.symbol_filter.clear()
        self.asset_type_filter.setCurrentIndex(0)  # "All"
        self._populate_positions_table(self.positions_data)
    
    def refresh_positions(self):
        """Refresh the positions table with current data."""
        if not self.open_positions:
            return
        
        try:
            self.positions_data = self.open_positions.get_all_positions()
            self._apply_filters()  # This will populate the table with current filters
            self.status_label.setText(f"Loaded {len(self.positions_data)} positions")
            logger.info(f"Refreshed positions table with {len(self.positions_data)} records")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh positions: {str(e)}")
            logger.error(f"Failed to refresh positions: {e}")
    
    def refresh_live_data(self):
        """Refresh positions with live prices and P&L calculations."""
        if not self.open_positions:
            self.status_label.setText("Open Positions service not available")
            return
        
        try:
            self.status_label.setText("Fetching live prices...")
            
            # Get positions with live prices
            self.positions_data = self.open_positions.get_all_positions_with_live_prices()
            self._apply_filters()  # This will populate the table with current filters
            
            # Count successful price fetches
            successful_fetches = sum(1 for pos in self.positions_data if pos.get('live_price') is not None)
            total_positions = len(self.positions_data)
            
            self.status_label.setText(
                f"Updated {successful_fetches}/{total_positions} positions with live prices"
            )
            logger.info(f"Refreshed {successful_fetches}/{total_positions} positions with live data")
            
        except Exception as e:
            error_msg = f"Failed to refresh live data: {str(e)}"
            self.status_label.setText(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(f"Failed to refresh live data: {e}")
    
    def refresh_portfolio(self):
        """Refresh the portfolio overview."""
        if not self.open_positions:
            self.portfolio_content.setText("Open Positions service not available")
            return
        
        try:
            # Get portfolio P&L
            portfolio_pnl = self.open_positions.calculate_portfolio_pnl()
            
            # Get positions summary
            positions_summary = self.open_positions.get_positions_summary()
            
            # Format portfolio text
            portfolio_text = f"""PORTFOLIO OVERVIEW
============================================

PORTFOLIO VALUE:
• Total Entry Value:    ${portfolio_pnl.get('total_entry_value', 0):,.2f}
• Total Current Value:  ${portfolio_pnl.get('total_current_value', 0):,.2f}
• Total Unrealized P&L: ${portfolio_pnl.get('total_unrealized_pnl', 0):,.2f}
• Portfolio Return:     {portfolio_pnl.get('portfolio_return_percent', 0):+.2f}%

PORTFOLIO BREAKDOWN:
• Total Positions:      {positions_summary.get('total_positions', 0)}
• Successful Fetches:   {positions_summary.get('successful_fetches', 0)}
• Failed Fetches:       {positions_summary.get('failed_fetches', 0)}

ASSET ALLOCATION:
"""
            
            # Asset type allocation
            asset_allocation = positions_summary.get('asset_allocation', {})
            for asset_type, data in asset_allocation.items():
                value = data.get('total_value', 0)
                percentage = data.get('percentage', 0)
                portfolio_text += f"• {asset_type.upper():<12}: ${value:>12,.2f} ({percentage:>5.1f}%)\n"
            
            portfolio_text += "\nTOP POSITIONS BY VALUE:\n"
            top_positions = positions_summary.get('top_positions', [])
            for pos in top_positions[:5]:
                symbol = pos.get('symbol', 'N/A')
                current_value = pos.get('current_value', 0)
                pnl_percent = pos.get('unrealized_pnl_percent', 0)
                portfolio_text += f"• {symbol:<12}: ${current_value:>12,.2f} ({pnl_percent:+5.1f}%)\n"
            
            self.portfolio_content.setText(portfolio_text)
            logger.info("Refreshed portfolio overview")
            
        except Exception as e:
            error_text = f"Error loading portfolio overview: {str(e)}"
            self.portfolio_content.setText(error_text)
            logger.error(f"Failed to refresh portfolio: {e}")
    
    def refresh_performance(self):
        """Refresh the performance metrics."""
        if not self.open_positions:
            self.performance_content.setText("Open Positions service not available")
            return
        
        try:
            # Get top performers
            top_performers = self.open_positions.get_top_performers(limit=10)
            
            # Get portfolio P&L
            portfolio_pnl = self.open_positions.calculate_portfolio_pnl()
            
            # Format performance text
            performance_text = f"""PERFORMANCE METRICS
============================================

OVERALL PERFORMANCE:
• Total Unrealized P&L: ${portfolio_pnl.get('total_unrealized_pnl', 0):,.2f}
• Portfolio Return:     {portfolio_pnl.get('portfolio_return_percent', 0):+.2f}%
• Best Performer:       {portfolio_pnl.get('best_performer', 'N/A')}
• Worst Performer:      {portfolio_pnl.get('worst_performer', 'N/A')}

TOP PERFORMERS (by P&L %):
"""
            
            for i, pos in enumerate(top_performers, 1):
                symbol = pos.get('symbol', 'N/A')
                pnl = pos.get('unrealized_pnl', 0)
                pnl_percent = pos.get('unrealized_pnl_percent', 0)
                live_price = pos.get('live_price', 0)
                
                status = "📈" if pnl >= 0 else "📉"
                performance_text += f"{i:2d}. {status} {symbol:<8}: ${pnl:>8,.2f} ({pnl_percent:+6.1f}%)"
                
                if live_price:
                    performance_text += f" @ ${live_price:.2f}\n"
                else:
                    performance_text += " [Price N/A]\n"
            
            if not top_performers:
                performance_text += "• No performance data available\n"
            
            performance_text += f"\nRISK METRICS:\n"
            performance_text += f"• Positions with P&L data: {len([p for p in top_performers if p.get('live_price')])}\n"
            performance_text += f"• Positions missing prices: {len([p for p in top_performers if not p.get('live_price')])}\n"
            
            # Calculate basic statistics
            profitable_positions = [p for p in top_performers if p.get('unrealized_pnl', 0) > 0]
            losing_positions = [p for p in top_performers if p.get('unrealized_pnl', 0) < 0]
            
            performance_text += f"• Profitable positions: {len(profitable_positions)}\n"
            performance_text += f"• Losing positions: {len(losing_positions)}\n"
            
            if top_performers:
                win_rate = (len(profitable_positions) / len(top_performers)) * 100
                performance_text += f"• Win rate: {win_rate:.1f}%\n"
            
            self.performance_content.setText(performance_text)
            logger.info("Refreshed performance metrics")
            
        except Exception as e:
            error_text = f"Error loading performance metrics: {str(e)}"
            self.performance_content.setText(error_text)
            logger.error(f"Failed to refresh performance: {e}")
    
    def _populate_positions_table(self, positions_data: List[Dict[str, Any]]):
        """Populate the positions table with given data."""
        self.positions_table.setRowCount(len(positions_data))
        
        for row, position in enumerate(positions_data):
            # ID (hidden)
            self.positions_table.setItem(row, 0, QTableWidgetItem(str(position['id'])))
            
            # Symbol
            self.positions_table.setItem(row, 1, QTableWidgetItem(position['symbol']))
            
            # Asset Type
            self.positions_table.setItem(row, 2, QTableWidgetItem(position['asset_type'].upper()))
            
            # Entry Date
            self.positions_table.setItem(row, 3, QTableWidgetItem(position['entry_date']))
            
            # Entry Price
            entry_price_item = QTableWidgetItem(f"${position['entry_price']:.4f}")
            entry_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.positions_table.setItem(row, 4, entry_price_item)
            
            # Quantity
            qty_item = QTableWidgetItem(f"{position['quantity']:.4f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.positions_table.setItem(row, 5, qty_item)
            
            # Entry Value
            entry_value = position.get('entry_value', position['entry_price'] * position['quantity'])
            entry_value_item = QTableWidgetItem(f"${entry_value:,.2f}")
            entry_value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.positions_table.setItem(row, 6, entry_value_item)
            
            # Live Price
            live_price = position.get('live_price')
            if live_price is not None:
                live_price_item = QTableWidgetItem(f"${live_price:.4f}")
                live_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # Color code based on price change
                price_change_percent = position.get('price_change_percent', 0)
                if price_change_percent > 0:
                    live_price_item.setBackground(QColor(220, 255, 220))  # Light green
                elif price_change_percent < 0:
                    live_price_item.setBackground(QColor(255, 220, 220))  # Light red
                
                self.positions_table.setItem(row, 7, live_price_item)
            else:
                error_item = QTableWidgetItem("N/A")
                error_item.setBackground(QColor(240, 240, 240))  # Light gray
                self.positions_table.setItem(row, 7, error_item)
            
            # Current Value
            current_value = position.get('current_value')
            if current_value is not None:
                current_value_item = QTableWidgetItem(f"${current_value:,.2f}")
                current_value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.positions_table.setItem(row, 8, current_value_item)
            else:
                self.positions_table.setItem(row, 8, QTableWidgetItem("N/A"))
            
            # P&L
            unrealized_pnl = position.get('unrealized_pnl')
            if unrealized_pnl is not None:
                pnl_item = QTableWidgetItem(f"${unrealized_pnl:+,.2f}")
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # Color code P&L
                if unrealized_pnl > 0:
                    pnl_item.setBackground(QColor(220, 255, 220))  # Light green
                elif unrealized_pnl < 0:
                    pnl_item.setBackground(QColor(255, 220, 220))  # Light red
                
                self.positions_table.setItem(row, 9, pnl_item)
            else:
                self.positions_table.setItem(row, 9, QTableWidgetItem("N/A"))
            
            # P&L %
            unrealized_pnl_percent = position.get('unrealized_pnl_percent')
            if unrealized_pnl_percent is not None:
                pnl_percent_item = QTableWidgetItem(f"{unrealized_pnl_percent:+.2f}%")
                pnl_percent_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # Color code P&L %
                if unrealized_pnl_percent > 0:
                    pnl_percent_item.setBackground(QColor(220, 255, 220))  # Light green
                elif unrealized_pnl_percent < 0:
                    pnl_percent_item.setBackground(QColor(255, 220, 220))  # Light red
                
                self.positions_table.setItem(row, 10, pnl_percent_item)
            else:
                self.positions_table.setItem(row, 10, QTableWidgetItem("N/A"))
            
            # Price Change %
            price_change_percent = position.get('price_change_percent')
            if price_change_percent is not None:
                price_change_item = QTableWidgetItem(f"{price_change_percent:+.2f}%")
                price_change_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.positions_table.setItem(row, 11, price_change_item)
            else:
                self.positions_table.setItem(row, 11, QTableWidgetItem("N/A"))
            
            # Last Updated
            last_updated = position.get('last_updated', 'Never')
            if last_updated != 'Never' and 'T' in last_updated:
                # Format timestamp
                try:
                    dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%H:%M:%S')
                    self.positions_table.setItem(row, 12, QTableWidgetItem(formatted_time))
                except:
                    self.positions_table.setItem(row, 12, QTableWidgetItem(last_updated))
            else:
                self.positions_table.setItem(row, 12, QTableWidgetItem(last_updated))
    
    def refresh_data(self):
        """Refresh all data (positions, portfolio, and performance)."""
        self.refresh_positions()
        self.refresh_portfolio()
        self.refresh_performance()
        self.data_updated.emit()
        logger.info("Refreshed all Open Positions data")
    
    def closeEvent(self, event):
        """Handle close event to stop auto-refresh timer."""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
        event.accept()
    
    # ==================== CRUD METHODS ====================
    
    def _on_position_selection_changed(self):
        """Handle position selection change in table."""
        selected_rows = self.positions_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        # Enable/disable edit and delete buttons based on selection
        self.edit_position_btn.setEnabled(has_selection)
        self.delete_position_btn.setEnabled(has_selection)
    
    def _add_position(self):
        """Show dialog to add a new position."""
        if not self.open_positions:
            QMessageBox.warning(self, "Error", "Open Positions service not available")
            return
        
        dialog = AddPositionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            position_data = dialog.get_position_data()
            
            try:
                position_id = self.open_positions.add_position(
                    symbol=position_data['symbol'],
                    asset_type=position_data['asset_type'],
                    entry_date=position_data['entry_date'],
                    entry_price=position_data['entry_price'],
                    quantity=position_data['quantity']
                )
                
                QMessageBox.information(self, "Success", f"Position added successfully (ID: {position_id})")
                self.refresh_positions()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add position: {str(e)}")
    
    def _edit_position(self):
        """Show dialog to edit the selected position."""
        if not self.open_positions:
            QMessageBox.warning(self, "Error", "Open Positions service not available")
            return
        
        selected_rows = self.positions_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a position to edit")
            return
        
        # Get position ID from the selected row
        row = selected_rows[0].row()
        position_id = int(self.positions_table.item(row, 0).text())
        
        # Get current position data
        try:
            position = self.open_positions.get_position(position_id)
            if not position:
                QMessageBox.warning(self, "Error", "Position not found")
                return
            
            dialog = EditPositionDialog(position, self)
            if dialog.exec() == QDialog.Accepted:
                position_data = dialog.get_position_data()
                
                success = self.open_positions.update_position(
                    position_id=position_id,
                    symbol=position_data['symbol'],
                    asset_type=position_data['asset_type'],
                    entry_date=position_data['entry_date'],
                    entry_price=position_data['entry_price'],
                    quantity=position_data['quantity']
                )
                
                if success:
                    QMessageBox.information(self, "Success", "Position updated successfully")
                    self.refresh_positions()
                else:
                    QMessageBox.warning(self, "Warning", "Position update failed")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit position: {str(e)}")
    
    def _delete_position(self):
        """Delete the selected position."""
        if not self.open_positions:
            QMessageBox.warning(self, "Error", "Open Positions service not available")
            return
        
        selected_rows = self.positions_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a position to delete")
            return
        
        # Get position info from the selected row
        row = selected_rows[0].row()
        position_id = int(self.positions_table.item(row, 0).text())
        symbol = self.positions_table.item(row, 1).text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete the position for {symbol}?\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.open_positions.delete_position(position_id)
                
                if success:
                    QMessageBox.information(self, "Success", f"Position {symbol} deleted successfully")
                    self.refresh_positions()
                else:
                    QMessageBox.warning(self, "Warning", "Position deletion failed")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete position: {str(e)}")


# ==================== DIALOG CLASSES ====================

class AddPositionDialog(QDialog):
    """Dialog for adding a new position."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Position")
        self.setModal(True)
        self.resize(450, 350)
        
        # Center the dialog on parent
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - 450) // 2
            y = parent_rect.y() + (parent_rect.height() - 350) // 2
            self.move(x, y)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Symbol
        self.symbol_edit = QLineEdit()
        self.symbol_edit.setPlaceholderText("e.g., AAPL, BTC")
        form_layout.addRow("Symbol:", self.symbol_edit)
        
        # Asset Type
        self.asset_type_combo = QComboBox()
        self.asset_type_combo.addItems(["stock", "crypto", "etf", "forex", "commodity", "bond", "option", "future"])
        form_layout.addRow("Asset Type:", self.asset_type_combo)
        
        # Entry Date
        self.entry_date_edit = QDateEdit()
        self.entry_date_edit.setDate(datetime.now().date())
        self.entry_date_edit.setCalendarPopup(True)
        form_layout.addRow("Entry Date:", self.entry_date_edit)
        
        # Entry Price
        self.entry_price_spin = QDoubleSpinBox()
        self.entry_price_spin.setRange(0.01, 999999.99)
        self.entry_price_spin.setDecimals(2)
        self.entry_price_spin.setValue(100.00)
        form_layout.addRow("Entry Price:", self.entry_price_spin)
        
        # Quantity
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.01, 999999.99)
        self.quantity_spin.setDecimals(4)
        self.quantity_spin.setValue(1.0)
        form_layout.addRow("Quantity:", self.quantity_spin)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_btn = QPushButton("Add Position")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def get_position_data(self):
        """Get the position data from the form."""
        return {
            'symbol': self.symbol_edit.text().strip().upper(),
            'asset_type': self.asset_type_combo.currentText(),
            'entry_date': self.entry_date_edit.date().toString('yyyy-MM-dd'),
            'entry_price': self.entry_price_spin.value(),
            'quantity': self.quantity_spin.value()
        }
    
    def accept(self):
        """Validate and accept the dialog."""
        if not self.symbol_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a symbol")
            return
        
        if self.entry_price_spin.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Entry price must be greater than 0")
            return
        
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0")
            return
        
        super().accept()


class EditPositionDialog(QDialog):
    """Dialog for editing an existing position."""
    
    def __init__(self, position_data, parent=None):
        super().__init__(parent)
        self.position_data = position_data
        self.setWindowTitle(f"Edit Position - {position_data['symbol']}")
        self.setModal(True)
        self.resize(450, 350)
        
        # Center the dialog on parent
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - 450) // 2
            y = parent_rect.y() + (parent_rect.height() - 350) // 2
            self.move(x, y)
        
        self._setup_ui()
        self._populate_form()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Symbol
        self.symbol_edit = QLineEdit()
        form_layout.addRow("Symbol:", self.symbol_edit)
        
        # Asset Type
        self.asset_type_combo = QComboBox()
        self.asset_type_combo.addItems(["stock", "crypto", "etf", "forex", "commodity", "bond", "option", "future"])
        form_layout.addRow("Asset Type:", self.asset_type_combo)
        
        # Entry Date
        self.entry_date_edit = QDateEdit()
        self.entry_date_edit.setCalendarPopup(True)
        form_layout.addRow("Entry Date:", self.entry_date_edit)
        
        # Entry Price
        self.entry_price_spin = QDoubleSpinBox()
        self.entry_price_spin.setRange(0.01, 999999.99)
        self.entry_price_spin.setDecimals(2)
        form_layout.addRow("Entry Price:", self.entry_price_spin)
        
        # Quantity
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.01, 999999.99)
        self.quantity_spin.setDecimals(4)
        form_layout.addRow("Quantity:", self.quantity_spin)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_btn = QPushButton("Update Position")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _populate_form(self):
        """Populate the form with existing position data."""
        self.symbol_edit.setText(self.position_data['symbol'])
        
        # Set asset type
        index = self.asset_type_combo.findText(self.position_data['asset_type'])
        if index >= 0:
            self.asset_type_combo.setCurrentIndex(index)
        
        # Set entry date
        entry_date = datetime.strptime(self.position_data['entry_date'], '%Y-%m-%d').date()
        self.entry_date_edit.setDate(entry_date)
        
        # Set entry price and quantity
        self.entry_price_spin.setValue(float(self.position_data['entry_price']))
        self.quantity_spin.setValue(float(self.position_data['quantity']))
    
    def get_position_data(self):
        """Get the updated position data from the form."""
        return {
            'symbol': self.symbol_edit.text().strip().upper(),
            'asset_type': self.asset_type_combo.currentText(),
            'entry_date': self.entry_date_edit.date().toString('yyyy-MM-dd'),
            'entry_price': self.entry_price_spin.value(),
            'quantity': self.quantity_spin.value()
        }
    
    def accept(self):
        """Validate and accept the dialog."""
        if not self.symbol_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a symbol")
            return
        
        if self.entry_price_spin.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Entry price must be greater than 0")
            return
        
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0")
            return
        
        super().accept() 