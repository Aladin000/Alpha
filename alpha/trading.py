"""
trading.py

This module contains trading journal logic for the alpha application.
Includes logging, storing, and managing trade records with search and filter capabilities.
Provides a clean API layer over the database for trading operations.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

# Import the database layer
from db import AlphaDatabase

# Configure logging
logger = logging.getLogger(__name__)


class TradingJournalError(Exception):
    """Custom exception for trading journal operations."""
    pass


class TradingJournal:
    """
    Trading Journal management class for the Alpha application.
    
    Provides a high-level API for managing trading activities with validation,
    error handling, and business logic. Built on top of the AlphaDatabase layer.
    """
    
    def __init__(self, database: AlphaDatabase):
        """
        Initialize the TradingJournal manager.
        
        Args:
            database (AlphaDatabase): Instance of the database manager
        """
        self.db = database
        self.valid_asset_types = {'stock', 'crypto', 'etf', 'forex', 'commodity', 'bond', 'option', 'future'}
        self.valid_trade_types = {'buy', 'sell', 'short', 'cover'}
        logger.info("TradingJournal manager initialized")
    
    # ==================== TRADE MANAGEMENT ====================
    
    def add_trade(self, symbol: str, asset_type: str, entry_date: str, entry_price: float,
                  quantity: float, trade_type: str, notes: str = "", tags: str = "") -> int:
        """
        Add a new trade with validation.
        
        Args:
            symbol (str): Trading symbol (e.g., AAPL, BTC-USD)
            asset_type (str): Type of asset (stock, crypto, etf, etc.)
            entry_date (str): Date in YYYY-MM-DD format
            entry_price (float): Price at entry (must be positive)
            quantity (float): Quantity traded (must be positive)
            trade_type (str): Type of trade (buy, sell, short, cover)
            notes (str, optional): Additional notes
            tags (str, optional): Comma-separated tags
            
        Returns:
            int: ID of the newly created trade
            
        Raises:
            TradingJournalError: If validation fails
        """
        # Validate inputs
        self._validate_symbol(symbol)
        self._validate_asset_type(asset_type)
        self._validate_date(entry_date)
        self._validate_price(entry_price)
        self._validate_quantity(quantity)
        self._validate_trade_type(trade_type)
        
        try:
            trade_id = self.db.add_trade(
                symbol=symbol.upper(),
                asset_type=asset_type.lower(),
                entry_date=entry_date,
                entry_price=entry_price,
                quantity=quantity,
                trade_type=trade_type.lower(),
                notes=notes,
                tags=tags
            )
            logger.info(f"Added trade: {symbol} {trade_type} {quantity}@${entry_price}")
            return trade_id
        except Exception as e:
            raise TradingJournalError(f"Failed to add trade: {str(e)}")
    
    def update_trade(self, trade_id: int, symbol: str = None, asset_type: str = None,
                    entry_date: str = None, entry_price: float = None, quantity: float = None,
                    trade_type: str = None, notes: str = None, tags: str = None) -> bool:
        """
        Update an existing trade with validation.
        
        Args:
            trade_id (int): ID of the trade to update
            symbol (str, optional): New symbol
            asset_type (str, optional): New asset type
            entry_date (str, optional): New date
            entry_price (float, optional): New entry price
            quantity (float, optional): New quantity
            trade_type (str, optional): New trade type
            notes (str, optional): New notes
            tags (str, optional): New tags
            
        Returns:
            bool: True if update was successful
            
        Raises:
            TradingJournalError: If validation fails or trade not found
        """
        # Check if trade exists
        if not self.get_trade(trade_id):
            raise TradingJournalError(f"Trade with ID {trade_id} not found")
        
        # Validate provided inputs
        if symbol is not None:
            self._validate_symbol(symbol)
            symbol = symbol.upper()
        if asset_type is not None:
            self._validate_asset_type(asset_type)
            asset_type = asset_type.lower()
        if entry_date is not None:
            self._validate_date(entry_date)
        if entry_price is not None:
            self._validate_price(entry_price)
        if quantity is not None:
            self._validate_quantity(quantity)
        if trade_type is not None:
            self._validate_trade_type(trade_type)
            trade_type = trade_type.lower()
        
        try:
            # Build kwargs for database update
            update_kwargs = {}
            if symbol is not None:
                update_kwargs['symbol'] = symbol
            if asset_type is not None:
                update_kwargs['asset_type'] = asset_type
            if entry_date is not None:
                update_kwargs['entry_date'] = entry_date
            if entry_price is not None:
                update_kwargs['entry_price'] = entry_price
            if quantity is not None:
                update_kwargs['quantity'] = quantity
            if trade_type is not None:
                update_kwargs['trade_type'] = trade_type
            if notes is not None:
                update_kwargs['notes'] = notes
            if tags is not None:
                update_kwargs['tags'] = tags
            
            success = self.db.update_trade(trade_id, **update_kwargs)
            if success:
                logger.info(f"Updated trade ID {trade_id}")
            return success
        except Exception as e:
            raise TradingJournalError(f"Failed to update trade: {str(e)}")
    
    def delete_trade(self, trade_id: int) -> bool:
        """
        Delete a trade.
        
        Args:
            trade_id (int): ID of the trade to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            TradingJournalError: If trade not found
        """
        # Check if trade exists
        if not self.get_trade(trade_id):
            raise TradingJournalError(f"Trade with ID {trade_id} not found")
        
        try:
            success = self.db.delete_trade(trade_id)
            if success:
                logger.info(f"Deleted trade ID {trade_id}")
            return success
        except Exception as e:
            raise TradingJournalError(f"Failed to delete trade: {str(e)}")
    
    def get_trade(self, trade_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific trade by ID.
        
        Args:
            trade_id (int): ID of the trade
            
        Returns:
            dict or None: Trade data, None if not found
        """
        try:
            return self.db.get_trade(trade_id)
        except Exception as e:
            raise TradingJournalError(f"Failed to retrieve trade: {str(e)}")
    
    def get_all_trades(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all trades with optional pagination.
        
        Args:
            limit (int, optional): Maximum number of records
            offset (int): Number of records to skip
            
        Returns:
            list: List of trade dictionaries
        """
        try:
            return self.db.get_all_trades(limit, offset)
        except Exception as e:
            raise TradingJournalError(f"Failed to retrieve trades: {str(e)}")
    
    # ==================== SEARCH AND FILTER METHODS ====================
    
    def get_trades_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get all trades for a specific symbol.
        
        Args:
            symbol (str): Symbol to filter by
            
        Returns:
            list: List of trade dictionaries
        """
        self._validate_symbol(symbol)
        try:
            return self.db.get_trades_by_symbol(symbol.upper())
        except Exception as e:
            raise TradingJournalError(f"Failed to retrieve trades by symbol: {str(e)}")
    
    def get_trades_by_asset_type(self, asset_type: str) -> List[Dict[str, Any]]:
        """
        Get all trades for a specific asset type.
        
        Args:
            asset_type (str): Asset type to filter by
            
        Returns:
            list: List of trade dictionaries
        """
        self._validate_asset_type(asset_type)
        try:
            return self.db.get_trades_by_asset_type(asset_type.lower())
        except Exception as e:
            raise TradingJournalError(f"Failed to retrieve trades by asset type: {str(e)}")
    
    def get_trades_by_type(self, trade_type: str) -> List[Dict[str, Any]]:
        """
        Get all trades for a specific trade type.
        
        Args:
            trade_type (str): Trade type to filter by (buy, sell, short, cover)
            
        Returns:
            list: List of trade dictionaries
        """
        self._validate_trade_type(trade_type)
        try:
            trades = self.get_all_trades()
            return [trade for trade in trades if trade['trade_type'] == trade_type.lower()]
        except Exception as e:
            raise TradingJournalError(f"Failed to retrieve trades by type: {str(e)}")
    
    def get_trades_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get trades within a date range.
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            list: List of trade dictionaries
        """
        self._validate_date(start_date)
        self._validate_date(end_date)
        
        # Validate date range
        if start_date > end_date:
            raise TradingJournalError("Start date must be before or equal to end date")
        
        try:
            trades = self.get_all_trades()
            return [trade for trade in trades 
                   if start_date <= trade['entry_date'] <= end_date]
        except Exception as e:
            raise TradingJournalError(f"Failed to retrieve trades by date range: {str(e)}")
    
    def search_trades_by_tags(self, tag: str) -> List[Dict[str, Any]]:
        """
        Search trades that contain a specific tag.
        
        Args:
            tag (str): Tag to search for
            
        Returns:
            list: List of trade dictionaries containing the tag
        """
        if not tag or not isinstance(tag, str):
            raise TradingJournalError("Tag must be a non-empty string")
        
        try:
            trades = self.get_all_trades()
            return [trade for trade in trades 
                   if trade['tags'] and tag.lower() in trade['tags'].lower()]
        except Exception as e:
            raise TradingJournalError(f"Failed to search trades by tags: {str(e)}")
    
    # ==================== ANALYTICS METHODS ====================
    
    def get_trade_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all trades.
        
        Returns:
            dict: Summary statistics including totals by type, asset type, etc.
        """
        try:
            trades = self.get_all_trades()
            
            summary = {
                'total_trades': len(trades),
                'by_trade_type': {},
                'by_asset_type': {},
                'total_volume': 0.0,
                'symbols_traded': set()
            }
            
            for trade in trades:
                # Count by trade type
                trade_type = trade['trade_type']
                summary['by_trade_type'][trade_type] = summary['by_trade_type'].get(trade_type, 0) + 1
                
                # Count by asset type
                asset_type = trade['asset_type']
                summary['by_asset_type'][asset_type] = summary['by_asset_type'].get(asset_type, 0) + 1
                
                # Calculate volume (price * quantity)
                summary['total_volume'] += trade['entry_price'] * trade['quantity']
                
                # Track unique symbols
                summary['symbols_traded'].add(trade['symbol'])
            
            # Convert set to count
            summary['unique_symbols'] = len(summary['symbols_traded'])
            del summary['symbols_traded']
            
            return summary
        except Exception as e:
            raise TradingJournalError(f"Failed to generate trade summary: {str(e)}")
    
    def get_symbol_performance(self, symbol: str) -> Dict[str, Any]:
        """
        Get performance metrics for a specific symbol.
        
        Args:
            symbol (str): Symbol to analyze
            
        Returns:
            dict: Performance metrics for the symbol
        """
        self._validate_symbol(symbol)
        
        try:
            trades = self.get_trades_by_symbol(symbol)
            
            if not trades:
                return {'symbol': symbol.upper(), 'trades': 0, 'message': 'No trades found'}
            
            buy_trades = [t for t in trades if t['trade_type'] in ['buy']]
            sell_trades = [t for t in trades if t['trade_type'] in ['sell']]
            
            performance = {
                'symbol': symbol.upper(),
                'total_trades': len(trades),
                'buy_trades': len(buy_trades),
                'sell_trades': len(sell_trades),
                'total_quantity_bought': sum(t['quantity'] for t in buy_trades),
                'total_quantity_sold': sum(t['quantity'] for t in sell_trades),
                'average_buy_price': 0.0,
                'average_sell_price': 0.0,
                'total_volume': sum(t['entry_price'] * t['quantity'] for t in trades)
            }
            
            if buy_trades:
                total_buy_value = sum(t['entry_price'] * t['quantity'] for t in buy_trades)
                total_buy_quantity = performance['total_quantity_bought']
                performance['average_buy_price'] = total_buy_value / total_buy_quantity if total_buy_quantity > 0 else 0
            
            if sell_trades:
                total_sell_value = sum(t['entry_price'] * t['quantity'] for t in sell_trades)
                total_sell_quantity = performance['total_quantity_sold']
                performance['average_sell_price'] = total_sell_value / total_sell_quantity if total_sell_quantity > 0 else 0
            
            return performance
        except Exception as e:
            raise TradingJournalError(f"Failed to calculate symbol performance: {str(e)}")
    
    # ==================== VALIDATION METHODS ====================
    
    def _validate_symbol(self, symbol: str) -> None:
        """
        Validate trading symbol.
        
        Args:
            symbol (str): Symbol to validate
            
        Raises:
            TradingJournalError: If symbol is invalid
        """
        if not symbol or not isinstance(symbol, str) or not symbol.strip():
            raise TradingJournalError("Symbol is required and cannot be empty")
        
        if len(symbol.strip()) > 20:
            raise TradingJournalError("Symbol cannot be longer than 20 characters")
    
    def _validate_asset_type(self, asset_type: str) -> None:
        """
        Validate asset type.
        
        Args:
            asset_type (str): Asset type to validate
            
        Raises:
            TradingJournalError: If asset type is invalid
        """
        if not asset_type or not isinstance(asset_type, str):
            raise TradingJournalError("Asset type is required")
        
        if asset_type.lower() not in self.valid_asset_types:
            valid_types = ', '.join(sorted(self.valid_asset_types))
            raise TradingJournalError(f"Asset type must be one of: {valid_types}")
    
    def _validate_date(self, date: str) -> None:
        """
        Validate date format (YYYY-MM-DD).
        
        Args:
            date (str): Date string to validate
            
        Raises:
            TradingJournalError: If date format is invalid
        """
        if not date or not isinstance(date, str):
            raise TradingJournalError("Date is required and must be a string")
        
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise TradingJournalError("Date must be in YYYY-MM-DD format")
    
    def _validate_price(self, price: float) -> None:
        """
        Validate price (must be positive).
        
        Args:
            price (float): Price to validate
            
        Raises:
            TradingJournalError: If price is invalid
        """
        if not isinstance(price, (int, float)) or price <= 0:
            raise TradingJournalError("Price must be a positive number")
    
    def _validate_quantity(self, quantity: float) -> None:
        """
        Validate quantity (must be positive).
        
        Args:
            quantity (float): Quantity to validate
            
        Raises:
            TradingJournalError: If quantity is invalid
        """
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            raise TradingJournalError("Quantity must be a positive number")
    
    def _validate_trade_type(self, trade_type: str) -> None:
        """
        Validate trade type.
        
        Args:
            trade_type (str): Trade type to validate
            
        Raises:
            TradingJournalError: If trade type is invalid
        """
        if not trade_type or not isinstance(trade_type, str):
            raise TradingJournalError("Trade type is required")
        
        if trade_type.lower() not in self.valid_trade_types:
            valid_types = ', '.join(sorted(self.valid_trade_types))
            raise TradingJournalError(f"Trade type must be one of: {valid_types}")


if __name__ == "__main__":
    """
    Demonstration of the TradingJournal functionality.
    This runs when the module is executed directly.
    """
    print("=" * 60)
    print("TRADING JOURNAL MODULE DEMONSTRATION")
    print("=" * 60)
    
    # Initialize database and trading journal
    from db import AlphaDatabase
    
    # Reduce logging noise for demo
    logging.getLogger('db').setLevel(logging.WARNING)
    
    db = AlphaDatabase()
    tj = TradingJournal(db)
    
    print("\n📈 TRADE MANAGEMENT DEMO")
    print("-" * 40)
    
    # Add sample trades
    print("📝 Adding trades...")
    trade1_id = tj.add_trade("AAPL", "stock", "2024-01-20", 150.25, 10, "buy", 
                            "Initial position", "tech,growth")
    trade2_id = tj.add_trade("BTC-USD", "crypto", "2024-01-21", 42500.00, 0.5, "buy",
                            "Bitcoin investment", "crypto,hodl")
    trade3_id = tj.add_trade("SPY", "etf", "2024-01-22", 480.75, 5, "buy",
                            "Market exposure", "index,diversification")
    
    print(f"✅ Added trades with IDs: {trade1_id}, {trade2_id}, {trade3_id}")
    
    # List all trades
    print("\n📋 Current trades:")
    trades = tj.get_all_trades()
    for trade in trades[-3:]:  # Show last 3
        print(f"  ID {trade['id']}: {trade['symbol']} | {trade['trade_type']} | "
              f"{trade['quantity']}@${trade['entry_price']:.2f} | {trade['entry_date']}")
    
    # Update a trade
    print(f"\n🔄 Updating trade {trade1_id}...")
    tj.update_trade(trade1_id, quantity=15, notes="Increased position size")
    updated_trade = tj.get_trade(trade1_id)
    print(f"✅ Updated: {updated_trade['quantity']} shares - {updated_trade['notes']}")
    
    print("\n🔍 SEARCH AND FILTER DEMO")
    print("-" * 40)
    
    # Filter by symbol
    aapl_trades = tj.get_trades_by_symbol("AAPL")
    print(f"🍎 AAPL trades: {len(aapl_trades)} found")
    
    # Filter by asset type
    stock_trades = tj.get_trades_by_asset_type("stock")
    print(f"📊 Stock trades: {len(stock_trades)} found")
    
    # Filter by trade type
    buy_trades = tj.get_trades_by_type("buy")
    print(f"🛒 Buy trades: {len(buy_trades)} found")
    
    # Search by tags
    crypto_tagged = tj.search_trades_by_tags("crypto")
    print(f"🪙 Crypto-tagged trades: {len(crypto_tagged)} found")
    
    # Date range filter
    recent_trades = tj.get_trades_by_date_range("2024-01-20", "2024-01-22")
    print(f"📅 Recent trades (Jan 20-22): {len(recent_trades)} found")
    
    print("\n📊 ANALYTICS DEMO")
    print("-" * 40)
    
    # Trade summary
    summary = tj.get_trade_summary()
    print(f"📈 Trade Summary:")
    print(f"  Total trades: {summary['total_trades']}")
    print(f"  Unique symbols: {summary['unique_symbols']}")
    print(f"  Total volume: ${summary['total_volume']:,.2f}")
    print(f"  By trade type: {summary['by_trade_type']}")
    print(f"  By asset type: {summary['by_asset_type']}")
    
    # Symbol performance
    aapl_performance = tj.get_symbol_performance("AAPL")
    print(f"\n🍎 AAPL Performance:")
    print(f"  Total trades: {aapl_performance['total_trades']}")
    print(f"  Quantity bought: {aapl_performance['total_quantity_bought']}")
    print(f"  Average buy price: ${aapl_performance['average_buy_price']:.2f}")
    print(f"  Total volume: ${aapl_performance['total_volume']:,.2f}")
    
    print("\n🧪 VALIDATION DEMO")
    print("-" * 40)
    
    # Test validation errors
    try:
        tj.add_trade("", "stock", "2024-01-01", 100.0, 10, "buy")
    except TradingJournalError as e:
        print(f"✅ Symbol validation: {e}")
    
    try:
        tj.add_trade("TEST", "invalid", "2024-01-01", 100.0, 10, "buy")
    except TradingJournalError as e:
        print(f"✅ Asset type validation: {e}")
    
    try:
        tj.add_trade("TEST", "stock", "invalid-date", 100.0, 10, "buy")
    except TradingJournalError as e:
        print(f"✅ Date validation: {e}")
    
    try:
        tj.add_trade("TEST", "stock", "2024-01-01", -100.0, 10, "buy")
    except TradingJournalError as e:
        print(f"✅ Price validation: {e}")
    
    try:
        tj.add_trade("TEST", "stock", "2024-01-01", 100.0, -10, "buy")
    except TradingJournalError as e:
        print(f"✅ Quantity validation: {e}")
    
    try:
        tj.add_trade("TEST", "stock", "2024-01-01", 100.0, 10, "invalid")
    except TradingJournalError as e:
        print(f"✅ Trade type validation: {e}")
    
    print("\n🗑️ DELETION DEMO")
    print("-" * 40)
    
    # Delete a trade
    print(f"🗑️ Deleting trade {trade3_id}...")
    tj.delete_trade(trade3_id)
    print("✅ Trade deleted")
    
    # Final summary
    final_summary = tj.get_trade_summary()
    
    print(f"\n📈 FINAL SUMMARY")
    print("-" * 40)
    print(f"📊 Current trades: {final_summary['total_trades']}")
    print(f"💰 Total volume: ${final_summary['total_volume']:,.2f}")
    print(f"🎯 Unique symbols: {final_summary['unique_symbols']}")
    
    print("\n" + "=" * 60)
    print("✅ Trading Journal module demonstration completed!")
    print("The TradingJournal API is ready for use by GUI and other modules.")
    print("=" * 60) 