"""
finance.py

This module contains personal finance management logic for the alpha application.
Includes tracking expenses, income, savings, and financial projections.
Provides a clean API layer over the database for financial operations.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

# Import the database layer
from db import AlphaDatabase

# Configure logging
logger = logging.getLogger(__name__)


class PersonalFinanceError(Exception):
    """Custom exception for personal finance operations."""
    pass


class PersonalFinance:
    """
    Personal Finance management class for the Alpha application.
    
    Provides a high-level API for managing expenses and savings,
    with validation, error handling, and business logic.
    Built on top of the AlphaDatabase layer.
    """
    
    def __init__(self, database: AlphaDatabase):
        """
        Initialize the PersonalFinance manager.
        
        Args:
            database (AlphaDatabase): Instance of the database manager
        """
        self.db = database
        logger.info("PersonalFinance manager initialized")
    
    # ==================== EXPENSE MANAGEMENT ====================
    
    def add_expense(self, date: str, category: str, amount: float, note: str = "") -> int:
        """
        Add a new expense with validation.
        
        Args:
            date (str): Date in YYYY-MM-DD format
            category (str): Expense category
            amount (float): Amount spent (must be positive)
            note (str, optional): Additional notes
            
        Returns:
            int: ID of the newly created expense
            
        Raises:
            PersonalFinanceError: If validation fails
        """
        # Validate inputs
        self._validate_date(date)
        self._validate_category(category)
        self._validate_amount(amount)
        
        try:
            expense_id = self.db.add_expense(date, category, amount, note)
            logger.info(f"Added expense: {category} - ${amount}")
            return expense_id
        except Exception as e:
            raise PersonalFinanceError(f"Failed to add expense: {str(e)}")
    
    def update_expense(self, expense_id: int, date: str = None, category: str = None,
                      amount: float = None, note: str = None) -> bool:
        """
        Update an existing expense with validation.
        
        Args:
            expense_id (int): ID of the expense to update
            date (str, optional): New date in YYYY-MM-DD format
            category (str, optional): New category
            amount (float, optional): New amount (must be positive)
            note (str, optional): New note
            
        Returns:
            bool: True if update was successful
            
        Raises:
            PersonalFinanceError: If validation fails or expense not found
        """
        # Validate provided inputs
        if date is not None:
            self._validate_date(date)
        if category is not None:
            self._validate_category(category)
        if amount is not None:
            self._validate_amount(amount)
        
        # Check if expense exists
        if not self.get_expense(expense_id):
            raise PersonalFinanceError(f"Expense with ID {expense_id} not found")
        
        try:
            success = self.db.update_expense(expense_id, date, category, amount, note)
            if success:
                logger.info(f"Updated expense ID {expense_id}")
            return success
        except Exception as e:
            raise PersonalFinanceError(f"Failed to update expense: {str(e)}")
    
    def delete_expense(self, expense_id: int) -> bool:
        """
        Delete an expense.
        
        Args:
            expense_id (int): ID of the expense to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            PersonalFinanceError: If expense not found
        """
        # Check if expense exists
        if not self.get_expense(expense_id):
            raise PersonalFinanceError(f"Expense with ID {expense_id} not found")
        
        try:
            success = self.db.delete_expense(expense_id)
            if success:
                logger.info(f"Deleted expense ID {expense_id}")
            return success
        except Exception as e:
            raise PersonalFinanceError(f"Failed to delete expense: {str(e)}")
    
    def get_expense(self, expense_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific expense by ID.
        
        Args:
            expense_id (int): ID of the expense
            
        Returns:
            dict or None: Expense data, None if not found
        """
        try:
            return self.db.get_expense(expense_id)
        except Exception as e:
            raise PersonalFinanceError(f"Failed to retrieve expense: {str(e)}")
    
    def get_all_expenses(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all expenses with optional pagination.
        
        Args:
            limit (int, optional): Maximum number of records
            offset (int): Number of records to skip
            
        Returns:
            list: List of expense dictionaries
        """
        try:
            return self.db.get_all_expenses(limit, offset)
        except Exception as e:
            raise PersonalFinanceError(f"Failed to retrieve expenses: {str(e)}")
    
    def get_expenses_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all expenses for a specific category.
        
        Args:
            category (str): Category to filter by
            
        Returns:
            list: List of expense dictionaries
        """
        self._validate_category(category)
        try:
            return self.db.get_expenses_by_category(category)
        except Exception as e:
            raise PersonalFinanceError(f"Failed to retrieve expenses by category: {str(e)}")
    
    def get_expenses_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get expenses within a date range.
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            list: List of expense dictionaries
        """
        self._validate_date(start_date)
        self._validate_date(end_date)
        
        # Validate date range
        if start_date > end_date:
            raise PersonalFinanceError("Start date must be before or equal to end date")
        
        try:
            return self.db.get_expenses_by_date_range(start_date, end_date)
        except Exception as e:
            raise PersonalFinanceError(f"Failed to retrieve expenses by date range: {str(e)}")
    
    # ==================== SAVINGS MANAGEMENT ====================
    
    def add_savings(self, date: str, source: str, amount: float, note: str = "") -> int:
        """
        Add a new savings record with validation.
        
        Args:
            date (str): Date in YYYY-MM-DD format
            source (str): Source of savings (salary, investment, etc.)
            amount (float): Amount saved (must be positive)
            note (str, optional): Additional notes
            
        Returns:
            int: ID of the newly created savings record
            
        Raises:
            PersonalFinanceError: If validation fails
        """
        # Validate inputs
        self._validate_date(date)
        self._validate_source(source)
        self._validate_amount(amount)
        
        try:
            savings_id = self.db.add_savings(date, source, amount, note)
            logger.info(f"Added savings: {source} - ${amount}")
            return savings_id
        except Exception as e:
            raise PersonalFinanceError(f"Failed to add savings: {str(e)}")
    
    def update_savings(self, savings_id: int, date: str = None, source: str = None,
                      amount: float = None, note: str = None) -> bool:
        """
        Update an existing savings record with validation.
        
        Args:
            savings_id (int): ID of the savings to update
            date (str, optional): New date in YYYY-MM-DD format
            source (str, optional): New source
            amount (float, optional): New amount (must be positive)
            note (str, optional): New note
            
        Returns:
            bool: True if update was successful
            
        Raises:
            PersonalFinanceError: If validation fails or savings not found
        """
        # Validate provided inputs
        if date is not None:
            self._validate_date(date)
        if source is not None:
            self._validate_source(source)
        if amount is not None:
            self._validate_amount(amount)
        
        # Check if savings exists
        if not self.get_savings(savings_id):
            raise PersonalFinanceError(f"Savings with ID {savings_id} not found")
        
        try:
            success = self.db.update_savings(savings_id, date, source, amount, note)
            if success:
                logger.info(f"Updated savings ID {savings_id}")
            return success
        except Exception as e:
            raise PersonalFinanceError(f"Failed to update savings: {str(e)}")
    
    def delete_savings(self, savings_id: int) -> bool:
        """
        Delete a savings record.
        
        Args:
            savings_id (int): ID of the savings to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            PersonalFinanceError: If savings not found
        """
        # Check if savings exists
        if not self.get_savings(savings_id):
            raise PersonalFinanceError(f"Savings with ID {savings_id} not found")
        
        try:
            success = self.db.delete_savings(savings_id)
            if success:
                logger.info(f"Deleted savings ID {savings_id}")
            return success
        except Exception as e:
            raise PersonalFinanceError(f"Failed to delete savings: {str(e)}")
    
    def get_savings(self, savings_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific savings record by ID.
        
        Args:
            savings_id (int): ID of the savings
            
        Returns:
            dict or None: Savings data, None if not found
        """
        try:
            return self.db.get_savings(savings_id)
        except Exception as e:
            raise PersonalFinanceError(f"Failed to retrieve savings: {str(e)}")
    
    def get_all_savings(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all savings with optional pagination.
        
        Args:
            limit (int, optional): Maximum number of records
            offset (int): Number of records to skip
            
        Returns:
            list: List of savings dictionaries
        """
        try:
            return self.db.get_all_savings(limit, offset)
        except Exception as e:
            raise PersonalFinanceError(f"Failed to retrieve savings: {str(e)}")
    
    def get_savings_by_source(self, source: str) -> List[Dict[str, Any]]:
        """
        Get all savings for a specific source.
        
        Args:
            source (str): Source to filter by
            
        Returns:
            list: List of savings dictionaries
        """
        self._validate_source(source)
        try:
            return self.db.get_savings_by_source(source)
        except Exception as e:
            raise PersonalFinanceError(f"Failed to retrieve savings by source: {str(e)}")
    
    # ==================== FINANCIAL ANALYTICS ====================
    
    def get_expense_total(self, start_date: str = None, end_date: str = None, 
                         category: str = None) -> float:
        """
        Calculate total expenses with optional filters.
        
        Args:
            start_date (str, optional): Start date filter
            end_date (str, optional): End date filter
            category (str, optional): Category filter
            
        Returns:
            float: Total expense amount
        """
        try:
            if start_date and end_date:
                expenses = self.get_expenses_by_date_range(start_date, end_date)
            elif category:
                expenses = self.get_expenses_by_category(category)
            else:
                expenses = self.get_all_expenses()
            
            return sum(expense['amount'] for expense in expenses)
        except Exception as e:
            raise PersonalFinanceError(f"Failed to calculate expense total: {str(e)}")
    
    def get_savings_total(self, start_date: str = None, end_date: str = None,
                         source: str = None) -> float:
        """
        Calculate total savings with optional filters.
        
        Args:
            start_date (str, optional): Start date filter
            end_date (str, optional): End date filter
            source (str, optional): Source filter
            
        Returns:
            float: Total savings amount
        """
        try:
            if source:
                savings = self.get_savings_by_source(source)
            else:
                savings = self.get_all_savings()
            
            # Apply date filtering if specified
            if start_date and end_date:
                savings = [s for s in savings if start_date <= s['date'] <= end_date]
            
            return sum(saving['amount'] for saving in savings)
        except Exception as e:
            raise PersonalFinanceError(f"Failed to calculate savings total: {str(e)}")
    
    def get_net_position(self, start_date: str = None, end_date: str = None) -> Dict[str, float]:
        """
        Calculate net financial position (savings - expenses).
        
        Args:
            start_date (str, optional): Start date filter
            end_date (str, optional): End date filter
            
        Returns:
            dict: Dictionary with savings, expenses, and net amounts
        """
        try:
            total_savings = self.get_savings_total(start_date, end_date)
            total_expenses = self.get_expense_total(start_date, end_date)
            net_amount = total_savings - total_expenses
            
            return {
                'total_savings': total_savings,
                'total_expenses': total_expenses,
                'net_position': net_amount
            }
        except Exception as e:
            raise PersonalFinanceError(f"Failed to calculate net position: {str(e)}")
    
    def get_expense_breakdown_by_category(self, start_date: str = None, 
                                        end_date: str = None) -> Dict[str, float]:
        """
        Get expense breakdown by category.
        
        Args:
            start_date (str, optional): Start date filter
            end_date (str, optional): End date filter
            
        Returns:
            dict: Category names as keys, total amounts as values
        """
        try:
            if start_date and end_date:
                expenses = self.get_expenses_by_date_range(start_date, end_date)
            else:
                expenses = self.get_all_expenses()
            
            breakdown = {}
            for expense in expenses:
                category = expense['category']
                amount = expense['amount']
                breakdown[category] = breakdown.get(category, 0) + amount
            
            return breakdown
        except Exception as e:
            raise PersonalFinanceError(f"Failed to generate expense breakdown: {str(e)}")
    
    # ==================== VALIDATION METHODS ====================
    
    def _validate_date(self, date: str) -> None:
        """
        Validate date format (YYYY-MM-DD).
        
        Args:
            date (str): Date string to validate
            
        Raises:
            PersonalFinanceError: If date format is invalid
        """
        if not date or not isinstance(date, str):
            raise PersonalFinanceError("Date is required and must be a string")
        
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise PersonalFinanceError("Date must be in YYYY-MM-DD format")
    
    def _validate_category(self, category: str) -> None:
        """
        Validate expense category.
        
        Args:
            category (str): Category to validate
            
        Raises:
            PersonalFinanceError: If category is invalid
        """
        if not category or not isinstance(category, str) or not category.strip():
            raise PersonalFinanceError("Category is required and cannot be empty")
    
    def _validate_source(self, source: str) -> None:
        """
        Validate savings source.
        
        Args:
            source (str): Source to validate
            
        Raises:
            PersonalFinanceError: If source is invalid
        """
        if not source or not isinstance(source, str) or not source.strip():
            raise PersonalFinanceError("Source is required and cannot be empty")
    
    def _validate_amount(self, amount: float) -> None:
        """
        Validate amount (must be positive).
        
        Args:
            amount (float): Amount to validate
            
        Raises:
            PersonalFinanceError: If amount is invalid
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise PersonalFinanceError("Amount must be a positive number")


if __name__ == "__main__":
    """
    Demonstration of the PersonalFinance functionality.
    This runs when the module is executed directly.
    """
    print("=" * 60)
    print("PERSONAL FINANCE MODULE DEMONSTRATION")
    print("=" * 60)
    
    # Initialize database and personal finance manager
    from db import AlphaDatabase
    
    # Reduce logging noise for demo
    logging.getLogger('db').setLevel(logging.WARNING)
    
    db = AlphaDatabase()
    pf = PersonalFinance(db)
    
    print("\n💰 EXPENSE MANAGEMENT DEMO")
    print("-" * 40)
    
    # Add sample expenses
    print("📝 Adding expenses...")
    expense1_id = pf.add_expense("2024-01-20", "Food & Dining", 45.50, "Lunch with friends")
    expense2_id = pf.add_expense("2024-01-21", "Transportation", 15.75, "Bus pass")
    expense3_id = pf.add_expense("2024-01-21", "Shopping", 89.99, "Groceries")
    
    print(f"✅ Added expenses with IDs: {expense1_id}, {expense2_id}, {expense3_id}")
    
    # List all expenses
    print("\n📋 Current expenses:")
    expenses = pf.get_all_expenses()
    for expense in expenses[-3:]:  # Show last 3
        print(f"  ID {expense['id']}: {expense['date']} | {expense['category']} | ${expense['amount']:.2f} | {expense['note']}")
    
    # Update an expense
    print(f"\n🔄 Updating expense {expense1_id}...")
    pf.update_expense(expense1_id, amount=50.00, note="Updated lunch cost")
    updated_expense = pf.get_expense(expense1_id)
    print(f"✅ Updated: ${updated_expense['amount']:.2f} - {updated_expense['note']}")
    
    # Get expenses by category
    food_expenses = pf.get_expenses_by_category("Food & Dining")
    print(f"\n🍽️ Food & Dining expenses: {len(food_expenses)} found")
    
    print("\n💾 SAVINGS MANAGEMENT DEMO")
    print("-" * 40)
    
    # Add sample savings
    print("📝 Adding savings...")
    savings1_id = pf.add_savings("2024-01-20", "Salary", 800.00, "Monthly savings")
    savings2_id = pf.add_savings("2024-01-21", "Freelance", 300.00, "Side project payment")
    savings3_id = pf.add_savings("2024-01-21", "Investment", 150.00, "Dividend payment")
    
    print(f"✅ Added savings with IDs: {savings1_id}, {savings2_id}, {savings3_id}")
    
    # List all savings
    print("\n📋 Current savings:")
    savings = pf.get_all_savings()
    for saving in savings[-3:]:  # Show last 3
        print(f"  ID {saving['id']}: {saving['date']} | {saving['source']} | ${saving['amount']:.2f} | {saving['note']}")
    
    # Update a savings record
    print(f"\n🔄 Updating savings {savings1_id}...")
    pf.update_savings(savings1_id, amount=850.00, note="Updated monthly savings")
    updated_saving = pf.get_savings(savings1_id)
    print(f"✅ Updated: ${updated_saving['amount']:.2f} - {updated_saving['note']}")
    
    print("\n📊 FINANCIAL ANALYTICS DEMO")
    print("-" * 40)
    
    # Calculate totals
    total_expenses = pf.get_expense_total()
    total_savings = pf.get_savings_total()
    net_position = pf.get_net_position()
    
    print(f"💸 Total Expenses: ${total_expenses:.2f}")
    print(f"💰 Total Savings: ${total_savings:.2f}")
    print(f"📈 Net Position: ${net_position['net_position']:.2f}")
    
    # Category breakdown
    expense_breakdown = pf.get_expense_breakdown_by_category()
    print(f"\n📊 Expense Breakdown by Category:")
    for category, amount in expense_breakdown.items():
        print(f"  {category}: ${amount:.2f}")
    
    print("\n🧪 VALIDATION DEMO")
    print("-" * 40)
    
    # Test validation errors
    try:
        pf.add_expense("invalid-date", "Test", 10.0)
    except PersonalFinanceError as e:
        print(f"✅ Date validation: {e}")
    
    try:
        pf.add_expense("2024-01-01", "", 10.0)
    except PersonalFinanceError as e:
        print(f"✅ Category validation: {e}")
    
    try:
        pf.add_expense("2024-01-01", "Test", -10.0)
    except PersonalFinanceError as e:
        print(f"✅ Amount validation: {e}")
    
    print("\n🗑️ DELETION DEMO")
    print("-" * 40)
    
    # Delete records
    print(f"🗑️ Deleting expense {expense3_id}...")
    pf.delete_expense(expense3_id)
    print("✅ Expense deleted")
    
    print(f"🗑️ Deleting savings {savings3_id}...")
    pf.delete_savings(savings3_id)
    print("✅ Savings deleted")
    
    # Final summary
    final_stats = {
        'expenses': len(pf.get_all_expenses()),
        'savings': len(pf.get_all_savings())
    }
    
    print(f"\n📈 FINAL SUMMARY")
    print("-" * 40)
    print(f"📊 Current Records: {final_stats}")
    print(f"💰 Net Position: ${pf.get_net_position()['net_position']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Personal Finance module demonstration completed!")
    print("The PersonalFinance API is ready for use by GUI and other modules.")
    print("=" * 60) 