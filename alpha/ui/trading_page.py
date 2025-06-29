"""
trading_page.py

Trading Journal page UI for the Alpha application.
Handles the user interface for trade logging and analysis.
Integrates with TradingJournal business logic while maintaining separation of concerns.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QGroupBox, 
    QFormLayout, QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, 
    QTextEdit, QSplitter, QMessageBox, QDialog, QDialogButtonBox,
    QHeaderView, QAbstractItemView, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont, QColor
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

# Import business logic
from trading import TradingJournal, TradingJournalError
from db import AlphaDatabase

# Configure logging
logger = logging.getLogger(__name__)


class AddTradeDialog(QDialog):
    """Dialog for adding new trades."""
    
    def __init__(self, parent=None):
        """Initialize the add trade dialog."""
        super().__init__(parent)
        self.setWindowTitle("Add New Trade")
        self.setModal(True)
        self.resize(450, 400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Symbol
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("e.g., AAPL, BTC-USD")
        form_layout.addRow("Symbol:", self.symbol_input)
        
        # Asset Type
        self.asset_type_input = QComboBox()
        asset_types = ["stock", "crypto", "etf", "forex", "commodity", "bond", "option", "future"]
        self.asset_type_input.addItems(asset_types)
        form_layout.addRow("Asset Type:", self.asset_type_input)
        
        # Trade Type
        self.trade_type_input = QComboBox()
        trade_types = ["buy", "sell", "short", "cover"]
        self.trade_type_input.addItems(trade_types)
        form_layout.addRow("Trade Type:", self.trade_type_input)
        
        # Entry Date
        self.entry_date_input = QDateEdit()
        self.entry_date_input.setDate(QDate.currentDate())
        self.entry_date_input.setCalendarPopup(True)
        form_layout.addRow("Entry Date:", self.entry_date_input)
        
        # Entry Price
        self.entry_price_input = QDoubleSpinBox()
        self.entry_price_input.setRange(0.0001, 999999.99)
        self.entry_price_input.setDecimals(4)
        self.entry_price_input.setValue(1.0)
        form_layout.addRow("Entry Price ($):", self.entry_price_input)
        
        # Quantity
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.0001, 999999.99)
        self.quantity_input.setDecimals(4)
        self.quantity_input.setValue(1.0)
        form_layout.addRow("Quantity:", self.quantity_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Enter trade notes...")
        form_layout.addRow("Notes:", self.notes_input)
        
        # Tags
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Enter tags (comma-separated)...")
        form_layout.addRow("Tags:", self.tags_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_trade_data(self) -> Dict[str, Any]:
        """Get the trade data from the form."""
        return {
            'symbol': self.symbol_input.text().strip(),
            'asset_type': self.asset_type_input.currentText(),
            'trade_type': self.trade_type_input.currentText(),
            'entry_date': self.entry_date_input.date().toString('yyyy-MM-dd'),
            'entry_price': self.entry_price_input.value(),
            'quantity': self.quantity_input.value(),
            'notes': self.notes_input.toPlainText().strip(),
            'tags': self.tags_input.text().strip()
        }


class EditTradeDialog(AddTradeDialog):
    """Dialog for editing existing trades."""
    
    def __init__(self, trade_data: Dict[str, Any], parent=None):
        """Initialize the edit trade dialog with existing data."""
        super().__init__(parent)
        self.setWindowTitle("Edit Trade")
        self._populate_form(trade_data)
    
    def _populate_form(self, data: Dict[str, Any]):
        """Populate the form with existing trade data."""
        self.symbol_input.setText(data.get('symbol', ''))
        
        # Asset type
        asset_type = data.get('asset_type', '')
        index = self.asset_type_input.findText(asset_type)
        if index >= 0:
            self.asset_type_input.setCurrentIndex(index)
        
        # Trade type
        trade_type = data.get('trade_type', '')
        index = self.trade_type_input.findText(trade_type)
        if index >= 0:
            self.trade_type_input.setCurrentIndex(index)
        
        # Entry date
        date_str = data.get('entry_date', '')
        if date_str:
            date = QDate.fromString(date_str, 'yyyy-MM-dd')
            self.entry_date_input.setDate(date)
        
        self.entry_price_input.setValue(float(data.get('entry_price', 0)))
        self.quantity_input.setValue(float(data.get('quantity', 0)))
        self.notes_input.setPlainText(data.get('notes', ''))
        self.tags_input.setText(data.get('tags', ''))


class TradingPage(QWidget):
    """
    Trading Journal management page.
    
    Provides UI for:
    - Adding, editing, and viewing trades
    - Trade filtering and search
    - Performance analysis and metrics
    - Trade history and patterns
    
    Integrates with TradingJournal business logic while maintaining
    strict separation between UI and business logic.
    """
    
    # Signals for data updates
    data_updated = Signal()
    
    def __init__(self, trading_journal: Optional[TradingJournal] = None):
        """
        Initialize the Trading Journal page.
        
        Args:
            trading_journal: TradingJournal instance for business logic
        """
        super().__init__()
        
        # Store business logic reference
        self.trading_journal = trading_journal
        
        # Data storage for tables
        self.trades_data = []
        
        self._setup_ui()
        
        # Load initial data if business logic is available
        if self.trading_journal:
            self.refresh_data()
        
        logger.info("Trading Journal page initialized")
    
    def set_trading_journal(self, trading_journal: TradingJournal):
        """Set the TradingJournal instance for business logic operations."""
        self.trading_journal = trading_journal
        self.refresh_data()
    
    def _setup_ui(self):
        """Set up the main UI layout and components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Page title
        title_label = QLabel("Trading Journal")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create tab widget for different trading views
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Add tabs
        self._setup_trades_tab()
        self._setup_analysis_tab()
        self._setup_performance_tab()
    
    def _setup_trades_tab(self):
        """Set up the trades management tab."""
        trades_widget = QWidget()
        layout = QVBoxLayout(trades_widget)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Trade Management")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Control buttons
        self.add_trade_btn = QPushButton("Add Trade")
        self.add_trade_btn.clicked.connect(self._add_trade)
        header_layout.addWidget(self.add_trade_btn)
        
        self.edit_trade_btn = QPushButton("Edit Trade")
        self.edit_trade_btn.clicked.connect(self._edit_trade)
        self.edit_trade_btn.setEnabled(False)
        header_layout.addWidget(self.edit_trade_btn)
        
        self.delete_trade_btn = QPushButton("Delete Trade")
        self.delete_trade_btn.clicked.connect(self._delete_trade)
        self.delete_trade_btn.setEnabled(False)
        header_layout.addWidget(self.delete_trade_btn)
        
        self.refresh_trades_btn = QPushButton("Refresh")
        self.refresh_trades_btn.clicked.connect(self.refresh_trades)
        header_layout.addWidget(self.refresh_trades_btn)
        
        layout.addLayout(header_layout)
        
        # Search and filter controls
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
        
        # Trade type filter
        filter_layout.addWidget(QLabel("Trade Type:"))
        self.trade_type_filter = QComboBox()
        self.trade_type_filter.addItem("All")
        self.trade_type_filter.addItems(["buy", "sell", "short", "cover"])
        self.trade_type_filter.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.trade_type_filter)
        
        # Clear filters button
        clear_filters_btn = QPushButton("Clear Filters")
        clear_filters_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(clear_filters_btn)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Trades table
        self.trades_table = QTableWidget()
        self.trades_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.trades_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.trades_table.setAlternatingRowColors(True)
        self.trades_table.setSortingEnabled(True)
        
        # Table headers
        headers = ["ID", "Symbol", "Asset Type", "Trade Type", "Entry Date", "Entry Price", "Quantity", "Value", "Notes", "Tags"]
        self.trades_table.setColumnCount(len(headers))
        self.trades_table.setHorizontalHeaderLabels(headers)
        
        # Hide ID column
        self.trades_table.setColumnHidden(0, True)
        
        # Resize columns
        header = self.trades_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Symbol
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Asset Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Trade Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Entry Date
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Entry Price
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Quantity
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Value
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)           # Notes
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Tags
        
        # Connect selection changes
        self.trades_table.selectionModel().selectionChanged.connect(self._on_trade_selection_changed)
        self.trades_table.doubleClicked.connect(self._edit_trade)
        
        layout.addWidget(self.trades_table)
        
        # Add to tab widget
        self.tab_widget.addTab(trades_widget, "📝 Trades")
    
    def _setup_analysis_tab(self):
        """Set up the trading analysis tab."""
        analysis_widget = QWidget()
        layout = QVBoxLayout(analysis_widget)
        
        # Analysis section header
        header_label = QLabel("Trading Analysis")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Analysis content
        self.analysis_content = QLabel("Loading trading analysis...")
        self.analysis_content.setStyleSheet("""
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
        self.analysis_content.setWordWrap(True)
        self.analysis_content.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.analysis_content)
        
        # Refresh button
        refresh_analysis_btn = QPushButton("Refresh Analysis")
        refresh_analysis_btn.clicked.connect(self.refresh_analysis)
        layout.addWidget(refresh_analysis_btn)
        
        # Add to tab widget
        self.tab_widget.addTab(analysis_widget, "📊 Analysis")
    
    def _setup_performance_tab(self):
        """Set up the performance metrics tab."""
        performance_widget = QWidget()
        layout = QVBoxLayout(performance_widget)
        
        # Performance section header
        header_label = QLabel("Performance Metrics")
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
    
    def _on_trade_selection_changed(self):
        """Handle trade table selection changes."""
        has_selection = len(self.trades_table.selectionModel().selectedRows()) > 0
        self.edit_trade_btn.setEnabled(has_selection)
        self.delete_trade_btn.setEnabled(has_selection)
    
    def _add_trade(self):
        """Add a new trade."""
        if not self.trading_journal:
            QMessageBox.warning(self, "Error", "Trading Journal service not available")
            return
        
        dialog = AddTradeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_trade_data()
                
                # Validate required fields
                if not data['symbol']:
                    QMessageBox.warning(self, "Error", "Symbol is required")
                    return
                
                self.trading_journal.add_trade(
                    symbol=data['symbol'],
                    asset_type=data['asset_type'],
                    entry_date=data['entry_date'],
                    entry_price=data['entry_price'],
                    quantity=data['quantity'],
                    trade_type=data['trade_type'],
                    notes=data['notes'],
                    tags=data['tags']
                )
                
                self.refresh_trades()
                QMessageBox.information(self, "Success", "Trade added successfully")
                logger.info(f"Added trade: {data['symbol']} {data['trade_type']} {data['quantity']}@${data['entry_price']}")
                
            except TradingJournalError as e:
                QMessageBox.critical(self, "Error", f"Failed to add trade: {str(e)}")
                logger.error(f"Failed to add trade: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error adding trade: {e}")
    
    def _edit_trade(self):
        """Edit the selected trade."""
        if not self.trading_journal:
            QMessageBox.warning(self, "Error", "Trading Journal service not available")
            return
        
        selected_rows = self.trades_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Info", "Please select a trade to edit")
            return
        
        row = selected_rows[0].row()
        trade_id = int(self.trades_table.item(row, 0).text())
        
        # Find the trade data
        trade_data = None
        for trade in self.trades_data:
            if trade['id'] == trade_id:
                trade_data = trade
                break
        
        if not trade_data:
            QMessageBox.critical(self, "Error", "Trade data not found")
            return
        
        dialog = EditTradeDialog(trade_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_trade_data()
                
                # Validate required fields
                if not data['symbol']:
                    QMessageBox.warning(self, "Error", "Symbol is required")
                    return
                
                self.trading_journal.update_trade(
                    trade_id=trade_id,
                    symbol=data['symbol'],
                    asset_type=data['asset_type'],
                    entry_date=data['entry_date'],
                    entry_price=data['entry_price'],
                    quantity=data['quantity'],
                    trade_type=data['trade_type'],
                    notes=data['notes'],
                    tags=data['tags']
                )
                
                self.refresh_trades()
                QMessageBox.information(self, "Success", "Trade updated successfully")
                logger.info(f"Updated trade ID {trade_id}")
                
            except TradingJournalError as e:
                QMessageBox.critical(self, "Error", f"Failed to update trade: {str(e)}")
                logger.error(f"Failed to update trade: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error updating trade: {e}")
    
    def _delete_trade(self):
        """Delete the selected trade."""
        if not self.trading_journal:
            QMessageBox.warning(self, "Error", "Trading Journal service not available")
            return
        
        selected_rows = self.trades_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Info", "Please select a trade to delete")
            return
        
        row = selected_rows[0].row()
        trade_id = int(self.trades_table.item(row, 0).text())
        trade_symbol = self.trades_table.item(row, 1).text()
        trade_type = self.trades_table.item(row, 3).text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the trade:\n\n{trade_symbol} - {trade_type}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.trading_journal.delete_trade(trade_id)
                self.refresh_trades()
                QMessageBox.information(self, "Success", "Trade deleted successfully")
                logger.info(f"Deleted trade ID {trade_id}")
                
            except TradingJournalError as e:
                QMessageBox.critical(self, "Error", f"Failed to delete trade: {str(e)}")
                logger.error(f"Failed to delete trade: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error deleting trade: {e}")
    
    def _apply_filters(self):
        """Apply filters to the trades table."""
        if not self.trades_data:
            return
        
        symbol_filter = self.symbol_filter.text().strip().upper()
        asset_type_filter = self.asset_type_filter.currentText()
        trade_type_filter = self.trade_type_filter.currentText()
        
        # Filter the data
        filtered_data = []
        for trade in self.trades_data:
            # Symbol filter
            if symbol_filter and symbol_filter not in trade.get('symbol', '').upper():
                continue
            
            # Asset type filter
            if asset_type_filter != "All" and trade.get('asset_type', '') != asset_type_filter:
                continue
            
            # Trade type filter
            if trade_type_filter != "All" and trade.get('trade_type', '') != trade_type_filter:
                continue
            
            filtered_data.append(trade)
        
        # Update the table with filtered data
        self._populate_trades_table(filtered_data)
        logger.info(f"Applied filters: {len(filtered_data)}/{len(self.trades_data)} trades shown")
    
    def _clear_filters(self):
        """Clear all filters and show all trades."""
        self.symbol_filter.clear()
        self.asset_type_filter.setCurrentIndex(0)  # "All"
        self.trade_type_filter.setCurrentIndex(0)  # "All"
        self._populate_trades_table(self.trades_data)
    
    def refresh_trades(self):
        """Refresh the trades table with current data."""
        if not self.trading_journal:
            return
        
        try:
            self.trades_data = self.trading_journal.get_all_trades()
            self._apply_filters()  # This will populate the table with current filters
            logger.info(f"Refreshed trades table with {len(self.trades_data)} records")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh trades: {str(e)}")
            logger.error(f"Failed to refresh trades: {e}")
    
    def refresh_analysis(self):
        """Refresh the trading analysis."""
        if not self.trading_journal:
            self.analysis_content.setText("Trading Journal service not available")
            return
        
        try:
            # Get trade summary
            summary = self.trading_journal.get_trade_summary()
            
            # Format analysis text
            analysis_text = f"""TRADING ANALYSIS
============================================

TRADE SUMMARY:
• Total Trades: {summary.get('total_trades', 0)}
• Total Volume: ${summary.get('total_volume', 0):,.2f}
• Unique Symbols: {summary.get('unique_symbols', 0)}

ASSET TYPE BREAKDOWN:
"""
            
            asset_breakdown = summary.get('asset_type_breakdown', {})
            for asset_type, count in asset_breakdown.items():
                percentage = (count / summary.get('total_trades', 1) * 100)
                analysis_text += f"• {asset_type.upper():<12}: {count:>3} trades ({percentage:>5.1f}%)\n"
            
            analysis_text += "\nTRADE TYPE BREAKDOWN:\n"
            trade_breakdown = summary.get('trade_type_breakdown', {})
            for trade_type, count in trade_breakdown.items():
                percentage = (count / summary.get('total_trades', 1) * 100)
                analysis_text += f"• {trade_type.upper():<12}: {count:>3} trades ({percentage:>5.1f}%)\n"
            
            analysis_text += "\nTOP SYMBOLS BY VOLUME:\n"
            top_symbols = summary.get('top_symbols_by_volume', {})
            for symbol, volume in list(top_symbols.items())[:5]:
                analysis_text += f"• {symbol:<12}: ${volume:>12,.2f}\n"
            
            self.analysis_content.setText(analysis_text)
            logger.info("Refreshed trading analysis")
            
        except Exception as e:
            error_text = f"Error loading trading analysis: {str(e)}"
            self.analysis_content.setText(error_text)
            logger.error(f"Failed to refresh analysis: {e}")
    
    def refresh_performance(self):
        """Refresh the performance metrics."""
        if not self.trading_journal:
            self.performance_content.setText("Trading Journal service not available")
            return
        
        try:
            # Get trade summary for performance metrics
            summary = self.trading_journal.get_trade_summary()
            
            # Calculate additional performance metrics
            trades = self.trading_journal.get_all_trades()
            
            # Calculate total value by trade type
            buy_volume = sum(t['entry_price'] * t['quantity'] for t in trades if t['trade_type'] == 'buy')
            sell_volume = sum(t['entry_price'] * t['quantity'] for t in trades if t['trade_type'] == 'sell')
            
            # Format performance text
            performance_text = f"""PERFORMANCE METRICS
============================================

VOLUME METRICS:
• Total Trading Volume: ${summary.get('total_volume', 0):,.2f}
• Buy Volume:           ${buy_volume:,.2f}
• Sell Volume:          ${sell_volume:,.2f}

TRADE METRICS:
• Total Trades:         {summary.get('total_trades', 0)}
• Unique Symbols:       {summary.get('unique_symbols', 0)}
• Average Trade Size:   ${summary.get('average_trade_size', 0):,.2f}

PORTFOLIO ACTIVITY:
• Most Active Symbol:   {summary.get('most_active_symbol', 'N/A')}
• Most Used Asset Type: {summary.get('most_active_asset_type', 'N/A')}

RECENT ACTIVITY:
"""
            
            # Show recent trades
            recent_trades = trades[-3:] if trades else []
            for trade in recent_trades:
                value = trade['entry_price'] * trade['quantity']
                performance_text += f"• {trade['entry_date']} | {trade['symbol']} {trade['trade_type'].upper()} | ${value:,.2f}\n"
            
            if not recent_trades:
                performance_text += "• No recent trades\n"
            
            self.performance_content.setText(performance_text)
            logger.info("Refreshed performance metrics")
            
        except Exception as e:
            error_text = f"Error loading performance metrics: {str(e)}"
            self.performance_content.setText(error_text)
            logger.error(f"Failed to refresh performance: {e}")
    
    def _populate_trades_table(self, trades_data: List[Dict[str, Any]]):
        """Populate the trades table with given data."""
        self.trades_table.setRowCount(len(trades_data))
        
        for row, trade in enumerate(trades_data):
            # ID (hidden)
            self.trades_table.setItem(row, 0, QTableWidgetItem(str(trade['id'])))
            
            # Symbol
            self.trades_table.setItem(row, 1, QTableWidgetItem(trade['symbol']))
            
            # Asset Type
            self.trades_table.setItem(row, 2, QTableWidgetItem(trade['asset_type'].upper()))
            
            # Trade Type
            trade_type_item = QTableWidgetItem(trade['trade_type'].upper())
            if trade['trade_type'] in ['buy', 'cover']:
                trade_type_item.setBackground(QColor(220, 255, 220))  # Light green
            else:
                trade_type_item.setBackground(QColor(255, 220, 220))  # Light red
            self.trades_table.setItem(row, 3, trade_type_item)
            
            # Entry Date
            self.trades_table.setItem(row, 4, QTableWidgetItem(trade['entry_date']))
            
            # Entry Price
            price_item = QTableWidgetItem(f"${trade['entry_price']:.4f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(row, 5, price_item)
            
            # Quantity
            qty_item = QTableWidgetItem(f"{trade['quantity']:.4f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(row, 6, qty_item)
            
            # Value (Price * Quantity)
            value = trade['entry_price'] * trade['quantity']
            value_item = QTableWidgetItem(f"${value:,.2f}")
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(row, 7, value_item)
            
            # Notes
            self.trades_table.setItem(row, 8, QTableWidgetItem(trade.get('notes', '')))
            
            # Tags
            self.trades_table.setItem(row, 9, QTableWidgetItem(trade.get('tags', '')))
    
    def refresh_data(self):
        """Refresh all data (trades, analysis, and performance)."""
        self.refresh_trades()
        self.refresh_analysis()
        self.refresh_performance()
        self.data_updated.emit()
        logger.info("Refreshed all Trading Journal data") 