"""
positions.py

This module contains open position tracking logic for the alpha application.
Includes monitoring current positions, calculating P&L, and real-time value updates.
Provides a clean API layer over the database with live market data integration.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

# Import the database layer and data fetching functions
from db import AlphaDatabase
from datafetch import get_market_price, DataFetchError

# Configure logging
logger = logging.getLogger(__name__)


class PositionsError(Exception):
    """Custom exception for position management operations."""
    pass


class OpenPositions:
    """
    Open Positions management class for the Alpha application.
    
    Provides a high-level API for tracking and monitoring open positions,
    fetching live prices, and calculating real-time P&L.
    Built on top of the AlphaDatabase layer with integrated data fetching.
    """
    
    def __init__(self, database: AlphaDatabase):
        """
        Initialize the OpenPositions manager.
        
        Args:
            database (AlphaDatabase): Instance of the database manager
        """
        self.db = database
        self.valid_asset_types = {'stock', 'crypto', 'etf', 'forex', 'commodity', 'bond', 'option', 'future'}
        logger.info("OpenPositions manager initialized")
    
    # ==================== POSITION MANAGEMENT ====================
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions from the database.
        
        Returns:
            list: List of position dictionaries
        """
        try:
            return self.db.get_all_positions()
        except Exception as e:
            raise PositionsError(f"Failed to retrieve positions: {str(e)}")
    
    def get_position(self, position_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific position by ID.
        
        Args:
            position_id (int): ID of the position
            
        Returns:
            dict or None: Position data, None if not found
        """
        try:
            return self.db.get_position(position_id)
        except Exception as e:
            raise PositionsError(f"Failed to retrieve position: {str(e)}")
    
    def get_position_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol (str): Symbol to search for
            
        Returns:
            dict or None: Position data, None if not found
        """
        try:
            return self.db.get_position_by_symbol(symbol.upper())
        except Exception as e:
            raise PositionsError(f"Failed to retrieve position by symbol: {str(e)}")
    
    def get_positions_by_asset_type(self, asset_type: str) -> List[Dict[str, Any]]:
        """
        Get all positions for a specific asset type.
        
        Args:
            asset_type (str): Asset type to filter by
            
        Returns:
            list: List of position dictionaries
        """
        if asset_type.lower() not in self.valid_asset_types:
            valid_types = ', '.join(sorted(self.valid_asset_types))
            raise PositionsError(f"Asset type must be one of: {valid_types}")
        
        try:
            positions = self.get_all_positions()
            return [pos for pos in positions if pos['asset_type'].lower() == asset_type.lower()]
        except Exception as e:
            raise PositionsError(f"Failed to filter positions by asset type: {str(e)}")
    
    # ==================== LIVE PRICE INTEGRATION ====================
    
    def get_position_with_live_price(self, position: Dict[str, Any], exchange: str = "binance") -> Dict[str, Any]:
        """
        Enhance position data with live market price and P&L calculations.
        
        Args:
            position (dict): Position data from database
            exchange (str): Exchange for crypto prices (default: 'binance')
            
        Returns:
            dict: Enhanced position data with live price and P&L
        """
        if not position:
            raise PositionsError("Position data is required")
        
        # Create a copy to avoid modifying original
        enhanced_position = position.copy()
        
        try:
            # Fetch live price
            live_price = get_market_price(
                symbol=position['symbol'],
                asset_type=position['asset_type'],
                exchange=exchange
            )
            
            # Calculate P&L metrics
            entry_price = float(position['entry_price'])
            quantity = float(position['quantity'])
            
            # Market value calculations
            entry_value = entry_price * quantity
            current_value = live_price * quantity
            
            # P&L calculations
            unrealized_pnl = current_value - entry_value
            unrealized_pnl_percent = (unrealized_pnl / entry_value) * 100 if entry_value > 0 else 0
            
            # Add calculated fields
            enhanced_position.update({
                'live_price': live_price,
                'entry_value': entry_value,
                'current_value': current_value,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_percent': unrealized_pnl_percent,
                'price_change': live_price - entry_price,
                'price_change_percent': ((live_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0,
                'last_updated': datetime.now().isoformat()
            })
            
            logger.info(f"Enhanced {position['symbol']} with live price ${live_price:.2f}, P&L: ${unrealized_pnl:.2f}")
            return enhanced_position
            
        except DataFetchError as e:
            logger.warning(f"Failed to fetch live price for {position['symbol']}: {e}")
            # Return position with error information
            enhanced_position.update({
                'live_price': None,
                'entry_value': float(position['entry_price']) * float(position['quantity']),
                'current_value': None,
                'unrealized_pnl': None,
                'unrealized_pnl_percent': None,
                'price_change': None,
                'price_change_percent': None,
                'price_error': str(e),
                'last_updated': datetime.now().isoformat()
            })
            return enhanced_position
        
        except Exception as e:
            raise PositionsError(f"Failed to enhance position with live data: {str(e)}")
    
    def get_all_positions_with_live_prices(self, exchange: str = "binance") -> List[Dict[str, Any]]:
        """
        Get all positions enhanced with live prices and P&L calculations.
        
        Args:
            exchange (str): Exchange for crypto prices (default: 'binance')
            
        Returns:
            list: List of enhanced position dictionaries
        """
        try:
            positions = self.get_all_positions()
            enhanced_positions = []
            
            for position in positions:
                enhanced_position = self.get_position_with_live_price(position, exchange)
                enhanced_positions.append(enhanced_position)
            
            logger.info(f"Enhanced {len(enhanced_positions)} positions with live data")
            return enhanced_positions
            
        except Exception as e:
            raise PositionsError(f"Failed to get positions with live prices: {str(e)}")
    
    # ==================== P&L ANALYTICS ====================
    
    def calculate_portfolio_pnl(self, exchange: str = "binance") -> Dict[str, Any]:
        """
        Calculate overall portfolio P&L metrics.
        
        Args:
            exchange (str): Exchange for crypto prices (default: 'binance')
            
        Returns:
            dict: Portfolio P&L summary
        """
        try:
            enhanced_positions = self.get_all_positions_with_live_prices(exchange)
            
            portfolio_summary = {
                'total_positions': len(enhanced_positions),
                'total_entry_value': 0.0,
                'total_current_value': 0.0,
                'total_unrealized_pnl': 0.0,
                'total_unrealized_pnl_percent': 0.0,
                'positions_with_data': 0,
                'positions_with_errors': 0,
                'best_performer': None,
                'worst_performer': None,
                'by_asset_type': {},
                'last_updated': datetime.now().isoformat()
            }
            
            valid_positions = []
            
            for position in enhanced_positions:
                # Track positions by asset type
                asset_type = position['asset_type']
                if asset_type not in portfolio_summary['by_asset_type']:
                    portfolio_summary['by_asset_type'][asset_type] = {
                        'count': 0,
                        'entry_value': 0.0,
                        'current_value': 0.0,
                        'unrealized_pnl': 0.0
                    }
                
                portfolio_summary['by_asset_type'][asset_type]['count'] += 1
                portfolio_summary['by_asset_type'][asset_type]['entry_value'] += position['entry_value']
                
                if position.get('price_error'):
                    portfolio_summary['positions_with_errors'] += 1
                    continue
                
                if position['current_value'] is not None:
                    portfolio_summary['positions_with_data'] += 1
                    portfolio_summary['total_entry_value'] += position['entry_value']
                    portfolio_summary['total_current_value'] += position['current_value']
                    portfolio_summary['total_unrealized_pnl'] += position['unrealized_pnl']
                    
                    # Update asset type totals
                    portfolio_summary['by_asset_type'][asset_type]['current_value'] += position['current_value']
                    portfolio_summary['by_asset_type'][asset_type]['unrealized_pnl'] += position['unrealized_pnl']
                    
                    valid_positions.append(position)
            
            # Calculate overall percentage
            if portfolio_summary['total_entry_value'] > 0:
                portfolio_summary['total_unrealized_pnl_percent'] = (
                    portfolio_summary['total_unrealized_pnl'] / portfolio_summary['total_entry_value']
                ) * 100
            
            # Find best and worst performers
            if valid_positions:
                portfolio_summary['best_performer'] = max(
                    valid_positions, 
                    key=lambda x: x['unrealized_pnl_percent']
                )
                portfolio_summary['worst_performer'] = min(
                    valid_positions, 
                    key=lambda x: x['unrealized_pnl_percent']
                )
            
            # Calculate asset type percentages
            for asset_type, data in portfolio_summary['by_asset_type'].items():
                if data['entry_value'] > 0:
                    data['unrealized_pnl_percent'] = (data['unrealized_pnl'] / data['entry_value']) * 100
                else:
                    data['unrealized_pnl_percent'] = 0.0
            
            return portfolio_summary
            
        except Exception as e:
            raise PositionsError(f"Failed to calculate portfolio P&L: {str(e)}")
    
    def get_top_performers(self, limit: int = 5, exchange: str = "binance") -> List[Dict[str, Any]]:
        """
        Get top performing positions by P&L percentage.
        
        Args:
            limit (int): Number of top performers to return
            exchange (str): Exchange for crypto prices (default: 'binance')
            
        Returns:
            list: Top performing positions sorted by P&L percentage
        """
        try:
            enhanced_positions = self.get_all_positions_with_live_prices(exchange)
            
            # Filter out positions without valid P&L data
            valid_positions = [
                pos for pos in enhanced_positions 
                if pos.get('unrealized_pnl_percent') is not None
            ]
            
            # Sort by P&L percentage (descending)
            sorted_positions = sorted(
                valid_positions, 
                key=lambda x: x['unrealized_pnl_percent'], 
                reverse=True
            )
            
            return sorted_positions[:limit]
            
        except Exception as e:
            raise PositionsError(f"Failed to get top performers: {str(e)}")
    
    def get_positions_summary(self, exchange: str = "binance") -> Dict[str, Any]:
        """
        Get a comprehensive summary of all positions.
        
        Args:
            exchange (str): Exchange for crypto prices (default: 'binance')
            
        Returns:
            dict: Comprehensive positions summary
        """
        try:
            portfolio_pnl = self.calculate_portfolio_pnl(exchange)
            top_performers = self.get_top_performers(3, exchange)
            
            summary = {
                'portfolio': portfolio_pnl,
                'top_performers': top_performers,
                'summary_generated': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            raise PositionsError(f"Failed to generate positions summary: {str(e)}")
    
    # ==================== POSITION CRUD OPERATIONS ====================
    
    def add_position(self, symbol: str, asset_type: str, entry_date: str, 
                    entry_price: float, quantity: float) -> int:
        """
        Add a new position to the portfolio.
        
        Args:
            symbol (str): Trading symbol (e.g., 'AAPL', 'BTC')
            asset_type (str): Type of asset (stock, crypto, etf, etc.)
            entry_date (str): Entry date in YYYY-MM-DD format
            entry_price (float): Entry price per unit
            quantity (float): Number of units/shares
            
        Returns:
            int: ID of the newly created position
            
        Raises:
            PositionsError: If validation fails or database operation fails
        """
        # Validate inputs
        if not symbol or not symbol.strip():
            raise PositionsError("Symbol is required")
        
        symbol = symbol.upper().strip()
        
        if asset_type.lower() not in self.valid_asset_types:
            valid_types = ', '.join(sorted(self.valid_asset_types))
            raise PositionsError(f"Asset type must be one of: {valid_types}")
        
        if entry_price <= 0:
            raise PositionsError("Entry price must be greater than 0")
        
        if quantity <= 0:
            raise PositionsError("Quantity must be greater than 0")
        
        # Validate date format
        try:
            datetime.strptime(entry_date, '%Y-%m-%d')
        except ValueError:
            raise PositionsError("Entry date must be in YYYY-MM-DD format")
        
        try:
            position_id = self.db.add_position(
                symbol=symbol,
                asset_type=asset_type.lower(),
                entry_date=entry_date,
                entry_price=entry_price,
                quantity=quantity
            )
            
            logger.info(f"Added position: {symbol} ({asset_type}) - {quantity} @ ${entry_price}")
            return position_id
            
        except Exception as e:
            raise PositionsError(f"Failed to add position: {str(e)}")
    
    def update_position(self, position_id: int, symbol: str = None, asset_type: str = None,
                       entry_date: str = None, entry_price: float = None, 
                       quantity: float = None) -> bool:
        """
        Update an existing position.
        
        Args:
            position_id (int): ID of the position to update
            symbol (str, optional): New trading symbol
            asset_type (str, optional): New asset type
            entry_date (str, optional): New entry date in YYYY-MM-DD format
            entry_price (float, optional): New entry price per unit
            quantity (float, optional): New quantity
            
        Returns:
            bool: True if update was successful
            
        Raises:
            PositionsError: If validation fails or database operation fails
        """
        # Check if position exists
        existing_position = self.get_position(position_id)
        if not existing_position:
            raise PositionsError(f"Position with ID {position_id} not found")
        
        # Validate inputs if provided
        if symbol is not None:
            if not symbol or not symbol.strip():
                raise PositionsError("Symbol cannot be empty")
            symbol = symbol.upper().strip()
        
        if asset_type is not None:
            if asset_type.lower() not in self.valid_asset_types:
                valid_types = ', '.join(sorted(self.valid_asset_types))
                raise PositionsError(f"Asset type must be one of: {valid_types}")
            asset_type = asset_type.lower()
        
        if entry_price is not None and entry_price <= 0:
            raise PositionsError("Entry price must be greater than 0")
        
        if quantity is not None and quantity <= 0:
            raise PositionsError("Quantity must be greater than 0")
        
        if entry_date is not None:
            try:
                datetime.strptime(entry_date, '%Y-%m-%d')
            except ValueError:
                raise PositionsError("Entry date must be in YYYY-MM-DD format")
        
        try:
            # Build kwargs for only non-None values
            update_kwargs = {'position_id': position_id}
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
            
            success = self.db.update_position(**update_kwargs)
            
            if success:
                logger.info(f"Updated position ID {position_id}")
            else:
                logger.warning(f"Position ID {position_id} not found for update")
            
            return success
            
        except Exception as e:
            raise PositionsError(f"Failed to update position: {str(e)}")
    
    def delete_position(self, position_id: int) -> bool:
        """
        Delete a position from the portfolio.
        
        Args:
            position_id (int): ID of the position to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            PositionsError: If database operation fails
        """
        # Check if position exists
        existing_position = self.get_position(position_id)
        if not existing_position:
            raise PositionsError(f"Position with ID {position_id} not found")
        
        try:
            success = self.db.delete_position(position_id)
            
            if success:
                logger.info(f"Deleted position ID {position_id} ({existing_position['symbol']})")
            else:
                logger.warning(f"Position ID {position_id} not found for deletion")
            
            return success
            
        except Exception as e:
            raise PositionsError(f"Failed to delete position: {str(e)}")


if __name__ == "__main__":
    """
    Demonstration of the OpenPositions functionality.
    This runs when the module is executed directly.
    """
    print("=" * 60)
    print("OPEN POSITIONS MODULE DEMONSTRATION")
    print("=" * 60)
    
    # Initialize database and positions manager
    from db import AlphaDatabase
    
    # Reduce logging noise for demo
    logging.getLogger('db').setLevel(logging.WARNING)
    
    db = AlphaDatabase()
    op = OpenPositions(db)
    
    print("\n📊 POSITIONS SETUP")
    print("-" * 40)
    
    # Add some test positions if none exist
    existing_positions = op.get_all_positions()
    if not existing_positions:
        print("📝 Adding test positions...")
        # Add test positions
        db.add_position("AAPL", "stock", "2024-01-15", 180.00, 50)
        db.add_position("BTC", "crypto", "2024-01-16", 45000.00, 0.25)
        db.add_position("SPY", "etf", "2024-01-17", 475.00, 20)
        print("✅ Test positions added")
    else:
        print(f"📊 Found {len(existing_positions)} existing positions")
    
    print("\n📋 BASIC POSITION LISTING")
    print("-" * 40)
    
    # List all positions
    positions = op.get_all_positions()
    print(f"Total positions: {len(positions)}")
    
    for position in positions:
        entry_value = position['entry_price'] * position['quantity']
        print(f"  {position['symbol']} ({position['asset_type']}): {position['quantity']} @ ${position['entry_price']:.2f} = ${entry_value:,.2f}")
    
    print("\n💰 LIVE PRICES AND P&L CALCULATION")
    print("-" * 40)
    
    # Get positions with live prices
    print("🔄 Fetching live prices...")
    enhanced_positions = op.get_all_positions_with_live_prices()
    
    for position in enhanced_positions:
        symbol = position['symbol']
        asset_type = position['asset_type']
        
        if position.get('price_error'):
            print(f"❌ {symbol} ({asset_type}): {position['price_error']}")
        else:
            live_price = position.get('live_price', 'N/A')
            entry_price = position['entry_price']
            quantity = position['quantity']
            pnl = position.get('unrealized_pnl', 0)
            pnl_percent = position.get('unrealized_pnl_percent', 0)
            
            pnl_color = "📈" if pnl >= 0 else "📉"
            print(f"{pnl_color} {symbol}: ${entry_price:.2f} → ${live_price:.2f} | "
                  f"P&L: ${pnl:.2f} ({pnl_percent:+.1f}%)")
    
    print("\n🔍 FILTERING AND SEARCH")
    print("-" * 40)
    
    # Filter by asset type
    try:
        stock_positions = op.get_positions_by_asset_type("stock")
        print(f"📊 Stock positions: {len(stock_positions)} found")
        
        crypto_positions = op.get_positions_by_asset_type("crypto")
        print(f"🪙 Crypto positions: {len(crypto_positions)} found")
    except PositionsError as e:
        print(f"❌ Filtering error: {e}")
    
    # Get position by symbol
    try:
        aapl_position = op.get_position_by_symbol("AAPL")
        if aapl_position:
            print(f"🍎 AAPL position found: {aapl_position['quantity']} shares")
        else:
            print("🍎 AAPL position not found")
    except PositionsError as e:
        print(f"❌ Symbol search error: {e}")
    
    print("\n📊 PORTFOLIO ANALYTICS")
    print("-" * 40)
    
    # Calculate portfolio P&L
    try:
        portfolio_pnl = op.calculate_portfolio_pnl()
        
        print(f"📈 Portfolio Summary:")
        print(f"  Total positions: {portfolio_pnl['total_positions']}")
        print(f"  Positions with data: {portfolio_pnl['positions_with_data']}")
        print(f"  Entry value: ${portfolio_pnl['total_entry_value']:,.2f}")
        print(f"  Current value: ${portfolio_pnl['total_current_value']:,.2f}")
        print(f"  Unrealized P&L: ${portfolio_pnl['total_unrealized_pnl']:,.2f}")
        print(f"  P&L percentage: {portfolio_pnl['total_unrealized_pnl_percent']:+.2f}%")
        
        # Asset type breakdown
        print(f"\n📊 By Asset Type:")
        for asset_type, data in portfolio_pnl['by_asset_type'].items():
            if data['count'] > 0:
                print(f"  {asset_type}: {data['count']} positions, P&L: ${data['unrealized_pnl']:,.2f} ({data['unrealized_pnl_percent']:+.1f}%)")
        
        # Best/worst performers
        if portfolio_pnl['best_performer']:
            best = portfolio_pnl['best_performer']
            print(f"\n🏆 Best performer: {best['symbol']} ({best['unrealized_pnl_percent']:+.1f}%)")
        
        if portfolio_pnl['worst_performer']:
            worst = portfolio_pnl['worst_performer']
            print(f"📉 Worst performer: {worst['symbol']} ({worst['unrealized_pnl_percent']:+.1f}%)")
        
    except PositionsError as e:
        print(f"❌ Portfolio analysis error: {e}")
    
    print("\n🏆 TOP PERFORMERS")
    print("-" * 40)
    
    try:
        top_performers = op.get_top_performers(3)
        for i, position in enumerate(top_performers, 1):
            pnl_percent = position['unrealized_pnl_percent']
            pnl = position['unrealized_pnl']
            print(f"{i}. {position['symbol']}: {pnl_percent:+.2f}% (${pnl:+.2f})")
    except PositionsError as e:
        print(f"❌ Top performers error: {e}")
    
    print("\n📋 COMPREHENSIVE SUMMARY")
    print("-" * 40)
    
    try:
        summary = op.get_positions_summary()
        portfolio = summary['portfolio']
        
        print(f"💼 Portfolio Overview:")
        print(f"  Total Value: ${portfolio['total_current_value']:,.2f}")
        print(f"  Total P&L: ${portfolio['total_unrealized_pnl']:,.2f} ({portfolio['total_unrealized_pnl_percent']:+.1f}%)")
        print(f"  Success Rate: {portfolio['positions_with_data']}/{portfolio['total_positions']} positions with data")
        
        if summary['top_performers']:
            print(f"\n🎯 Top Performer: {summary['top_performers'][0]['symbol']} "
                  f"({summary['top_performers'][0]['unrealized_pnl_percent']:+.1f}%)")
        
    except PositionsError as e:
        print(f"❌ Summary error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Open Positions module demonstration completed!")
    print("The OpenPositions API is ready for use by GUI and other modules.")
    print("=" * 60) 