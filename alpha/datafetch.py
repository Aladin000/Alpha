"""
datafetch.py

This module contains price/data API integration logic for the alpha application.
Includes fetching live market data for stocks, ETFs, and cryptocurrencies.
Provides modular, reusable functions with error handling for external API calls.
"""

import logging
from typing import Optional
import time

# Configure logging
logger = logging.getLogger(__name__)


class DataFetchError(Exception):
    """Custom exception for data fetching operations."""
    pass


def get_stock_price(symbol: str) -> float:
    """
    Fetch the current stock/ETF price using yfinance.
    
    Args:
        symbol (str): Stock/ETF symbol (e.g., 'AAPL', 'SPY')
        
    Returns:
        float: Current market price
        
    Raises:
        DataFetchError: If price fetch fails or symbol is invalid
    """
    if not symbol or not isinstance(symbol, str):
        raise DataFetchError("Symbol must be a non-empty string")
    
    symbol = symbol.upper().strip()
    
    try:
        import yfinance as yf
        
        # Create ticker object
        ticker = yf.Ticker(symbol)
        
        # Get current data
        info = ticker.info
        
        # Try multiple price fields in order of preference
        price_fields = ['currentPrice', 'regularMarketPrice', 'previousClose']
        
        for field in price_fields:
            if field in info and info[field] is not None:
                price = float(info[field])
                if price > 0:
                    logger.info(f"Fetched {symbol} price: ${price:.2f}")
                    return price
        
        # If info doesn't work, try fast_info
        try:
            fast_info = ticker.fast_info
            if hasattr(fast_info, 'last_price') and fast_info.last_price:
                price = float(fast_info.last_price)
                if price > 0:
                    logger.info(f"Fetched {symbol} price (fast): ${price:.2f}")
                    return price
        except Exception:
            pass
        
        # If all else fails, try history
        try:
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
                if price > 0:
                    logger.info(f"Fetched {symbol} price (history): ${price:.2f}")
                    return price
        except Exception:
            pass
        
        raise DataFetchError(f"No valid price data found for {symbol}")
        
    except ImportError:
        raise DataFetchError("yfinance library not available. Please install with: pip install yfinance")
    except Exception as e:
        error_msg = f"Failed to fetch price for {symbol}: {str(e)}"
        logger.error(error_msg)
        raise DataFetchError(error_msg)


def get_crypto_price(symbol: str, exchange: str = "binance") -> float:
    """
    Fetch the current cryptocurrency price using ccxt.
    
    Args:
        symbol (str): Crypto trading pair (e.g., 'BTC/USD', 'ETH/USDT')
        exchange (str): Exchange name (default: 'binance')
        
    Returns:
        float: Current market price
        
    Raises:
        DataFetchError: If price fetch fails or symbol is invalid
    """
    if not symbol or not isinstance(symbol, str):
        raise DataFetchError("Symbol must be a non-empty string")
    
    if not exchange or not isinstance(exchange, str):
        raise DataFetchError("Exchange must be a non-empty string")
    
    symbol = symbol.upper().strip()
    exchange = exchange.lower().strip()
    
    # Normalize symbol format for ccxt
    if '-' in symbol:
        symbol = symbol.replace('-', '/')
    
    # Add /USDT if no pair specified
    if '/' not in symbol:
        symbol = f"{symbol}/USDT"
    
    try:
        import ccxt
        
        # Create exchange instance
        if exchange == 'binance':
            exchange_obj = ccxt.binance({
                'sandbox': False,
                'enableRateLimit': True,
            })
        elif exchange == 'coinbase':
            exchange_obj = ccxt.coinbasepro({
                'sandbox': False,
                'enableRateLimit': True,
            })
        elif exchange == 'kraken':
            exchange_obj = ccxt.kraken({
                'sandbox': False,
                'enableRateLimit': True,
            })
        else:
            # Try to dynamically create exchange
            if hasattr(ccxt, exchange):
                exchange_class = getattr(ccxt, exchange)
                exchange_obj = exchange_class({
                    'sandbox': False,
                    'enableRateLimit': True,
                })
            else:
                raise DataFetchError(f"Unsupported exchange: {exchange}")
        
        # Fetch ticker
        ticker = exchange_obj.fetch_ticker(symbol)
        
        if not ticker or 'last' not in ticker or ticker['last'] is None:
            raise DataFetchError(f"No ticker data available for {symbol} on {exchange}")
        
        price = float(ticker['last'])
        if price <= 0:
            raise DataFetchError(f"Invalid price returned for {symbol}: {price}")
        
        logger.info(f"Fetched {symbol} price from {exchange}: ${price:.2f}")
        return price
        
    except ImportError:
        raise DataFetchError("ccxt library not available. Please install with: pip install ccxt")
    except Exception as e:
        error_msg = f"Failed to fetch crypto price for {symbol} on {exchange}: {str(e)}"
        logger.error(error_msg)
        raise DataFetchError(error_msg)


