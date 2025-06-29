"""
db.py

This module contains all database (SQLite) logic for the alpha application.
Provides a complete database abstraction layer with CRUD operations for
expenses, savings, trades, and positions.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlphaDatabase:
    """
    Database manager class for the Alpha personal finance application.
    
    Handles all SQLite database operations including table creation,
    data insertion, updates, deletions, and queries for expenses,
    savings, trades, and positions.
    """
    
    def __init__(self, db_path: str = "alpha.db"):
        """
        Initialize the database connection and create tables if they don't exist.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._create_tables()
        logger.info(f"Database initialized: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Ensures proper connection cleanup and transaction handling.
        
        Yields:
            sqlite3.Connection: Database connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _create_tables(self):
        """
        Create all required tables if they don't exist.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create expenses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    note TEXT
                )
            """)
            
            # Create savings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS savings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    source TEXT NOT NULL,
                    amount REAL NOT NULL,
                    note TEXT
                )
            """)
            
            # Create trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    entry_date TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    trade_type TEXT NOT NULL,
                    notes TEXT,
                    tags TEXT
                )
            """)
            
            # Create positions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    entry_date TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    quantity REAL NOT NULL
                )
            """)
            
            conn.commit()
            logger.info("Database tables created/verified")
    
    # ==================== EXPENSES METHODS ====================
    
    def add_expense(self, date: str, category: str, amount: float, note: str = "") -> int:
        """
        Add a new expense record to the database.
        
        Args:
            date (str): Date of the expense (YYYY-MM-DD format)
            category (str): Expense category
            amount (float): Amount spent
            note (str, optional): Additional notes
            
        Returns:
            int: ID of the newly created expense record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (date, category, amount, note)
                VALUES (?, ?, ?, ?)
            """, (date, category, amount, note))
            conn.commit()
            expense_id = cursor.lastrowid
            logger.info(f"Added expense: ID {expense_id}, {category} - ${amount}")
            return expense_id
    
    def update_expense(self, expense_id: int, date: Optional[str] = None, category: Optional[str] = None, 
                      amount: Optional[float] = None, note: Optional[str] = None) -> bool:
        """
        Update an existing expense record.
        
        Args:
            expense_id (int): ID of the expense to update
            date (str, optional): New date
            category (str, optional): New category
            amount (float, optional): New amount
            note (str, optional): New note
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Build dynamic update query based on provided parameters
        updates = []
        params = []
        
        if date is not None:
            updates.append("date = ?")
            params.append(date)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if amount is not None:
            updates.append("amount = ?")
            params.append(amount)
        if note is not None:
            updates.append("note = ?")
            params.append(note)
        
        if not updates:
            return False
        
        params.append(expense_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE expenses SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated expense ID {expense_id}")
            return success
    
    def delete_expense(self, expense_id: int) -> bool:
        """
        Delete an expense record.
        
        Args:
            expense_id (int): ID of the expense to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Deleted expense ID {expense_id}")
            return success
    
    def get_expense(self, expense_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific expense by ID.
        
        Args:
            expense_id (int): ID of the expense to retrieve
            
        Returns:
            dict or None: Expense data as dictionary, None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_expenses(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all expenses from the database.
        
        Args:
            limit (int, optional): Maximum number of records to return
            offset (int): Number of records to skip
            
        Returns:
            list: List of expense dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM expenses ORDER BY date DESC"
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_expenses_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all expenses for a specific category.
        
        Args:
            category (str): Category name to filter by
            
        Returns:
            list: List of expense dictionaries for the category
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM expenses WHERE category = ? ORDER BY date DESC
            """, (category,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_expenses_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get expenses within a date range.
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            list: List of expense dictionaries within the date range
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM expenses 
                WHERE date BETWEEN ? AND ? 
                ORDER BY date DESC
            """, (start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== SAVINGS METHODS ====================
    
    def add_savings(self, date: str, source: str, amount: float, note: str = "") -> int:
        """
        Add a new savings record to the database.
        
        Args:
            date (str): Date of the savings (YYYY-MM-DD format)
            source (str): Source of savings (salary, investment, etc.)
            amount (float): Amount saved
            note (str, optional): Additional notes
            
        Returns:
            int: ID of the newly created savings record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO savings (date, source, amount, note)
                VALUES (?, ?, ?, ?)
            """, (date, source, amount, note))
            conn.commit()
            savings_id = cursor.lastrowid
            logger.info(f"Added savings: ID {savings_id}, {source} - ${amount}")
            return savings_id
    
    def update_savings(self, savings_id: int, date: str = None, source: str = None,
                      amount: float = None, note: str = None) -> bool:
        """
        Update an existing savings record.
        
        Args:
            savings_id (int): ID of the savings to update
            date (str, optional): New date
            source (str, optional): New source
            amount (float, optional): New amount
            note (str, optional): New note
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        updates = []
        params = []
        
        if date is not None:
            updates.append("date = ?")
            params.append(date)
        if source is not None:
            updates.append("source = ?")
            params.append(source)
        if amount is not None:
            updates.append("amount = ?")
            params.append(amount)
        if note is not None:
            updates.append("note = ?")
            params.append(note)
        
        if not updates:
            return False
        
        params.append(savings_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE savings SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated savings ID {savings_id}")
            return success
    
    def delete_savings(self, savings_id: int) -> bool:
        """
        Delete a savings record.
        
        Args:
            savings_id (int): ID of the savings to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM savings WHERE id = ?", (savings_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Deleted savings ID {savings_id}")
            return success
    
    def get_savings(self, savings_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific savings record by ID.
        
        Args:
            savings_id (int): ID of the savings to retrieve
            
        Returns:
            dict or None: Savings data as dictionary, None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM savings WHERE id = ?", (savings_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_savings(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all savings from the database.
        
        Args:
            limit (int, optional): Maximum number of records to return
            offset (int): Number of records to skip
            
        Returns:
            list: List of savings dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM savings ORDER BY date DESC"
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_savings_by_source(self, source: str) -> List[Dict[str, Any]]:
        """
        Get all savings for a specific source.
        
        Args:
            source (str): Source name to filter by
            
        Returns:
            list: List of savings dictionaries for the source
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM savings WHERE source = ? ORDER BY date DESC
            """, (source,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== TRADES METHODS ====================
    
    def add_trade(self, symbol: str, asset_type: str, entry_date: str, entry_price: float,
                 quantity: float, trade_type: str, notes: str = "", tags: str = "") -> int:
        """
        Add a new trade record to the database.
        
        Args:
            symbol (str): Trading symbol (e.g., AAPL, BTC)
            asset_type (str): Type of asset (stock, crypto, etf, etc.)
            entry_date (str): Date of trade entry (YYYY-MM-DD format)
            entry_price (float): Price at entry
            quantity (float): Quantity traded
            trade_type (str): Type of trade (buy, sell)
            notes (str, optional): Additional notes
            tags (str, optional): Comma-separated tags
            
        Returns:
            int: ID of the newly created trade record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trades (symbol, asset_type, entry_date, entry_price, 
                                  quantity, trade_type, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, asset_type, entry_date, entry_price, quantity, trade_type, notes, tags))
            conn.commit()
            trade_id = cursor.lastrowid
            logger.info(f"Added trade: ID {trade_id}, {symbol} {trade_type} {quantity}@${entry_price}")
            return trade_id
    
    def update_trade(self, trade_id: int, **kwargs) -> bool:
        """
        Update an existing trade record.
        
        Args:
            trade_id (int): ID of the trade to update
            **kwargs: Fields to update (symbol, asset_type, entry_date, entry_price, 
                     quantity, trade_type, notes, tags)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        valid_fields = ['symbol', 'asset_type', 'entry_date', 'entry_price', 
                       'quantity', 'trade_type', 'notes', 'tags']
        
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if field in valid_fields and value is not None:
                updates.append(f"{field} = ?")
                params.append(value)
        
        if not updates:
            return False
        
        params.append(trade_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE trades SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated trade ID {trade_id}")
            return success
    
    def delete_trade(self, trade_id: int) -> bool:
        """
        Delete a trade record.
        
        Args:
            trade_id (int): ID of the trade to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Deleted trade ID {trade_id}")
            return success
    
    def get_trade(self, trade_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific trade by ID.
        
        Args:
            trade_id (int): ID of the trade to retrieve
            
        Returns:
            dict or None: Trade data as dictionary, None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_trades(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all trades from the database.
        
        Args:
            limit (int, optional): Maximum number of records to return
            offset (int): Number of records to skip
            
        Returns:
            list: List of trade dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM trades ORDER BY entry_date DESC"
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trades_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get all trades for a specific symbol.
        
        Args:
            symbol (str): Symbol to filter by
            
        Returns:
            list: List of trade dictionaries for the symbol
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trades WHERE symbol = ? ORDER BY entry_date DESC
            """, (symbol,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trades_by_asset_type(self, asset_type: str) -> List[Dict[str, Any]]:
        """
        Get all trades for a specific asset type.
        
        Args:
            asset_type (str): Asset type to filter by
            
        Returns:
            list: List of trade dictionaries for the asset type
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trades WHERE asset_type = ? ORDER BY entry_date DESC
            """, (asset_type,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== POSITIONS METHODS ====================
    
    def add_position(self, symbol: str, asset_type: str, entry_date: str, 
                    entry_price: float, quantity: float) -> int:
        """
        Add a new position record to the database.
        
        Args:
            symbol (str): Trading symbol (e.g., AAPL, BTC)
            asset_type (str): Type of asset (stock, crypto, etf, etc.)
            entry_date (str): Date of position entry (YYYY-MM-DD format)
            entry_price (float): Average entry price
            quantity (float): Quantity held
            
        Returns:
            int: ID of the newly created position record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO positions (symbol, asset_type, entry_date, entry_price, quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol, asset_type, entry_date, entry_price, quantity))
            conn.commit()
            position_id = cursor.lastrowid
            logger.info(f"Added position: ID {position_id}, {symbol} {quantity}@${entry_price}")
            return position_id
    
    def update_position(self, position_id: int, symbol: str = None, asset_type: str = None,
                       entry_date: str = None, entry_price: float = None, 
                       quantity: float = None) -> bool:
        """
        Update an existing position record.
        
        Args:
            position_id (int): ID of the position to update
            symbol (str, optional): New symbol
            asset_type (str, optional): New asset type
            entry_date (str, optional): New entry date
            entry_price (float, optional): New entry price
            quantity (float, optional): New quantity
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        updates = []
        params = []
        
        if symbol is not None:
            updates.append("symbol = ?")
            params.append(symbol)
        if asset_type is not None:
            updates.append("asset_type = ?")
            params.append(asset_type)
        if entry_date is not None:
            updates.append("entry_date = ?")
            params.append(entry_date)
        if entry_price is not None:
            updates.append("entry_price = ?")
            params.append(entry_price)
        if quantity is not None:
            updates.append("quantity = ?")
            params.append(quantity)
        
        if not updates:
            return False
        
        params.append(position_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE positions SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated position ID {position_id}")
            return success
    
    def delete_position(self, position_id: int) -> bool:
        """
        Delete a position record.
        
        Args:
            position_id (int): ID of the position to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM positions WHERE id = ?", (position_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Deleted position ID {position_id}")
            return success
    
    def get_position(self, position_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific position by ID.
        
        Args:
            position_id (int): ID of the position to retrieve
            
        Returns:
            dict or None: Position data as dictionary, None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        Get all positions from the database.
        
        Returns:
            list: List of position dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions ORDER BY symbol")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_position_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol (str): Symbol to search for
            
        Returns:
            dict or None: Position data as dictionary, None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions WHERE symbol = ?", (symbol,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== UTILITY METHODS ====================
    
    def get_database_stats(self) -> Dict[str, int]:
        """
        Get statistics about the database (record counts).
        
        Returns:
            dict: Dictionary with table names and record counts
        """
        stats = {}
        tables = ['expenses', 'savings', 'trades', 'positions']
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
        
        return stats
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path (str): Path for the backup file
            
        Returns:
            bool: True if backup was successful, False otherwise
        """
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False


if __name__ == "__main__":
    """
    Demonstration of the AlphaDatabase functionality.
    This runs when the module is executed directly.
    """
    print("=" * 60)
    print("ALPHA DATABASE DEMONSTRATION")
    print("=" * 60)
    
    # Initialize database
    db = AlphaDatabase()
    
    # Add sample data to each table
    print("\n📊 Adding Sample Data...")
    
    # Add sample expense
    expense_id = db.add_expense(
        date="2024-01-15",
        category="Food & Dining",
        amount=45.50,
        note="Lunch at restaurant"
    )
    print(f"Added expense with ID: {expense_id}")
    
    # Add sample savings
    savings_id = db.add_savings(
        date="2024-01-15",
        source="Salary",
        amount=500.00,
        note="Monthly savings from paycheck"
    )
    print(f"Added savings with ID: {savings_id}")
    
    # Add sample trade
    trade_id = db.add_trade(
        symbol="AAPL",
        asset_type="stock",
        entry_date="2024-01-15",
        entry_price=185.50,
        quantity=10,
        trade_type="buy",
        notes="Long-term hold",
        tags="tech,dividend"
    )
    print(f"Added trade with ID: {trade_id}")
    
    # Add sample position
    position_id = db.add_position(
        symbol="AAPL",
        asset_type="stock",
        entry_date="2024-01-15",
        entry_price=185.50,
        quantity=10
    )
    print(f"Added position with ID: {position_id}")
    
    # Display all data
    print("\n📋 Database Contents:")
    print("-" * 40)
    
    print("\n💰 EXPENSES:")
    expenses = db.get_all_expenses()
    for expense in expenses:
        print(f"  ID {expense['id']}: {expense['date']} | {expense['category']} | ${expense['amount']} | {expense['note']}")
    
    print("\n💾 SAVINGS:")
    savings = db.get_all_savings()
    for saving in savings:
        print(f"  ID {saving['id']}: {saving['date']} | {saving['source']} | ${saving['amount']} | {saving['note']}")
    
    print("\n📈 TRADES:")
    trades = db.get_all_trades()
    for trade in trades:
        print(f"  ID {trade['id']}: {trade['symbol']} | {trade['trade_type']} | {trade['quantity']}@${trade['entry_price']} | {trade['entry_date']}")
    
    print("\n📊 POSITIONS:")
    positions = db.get_all_positions()
    for position in positions:
        print(f"  ID {position['id']}: {position['symbol']} | {position['quantity']}@${position['entry_price']} | {position['entry_date']}")
    
    # Show database statistics
    print("\n📈 DATABASE STATISTICS:")
    stats = db.get_database_stats()
    for table, count in stats.items():
        print(f"  {table.capitalize()}: {count} records")
    
    print("\n" + "=" * 60)
    print("✅ Database demonstration completed successfully!")
    print("The Alpha database is ready for use by other modules.")
    print("=" * 60) 