"""
finance_page.py

Personal Finance page UI for the Alpha application.
Handles the user interface for expense and savings management.
Integrates with PersonalFinance business logic while maintaining separation of concerns.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QGroupBox, 
    QFormLayout, QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, 
    QTextEdit, QSplitter, QMessageBox, QDialog, QDialogButtonBox,
    QHeaderView, QAbstractItemView, QFrame
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont, QColor
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

# Import business logic
from finance import PersonalFinance, PersonalFinanceError
from db import AlphaDatabase

# Configure logging
logger = logging.getLogger(__name__)


class AddExpenseDialog(QDialog):
    """Dialog for adding new expenses."""
    
    def __init__(self, parent=None):
        """Initialize the add expense dialog."""
        super().__init__(parent)
        self.setWindowTitle("Add New Expense")
        self.setModal(True)
        self.resize(400, 300)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setValue(0.01)
        form_layout.addRow("Amount ($):", self.amount_input)
        
        # Category
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        categories = [
            "Food & Dining", "Transportation", "Shopping", "Bills", 
            "Entertainment", "Healthcare", "Travel", "Education", "Other"
        ]
        self.category_input.addItems(categories)
        form_layout.addRow("Category:", self.category_input)
        
        # Date
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date_input)
        
        # Description
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Enter expense description...")
        form_layout.addRow("Description:", self.description_input)
        
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
    
    def get_expense_data(self) -> Dict[str, Any]:
        """Get the expense data from the form."""
        return {
            'amount': self.amount_input.value(),
            'category': self.category_input.currentText(),
            'date': self.date_input.date().toString('yyyy-MM-dd'),
            'description': self.description_input.text(),
            'tags': self.tags_input.text()
        }


class AddSavingsDialog(QDialog):
    """Dialog for adding new savings records."""
    
    def __init__(self, parent=None):
        """Initialize the add savings dialog."""
        super().__init__(parent)
        self.setWindowTitle("Add New Savings")
        self.setModal(True)
        self.resize(400, 300)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setValue(0.01)
        form_layout.addRow("Amount ($):", self.amount_input)
        
        # Source
        self.source_input = QComboBox()
        self.source_input.setEditable(True)
        sources = [
            "Salary", "Freelance", "Investment", "Bonus", 
            "Gift", "Refund", "Side Hustle", "Other"
        ]
        self.source_input.addItems(sources)
        form_layout.addRow("Source:", self.source_input)
        
        # Date
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date_input)
        
        # Description
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Enter savings description...")
        form_layout.addRow("Description:", self.description_input)
        
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
    
    def get_savings_data(self) -> Dict[str, Any]:
        """Get the savings data from the form."""
        return {
            'amount': self.amount_input.value(),
            'source': self.source_input.currentText(),
            'date': self.date_input.date().toString('yyyy-MM-dd'),
            'description': self.description_input.text(),
            'tags': self.tags_input.text()
        }


class EditExpenseDialog(AddExpenseDialog):
    """Dialog for editing existing expenses."""
    
    def __init__(self, expense_data: Dict[str, Any], parent=None):
        """Initialize the edit expense dialog with existing data."""
        super().__init__(parent)
        self.setWindowTitle("Edit Expense")
        self._populate_form(expense_data)
    
    def _populate_form(self, data: Dict[str, Any]):
        """Populate the form with existing expense data."""
        self.amount_input.setValue(float(data.get('amount', 0)))
        
        category = data.get('category', '')
        index = self.category_input.findText(category)
        if index >= 0:
            self.category_input.setCurrentIndex(index)
        else:
            self.category_input.setCurrentText(category)
        
        date_str = data.get('date', '')
        if date_str:
            date = QDate.fromString(date_str, 'yyyy-MM-dd')
            self.date_input.setDate(date)
        
        self.description_input.setText(data.get('description', ''))
        self.tags_input.setText(data.get('tags', ''))


class EditSavingsDialog(AddSavingsDialog):
    """Dialog for editing existing savings records."""
    
    def __init__(self, savings_data: Dict[str, Any], parent=None):
        """Initialize the edit savings dialog with existing data."""
        super().__init__(parent)
        self.setWindowTitle("Edit Savings")
        self._populate_form(savings_data)
    
    def _populate_form(self, data: Dict[str, Any]):
        """Populate the form with existing savings data."""
        self.amount_input.setValue(float(data.get('amount', 0)))
        
        source = data.get('source', '')
        index = self.source_input.findText(source)
        if index >= 0:
            self.source_input.setCurrentIndex(index)
        else:
            self.source_input.setCurrentText(source)
        
        date_str = data.get('date', '')
        if date_str:
            date = QDate.fromString(date_str, 'yyyy-MM-dd')
            self.date_input.setDate(date)
        
        self.description_input.setText(data.get('description', ''))
        self.tags_input.setText(data.get('tags', ''))


class FinancePage(QWidget):
    """
    Personal Finance management page.
    
    Provides UI for:
    - Adding, editing, and viewing expenses
    - Managing savings records
    - Expense categorization and filtering
    - Financial summaries and totals
    
    Integrates with PersonalFinance business logic while maintaining
    strict separation between UI and business logic.
    """
    
    # Signals for data updates
    data_updated = Signal()
    
    def __init__(self, personal_finance: Optional[PersonalFinance] = None):
        """
        Initialize the Personal Finance page.
        
        Args:
            personal_finance: PersonalFinance instance for business logic
        """
        super().__init__()
        
        # Store business logic reference
        self.personal_finance = personal_finance
        
        # Data storage for tables
        self.expenses_data = []
        self.savings_data = []
        
        self._setup_ui()
        
        # Load initial data if business logic is available
        if self.personal_finance:
            self.refresh_data()
        
        logger.info("Personal Finance page initialized")
    
    def set_personal_finance(self, personal_finance: PersonalFinance):
        """Set the PersonalFinance instance for business logic operations."""
        self.personal_finance = personal_finance
        self.refresh_data()
    
    def _setup_ui(self):
        """Set up the main UI layout and components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Page title
        title_label = QLabel("Personal Finance Management")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create tab widget for expenses and savings
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Add tabs
        self._setup_expenses_tab()
        self._setup_savings_tab()
        self._setup_summary_tab()
    
    def _setup_expenses_tab(self):
        """Set up the expenses management tab."""
        expenses_widget = QWidget()
        layout = QVBoxLayout(expenses_widget)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Expense Management")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Control buttons
        self.add_expense_btn = QPushButton("Add Expense")
        self.add_expense_btn.clicked.connect(self._add_expense)
        header_layout.addWidget(self.add_expense_btn)
        
        self.edit_expense_btn = QPushButton("Edit Expense")
        self.edit_expense_btn.clicked.connect(self._edit_expense)
        self.edit_expense_btn.setEnabled(False)
        header_layout.addWidget(self.edit_expense_btn)
        
        self.delete_expense_btn = QPushButton("Delete Expense")
        self.delete_expense_btn.clicked.connect(self._delete_expense)
        self.delete_expense_btn.setEnabled(False)
        header_layout.addWidget(self.delete_expense_btn)
        
        self.refresh_expenses_btn = QPushButton("Refresh")
        self.refresh_expenses_btn.clicked.connect(self.refresh_expenses)
        header_layout.addWidget(self.refresh_expenses_btn)
        
        layout.addLayout(header_layout)
        
        # Expenses table
        self.expenses_table = QTableWidget()
        self.expenses_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.expenses_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.expenses_table.setAlternatingRowColors(True)
        self.expenses_table.setSortingEnabled(True)
        
        # Table headers
        headers = ["ID", "Date", "Amount", "Category", "Description", "Tags"]
        self.expenses_table.setColumnCount(len(headers))
        self.expenses_table.setHorizontalHeaderLabels(headers)
        
        # Hide ID column
        self.expenses_table.setColumnHidden(0, True)
        
        # Resize columns
        header = self.expenses_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Amount
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Category
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Description
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Tags
        
        # Connect selection changes
        self.expenses_table.selectionModel().selectionChanged.connect(self._on_expense_selection_changed)
        self.expenses_table.doubleClicked.connect(self._edit_expense)
        
        layout.addWidget(self.expenses_table)
        
        # Add to tab widget
        self.tab_widget.addTab(expenses_widget, "💸 Expenses")
    
    def _setup_savings_tab(self):
        """Set up the savings management tab."""
        savings_widget = QWidget()
        layout = QVBoxLayout(savings_widget)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Savings Management")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Control buttons
        self.add_savings_btn = QPushButton("Add Savings")
        self.add_savings_btn.clicked.connect(self._add_savings)
        header_layout.addWidget(self.add_savings_btn)
        
        self.edit_savings_btn = QPushButton("Edit Savings")
        self.edit_savings_btn.clicked.connect(self._edit_savings)
        self.edit_savings_btn.setEnabled(False)
        header_layout.addWidget(self.edit_savings_btn)
        
        self.delete_savings_btn = QPushButton("Delete Savings")
        self.delete_savings_btn.clicked.connect(self._delete_savings)
        self.delete_savings_btn.setEnabled(False)
        header_layout.addWidget(self.delete_savings_btn)
        
        self.refresh_savings_btn = QPushButton("Refresh")
        self.refresh_savings_btn.clicked.connect(self.refresh_savings)
        header_layout.addWidget(self.refresh_savings_btn)
        
        layout.addLayout(header_layout)
        
        # Savings table
        self.savings_table = QTableWidget()
        self.savings_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.savings_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.savings_table.setAlternatingRowColors(True)
        self.savings_table.setSortingEnabled(True)
        
        # Table headers
        headers = ["ID", "Date", "Amount", "Source", "Description", "Tags"]
        self.savings_table.setColumnCount(len(headers))
        self.savings_table.setHorizontalHeaderLabels(headers)
        
        # Hide ID column
        self.savings_table.setColumnHidden(0, True)
        
        # Resize columns
        header = self.savings_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Amount
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Source
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Description
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Tags
        
        # Connect selection changes
        self.savings_table.selectionModel().selectionChanged.connect(self._on_savings_selection_changed)
        self.savings_table.doubleClicked.connect(self._edit_savings)
        
        layout.addWidget(self.savings_table)
        
        # Add to tab widget
        self.tab_widget.addTab(savings_widget, "💰 Savings")
    
    def _setup_summary_tab(self):
        """Set up the financial summary tab."""
        summary_widget = QWidget()
        layout = QVBoxLayout(summary_widget)
        
        # Summary section header
        header_label = QLabel("Financial Summary")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Summary content
        self.summary_content = QLabel("Loading financial summary...")
        self.summary_content.setStyleSheet("""
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
        self.summary_content.setWordWrap(True)
        self.summary_content.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.summary_content)
        
        # Refresh button
        refresh_summary_btn = QPushButton("Refresh Summary")
        refresh_summary_btn.clicked.connect(self.refresh_summary)
        layout.addWidget(refresh_summary_btn)
        
        # Add to tab widget
        self.tab_widget.addTab(summary_widget, "📊 Summary")
    
    def _on_expense_selection_changed(self):
        """Handle expense table selection changes."""
        has_selection = len(self.expenses_table.selectionModel().selectedRows()) > 0
        self.edit_expense_btn.setEnabled(has_selection)
        self.delete_expense_btn.setEnabled(has_selection)
    
    def _on_savings_selection_changed(self):
        """Handle savings table selection changes."""
        has_selection = len(self.savings_table.selectionModel().selectedRows()) > 0
        self.edit_savings_btn.setEnabled(has_selection)
        self.delete_savings_btn.setEnabled(has_selection)
    
    def _add_expense(self):
        """Add a new expense."""
        if not self.personal_finance:
            QMessageBox.warning(self, "Error", "Personal Finance service not available")
            return
        
        dialog = AddExpenseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_expense_data()
                self.personal_finance.add_expense(
                    date=data['date'],
                    category=data['category'], 
                    amount=data['amount'],
                    note=data['description']
                )
                self.refresh_expenses()
                QMessageBox.information(self, "Success", "Expense added successfully")
                logger.info(f"Added expense: {data['amount']} in {data['category']}")
                
            except PersonalFinanceError as e:
                QMessageBox.critical(self, "Error", f"Failed to add expense: {str(e)}")
                logger.error(f"Failed to add expense: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error adding expense: {e}")
    
    def _edit_expense(self):
        """Edit the selected expense."""
        if not self.personal_finance:
            QMessageBox.warning(self, "Error", "Personal Finance service not available")
            return
        
        selected_rows = self.expenses_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Info", "Please select an expense to edit")
            return
        
        row = selected_rows[0].row()
        expense_id = int(self.expenses_table.item(row, 0).text())
        
        # Find the expense data
        expense_data = None
        for expense in self.expenses_data:
            if expense['id'] == expense_id:
                expense_data = expense
                break
        
        if not expense_data:
            QMessageBox.critical(self, "Error", "Expense data not found")
            return
        
        dialog = EditExpenseDialog(expense_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_expense_data()
                self.personal_finance.update_expense(
                    expense_id=expense_id,
                    date=data['date'],
                    category=data['category'],
                    amount=data['amount'],
                    note=data['description']
                )
                self.refresh_expenses()
                QMessageBox.information(self, "Success", "Expense updated successfully")
                logger.info(f"Updated expense ID {expense_id}")
                
            except PersonalFinanceError as e:
                QMessageBox.critical(self, "Error", f"Failed to update expense: {str(e)}")
                logger.error(f"Failed to update expense: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error updating expense: {e}")
    
    def _delete_expense(self):
        """Delete the selected expense."""
        if not self.personal_finance:
            QMessageBox.warning(self, "Error", "Personal Finance service not available")
            return
        
        selected_rows = self.expenses_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Info", "Please select an expense to delete")
            return
        
        row = selected_rows[0].row()
        expense_id = int(self.expenses_table.item(row, 0).text())
        expense_desc = self.expenses_table.item(row, 4).text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the expense:\n\n{expense_desc}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.personal_finance.delete_expense(expense_id)
                self.refresh_expenses()
                QMessageBox.information(self, "Success", "Expense deleted successfully")
                logger.info(f"Deleted expense ID {expense_id}")
                
            except PersonalFinanceError as e:
                QMessageBox.critical(self, "Error", f"Failed to delete expense: {str(e)}")
                logger.error(f"Failed to delete expense: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error deleting expense: {e}")
    
    def _add_savings(self):
        """Add a new savings record."""
        if not self.personal_finance:
            QMessageBox.warning(self, "Error", "Personal Finance service not available")
            return
        
        dialog = AddSavingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_savings_data()
                self.personal_finance.add_savings(
                    date=data['date'],
                    source=data['source'],
                    amount=data['amount'],
                    note=data['description']
                )
                self.refresh_savings()
                QMessageBox.information(self, "Success", "Savings added successfully")
                logger.info(f"Added savings: {data['amount']} from {data['source']}")
                
            except PersonalFinanceError as e:
                QMessageBox.critical(self, "Error", f"Failed to add savings: {str(e)}")
                logger.error(f"Failed to add savings: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error adding savings: {e}")
    
    def _edit_savings(self):
        """Edit the selected savings record."""
        if not self.personal_finance:
            QMessageBox.warning(self, "Error", "Personal Finance service not available")
            return
        
        selected_rows = self.savings_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Info", "Please select a savings record to edit")
            return
        
        row = selected_rows[0].row()
        savings_id = int(self.savings_table.item(row, 0).text())
        
        # Find the savings data
        savings_data = None
        for savings in self.savings_data:
            if savings['id'] == savings_id:
                savings_data = savings
                break
        
        if not savings_data:
            QMessageBox.critical(self, "Error", "Savings data not found")
            return
        
        dialog = EditSavingsDialog(savings_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_savings_data()
                self.personal_finance.update_savings(
                    savings_id=savings_id,
                    date=data['date'],
                    source=data['source'],
                    amount=data['amount'],
                    note=data['description']
                )
                self.refresh_savings()
                QMessageBox.information(self, "Success", "Savings updated successfully")
                logger.info(f"Updated savings ID {savings_id}")
                
            except PersonalFinanceError as e:
                QMessageBox.critical(self, "Error", f"Failed to update savings: {str(e)}")
                logger.error(f"Failed to update savings: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error updating savings: {e}")
    
    def _delete_savings(self):
        """Delete the selected savings record."""
        if not self.personal_finance:
            QMessageBox.warning(self, "Error", "Personal Finance service not available")
            return
        
        selected_rows = self.savings_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Info", "Please select a savings record to delete")
            return
        
        row = selected_rows[0].row()
        savings_id = int(self.savings_table.item(row, 0).text())
        savings_desc = self.savings_table.item(row, 4).text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the savings record:\n\n{savings_desc}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.personal_finance.delete_savings(savings_id)
                self.refresh_savings()
                QMessageBox.information(self, "Success", "Savings deleted successfully")
                logger.info(f"Deleted savings ID {savings_id}")
                
            except PersonalFinanceError as e:
                QMessageBox.critical(self, "Error", f"Failed to delete savings: {str(e)}")
                logger.error(f"Failed to delete savings: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error deleting savings: {e}")
    
    def refresh_expenses(self):
        """Refresh the expenses table with current data."""
        if not self.personal_finance:
            return
        
        try:
            self.expenses_data = self.personal_finance.get_all_expenses()
            self._populate_expenses_table()
            logger.info(f"Refreshed expenses table with {len(self.expenses_data)} records")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh expenses: {str(e)}")
            logger.error(f"Failed to refresh expenses: {e}")
    
    def refresh_savings(self):
        """Refresh the savings table with current data."""
        if not self.personal_finance:
            return
        
        try:
            self.savings_data = self.personal_finance.get_all_savings()
            self._populate_savings_table()
            logger.info(f"Refreshed savings table with {len(self.savings_data)} records")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh savings: {str(e)}")
            logger.error(f"Failed to refresh savings: {e}")
    
    def refresh_summary(self):
        """Refresh the financial summary."""
        if not self.personal_finance:
            self.summary_content.setText("Personal Finance service not available")
            return
        
        try:
            # Get summary data
            total_expenses = self.personal_finance.get_expense_total()
            total_savings = self.personal_finance.get_savings_total()
            net_position_data = self.personal_finance.get_net_position()
            net_position = net_position_data.get('net_position', 0)
            
            # Get breakdown data
            expense_breakdown = self.personal_finance.get_expense_breakdown_by_category()
            # Create savings breakdown manually since method doesn't exist
            savings_breakdown = {}
            savings_data = self.personal_finance.get_all_savings()
            for savings in savings_data:
                source = savings.get('source', 'Unknown')
                amount = savings.get('amount', 0)
                savings_breakdown[source] = savings_breakdown.get(source, 0) + amount
            
            # Format summary text
            summary_text = f"""FINANCIAL SUMMARY
============================================

TOTALS:
• Total Expenses: ${total_expenses:,.2f}
• Total Savings:  ${total_savings:,.2f}
• Net Position:   ${net_position:,.2f}

EXPENSE BREAKDOWN BY CATEGORY:
"""
            for category, amount in expense_breakdown.items():
                percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                summary_text += f"• {category:<15}: ${amount:>8,.2f} ({percentage:>5.1f}%)\n"
            
            summary_text += "\nSAVINGS BREAKDOWN BY SOURCE:\n"
            for source, amount in savings_breakdown.items():
                percentage = (amount / total_savings * 100) if total_savings > 0 else 0
                summary_text += f"• {source:<15}: ${amount:>8,.2f} ({percentage:>5.1f}%)\n"
            
            summary_text += f"\nRECORD COUNTS:\n"
            summary_text += f"• Expense Records: {len(self.expenses_data)}\n"
            summary_text += f"• Savings Records: {len(self.savings_data)}\n"
            
            self.summary_content.setText(summary_text)
            logger.info("Refreshed financial summary")
            
        except Exception as e:
            error_text = f"Error loading financial summary: {str(e)}"
            self.summary_content.setText(error_text)
            logger.error(f"Failed to refresh summary: {e}")
    
    def _populate_expenses_table(self):
        """Populate the expenses table with current data."""
        self.expenses_table.setRowCount(len(self.expenses_data))
        
        for row, expense in enumerate(self.expenses_data):
            # ID (hidden)
            self.expenses_table.setItem(row, 0, QTableWidgetItem(str(expense['id'])))
            
            # Date
            self.expenses_table.setItem(row, 1, QTableWidgetItem(expense['date']))
            
            # Amount
            amount_item = QTableWidgetItem(f"${expense['amount']:.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.expenses_table.setItem(row, 2, amount_item)
            
            # Category
            self.expenses_table.setItem(row, 3, QTableWidgetItem(expense['category']))
            
            # Description (stored as 'note' in database)
            self.expenses_table.setItem(row, 4, QTableWidgetItem(expense.get('note', '')))
            
            # Tags (not stored in database, show empty)
            self.expenses_table.setItem(row, 5, QTableWidgetItem(''))
    
    def _populate_savings_table(self):
        """Populate the savings table with current data."""
        self.savings_table.setRowCount(len(self.savings_data))
        
        for row, savings in enumerate(self.savings_data):
            # ID (hidden)
            self.savings_table.setItem(row, 0, QTableWidgetItem(str(savings['id'])))
            
            # Date
            self.savings_table.setItem(row, 1, QTableWidgetItem(savings['date']))
            
            # Amount
            amount_item = QTableWidgetItem(f"${savings['amount']:.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.savings_table.setItem(row, 2, amount_item)
            
            # Source
            self.savings_table.setItem(row, 3, QTableWidgetItem(savings['source']))
            
            # Description (stored as 'note' in database)
            self.savings_table.setItem(row, 4, QTableWidgetItem(savings.get('note', '')))
            
            # Tags (not stored in database, show empty)
            self.savings_table.setItem(row, 5, QTableWidgetItem(''))
    
    def refresh_data(self):
        """Refresh all data (expenses, savings, and summary)."""
        self.refresh_expenses()
        self.refresh_savings()
        self.refresh_summary()
        self.data_updated.emit()
        logger.info("Refreshed all Personal Finance data") 