def get_market_price(symbol: str, asset_type: str, exchange: str = "binance") -> float:
    """
    Universal price fetching function that routes to appropriate API based on asset type.
    
    Args:
        symbol (str): Trading symbol
        asset_type (str): Asset type ('stock', 'crypto', 'etf', etc.)
        exchange (str): Exchange for crypto (default: 'binance')
        
    Returns:
        float: Current market price
        
    Raises:
        DataFetchError: If price fetch fails
    """
    if not symbol or not isinstance(symbol, str):
        raise DataFetchError("Symbol must be a non-empty string")
    
    if not asset_type or not isinstance(asset_type, str):
        raise DataFetchError("Asset type must be a non-empty string")
    
    asset_type = asset_type.lower().strip()
    
    try:
        if asset_type in ['stock', 'etf', 'equity']:
            return get_stock_price(symbol)
        elif asset_type in ['crypto', 'cryptocurrency']:
            return get_crypto_price(symbol, exchange)
        else:
            # Default to stock for unknown asset types
            logger.warning(f"Unknown asset type '{asset_type}', defaulting to stock API")
            return get_stock_price(symbol)
            
    except Exception as e:
        raise DataFetchError(f"Failed to fetch price for {symbol} ({asset_type}): {str(e)}")


def test_api_connectivity() -> dict:
    """
    Test connectivity to various data APIs.
    
    Returns:
        dict: Test results for each API
    """
    results = {
        'yfinance': {'available': False, 'error': None},
        'ccxt': {'available': False, 'error': None}
    }
    
    # Test yfinance
    try:
        import yfinance as yf
        # Quick test with a stable symbol
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        if info and 'symbol' in info:
            results['yfinance']['available'] = True
        else:
            results['yfinance']['error'] = "No data returned"
    except ImportError:
        results['yfinance']['error'] = "yfinance not installed"
    except Exception as e:
        results['yfinance']['error'] = str(e)
    
    # Test ccxt
    try:
        import ccxt
        # Quick test with binance
        exchange = ccxt.binance({'enableRateLimit': True})
        markets = exchange.load_markets()
        if markets:
            results['ccxt']['available'] = True
        else:
            results['ccxt']['error'] = "No markets returned"
    except ImportError:
        results['ccxt']['error'] = "ccxt not installed"
    except Exception as e:
        results['ccxt']['error'] = str(e)
    
    return results


if __name__ == "__main__":
    """
    Demonstration of the datafetch functionality.
    This runs when the module is executed directly.
    """
    print("=" * 60)
    print("DATA FETCH MODULE DEMONSTRATION")
    print("=" * 60)
    
    # Test API connectivity
    print("\n🔌 API Connectivity Test")
    print("-" * 40)
    
    connectivity = test_api_connectivity()
    for api, result in connectivity.items():
        status = "✅ Available" if result['available'] else f"❌ {result['error']}"
        print(f"{api}: {status}")
    
    # Test stock price fetching
    print("\n📈 Stock Price Fetching")
    print("-" * 40)
    
    stock_symbols = ['AAPL', 'MSFT', 'SPY']
    for symbol in stock_symbols:
        try:
            price = get_stock_price(symbol)
            print(f"✅ {symbol}: ${price:.2f}")
        except DataFetchError as e:
            print(f"❌ {symbol}: {e}")
    
    # Test crypto price fetching
    print("\n🪙 Crypto Price Fetching")
    print("-" * 40)
    
    crypto_symbols = ['BTC/USDT', 'ETH/USDT', 'BTC-USD']
    for symbol in crypto_symbols:
        try:
            price = get_crypto_price(symbol)
            print(f"✅ {symbol}: ${price:.2f}")
        except DataFetchError as e:
            print(f"❌ {symbol}: {e}")
    
    # Test universal price function
    print("\n🌐 Universal Price Fetching")
    print("-" * 40)
    
    test_cases = [
        ('AAPL', 'stock'),
        ('BTC/USDT', 'crypto'),
        ('SPY', 'etf')
    ]
    
    for symbol, asset_type in test_cases:
        try:
            price = get_market_price(symbol, asset_type)
            print(f"✅ {symbol} ({asset_type}): ${price:.2f}")
        except DataFetchError as e:
            print(f"❌ {symbol} ({asset_type}): {e}")
    
    # Test error handling
    print("\n🧪 Error Handling Test")
    print("-" * 40)
    
    error_cases = [
        ('', 'stock', 'Empty symbol'),
        ('INVALIDXYZ', 'stock', 'Invalid stock symbol'),
        ('INVALID/PAIR', 'crypto', 'Invalid crypto pair')
    ]
    
    for symbol, asset_type, description in error_cases:
        try:
            price = get_market_price(symbol, asset_type)
            print(f"❌ {description}: Unexpected success - ${price:.2f}")
        except DataFetchError as e:
            print(f"✅ {description}: Correctly caught error")
    
    print("\n" + "=" * 60)
    print("✅ Data fetch module demonstration completed!")
    print("The data fetching functions are ready for use by other modules.")
    print("=" * 60) 