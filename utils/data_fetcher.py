"""
Enhanced Data Fetcher with robust error handling and caching
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
import pytz
from typing import Optional, List, Dict, Union

logger = logging.getLogger(__name__)

class DataFetcher:
    """Enhanced data fetcher with error handling and rate limiting"""
    
    def __init__(self, rate_limit_delay=0.1):
        """
        Initialize data fetcher
        
        Args:
            rate_limit_delay (float): Delay between API calls in seconds
        """
        self.rate_limit_delay = rate_limit_delay
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
        self.ist = pytz.timezone('Asia/Kolkata')
        
        # NSE stock symbols
        self.nse_stocks = [
            "BTC-USD","RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
            "INFOSYS.NS", "SBIN.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS",
            "LT.NS", "KOTAKBANK.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
            "TITAN.NS", "ONGC.NS", "NTPC.NS", "ASIANPAINT.NS", "M&M.NS",
            "NESTLEIND.NS", "TATAMOTORS.NS", "ULTRACEMCO.NS", "ADANIPORTS.NS",
            "WIPRO.NS", "POWERGRID.NS", "BAJFINANCE.NS", "COALINDIA.NS",
            "HDFCLIFE.NS", "GRASIM.NS", "TECHM.NS", "INDUSINDBK.NS",
            "TATASTEEL.NS", "BAJAJFINSV.NS", "AXISBANK.NS", "CIPLA.NS",
            "EICHERMOT.NS", "DRREDDY.NS", "JSWSTEEL.NS", "BRITANNIA.NS",
            "DIVISLAB.NS", "ADANITRANS.NS", "APOLLOHOSP.NS", "HINDALCO.NS",
            "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "GODREJCP.NS", "SIEMENS.NS",
            "PIDILITIND.NS", "VEDL.NS", "SHREECEM.NS", "DABUR.NS",
            "BERGEPAINT.NS", "MARICO.NS", "COLPAL.NS", "BANKBARODA.NS",
            "TATACONSUM.NS", "AMBUJACEM.NS", "LUPIN.NS", "GAIL.NS",
            "TRENT.NS", "TORNTPHARM.NS", "HAVELLS.NS", "IDEA.NS",
            "MCDOWELL-N.NS", "PAGEIND.NS", "LTIM.NS", "SBILIFE.NS",
            "MOTHERSON.NS", "ADANIENT.NS", "JUBLFOOD.NS", "CONCOR.NS",
            "BEL.NS", "INDUSTOWER.NS", "MPHASIS.NS", "INDIGO.NS",
            "NAUKRI.NS", "BOSCHLTD.NS", "LICHSGFIN.NS", "PNB.NS",
            "OFSS.NS", "PERSISTENT.NS", "POLYCAB.NS", "ALKEM.NS",
            "INDIANB.NS", "CUMMINSIND.NS", "BIOCON.NS", "BALKRISIND.NS",
            "CHAMBLFERT.NS", "MRF.NS", "AUROPHARMA.NS", "RBLBANK.NS",
            "CHOLAFIN.NS", "GMRINFRA.NS", "FEDERALBNK.NS", "MANAPPURAM.NS",
            "RECLTD.NS", "NATIONALUM.NS", "NMDC.NS", "SAIL.NS",
            "JINDALSTEL.NS", "ZEEL.NS", "ASHOKLEY.NS", "VOLTAS.NS"
        ]
        
        logger.info(f"Data fetcher initialized with {len(self.nse_stocks)} NSE stocks")
    
    def get_stock_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Fetch stock data with caching and error handling
        
        Args:
            symbol (str): Stock symbol
            period (str): Data period (1y, 6mo, 3mo, etc.)
            interval (str): Data interval (1d, 1h, 15m, etc.)
            
        Returns:
            pd.DataFrame or None: Stock data or None if failed
        """
        cache_key = f"{symbol}_{period}_{interval}"
        
        # Check cache
        if self._is_cached_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No data received for {symbol}")
                return None
            
            # Clean data
            data = self._clean_data(data)
            
            # Cache data
            self.cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now(self.ist)
            }
            
            logger.debug(f"Fetched {len(data)} rows for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def get_multiple_stocks_data(self, symbols: List[str], period: str = "1y", interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks
        
        Args:
            symbols (List[str]): List of stock symbols
            period (str): Data period
            interval (str): Data interval
            
        Returns:
            Dict[str, pd.DataFrame]: Dictionary of symbol -> data
        """
        results = {}
        
        for symbol in symbols:
            data = self.get_stock_data(symbol, period, interval)
            if data is not None:
                results[symbol] = data
        
        logger.info(f"Fetched data for {len(results)}/{len(symbols)} symbols")
        return results
    
    def get_nse_stocks_data(self, limit: int = 50, period: str = "1y", interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Fetch data for NSE stocks
        
        Args:
            limit (int): Maximum number of stocks to fetch
            period (str): Data period
            interval (str): Data interval
            
        Returns:
            Dict[str, pd.DataFrame]: Dictionary of symbol -> data
        """
        symbols = self.nse_stocks[:limit]
        return self.get_multiple_stocks_data(symbols, period, interval)
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            float or None: Current price or None if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                return float(data['Close'].iloc[-1])
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate stock data
        
        Args:
            data (pd.DataFrame): Raw stock data
            
        Returns:
            pd.DataFrame: Cleaned data
        """
        if data.empty:
            return data
        
        # Remove rows with all NaN values
        data = data.dropna(how='all')
        
        # Forward fill missing values
        data = data.ffill()
        
        # Ensure we have required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in data.columns:
                logger.warning(f"Missing column {col} in data")
                return pd.DataFrame()
        
        # Remove rows with zero or negative prices
        data = data[(data['Close'] > 0) & (data['High'] > 0) & (data['Low'] > 0) & (data['Open'] > 0)]
        
        # Ensure High >= Low
        data = data[data['High'] >= data['Low']]
        
        return data
    
    def _is_cached_valid(self, cache_key: str) -> bool:
        """
        Check if cached data is still valid
        
        Args:
            cache_key (str): Cache key
            
        Returns:
            bool: True if cache is valid
        """
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key]['timestamp']
        current_time = datetime.now(self.ist)
        
        return (current_time - cache_time) < self.cache_duration
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        current_time = datetime.now(self.ist)
        valid_entries = 0
        
        for cache_key, cache_data in self.cache.items():
            if (current_time - cache_data['timestamp']) < self.cache_duration:
                valid_entries += 1
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60
        }
