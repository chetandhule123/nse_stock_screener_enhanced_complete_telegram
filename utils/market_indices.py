"""
Market Indices Data Fetcher for NSE indices
"""

import yfinance as yf
import pandas as pd
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class MarketIndices:
    """Fetch and display live market indices data"""
    
    def __init__(self):
        """Initialize market indices fetcher"""
        self.ist = pytz.timezone('Asia/Kolkata')
        
        # NSE Indices with their Yahoo Finance symbols
        self.indices = {
            "NIFTY 50": "^NSEI",
            "NIFTY BANK": "^NSEBANK",
            "SENSEX": "^BSESN",
            "NIFTY IT": "^CNXIT",
            "NIFTY AUTO": "^CNXAUTO",
            "NIFTY FMCG": "^CNXFMCG",
            "NIFTY PHARMA": "^CNXPHARMA",
            "NIFTY METAL": "^CNXMETAL"
        }
        
        logger.info(f"Market indices initialized with {len(self.indices)} indices")
    
    def get_live_indices(self) -> pd.DataFrame:
        """
        Fetch live market indices data
        
        Returns:
            pd.DataFrame: DataFrame with indices data
        """
        try:
            indices_data = []
            
            for name, symbol in self.indices.items():
                try:
                    # Fetch current data
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d", interval="1d")
                    
                    if len(hist) >= 2:
                        current_price = hist['Close'].iloc[-1]
                        previous_price = hist['Close'].iloc[-2]
                        
                        change = current_price - previous_price
                        change_pct = (change / previous_price) * 100
                        
                        indices_data.append({
                            'Name': name,
                            'Symbol': symbol,
                            'Price': round(current_price, 2),
                            'Change': round(change, 2),
                            'Change%': round(change_pct, 2)
                        })
                        
                    elif len(hist) == 1:
                        # Only current day data available
                        current_price = hist['Close'].iloc[-1]
                        
                        indices_data.append({
                            'Name': name,
                            'Symbol': symbol,
                            'Price': round(current_price, 2),
                            'Change': 0.0,
                            'Change%': 0.0
                        })
                
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {name}: {e}")
                    # Add placeholder data to maintain structure
                    indices_data.append({
                        'Name': name,
                        'Symbol': symbol,
                        'Price': 0.0,
                        'Change': 0.0,
                        'Change%': 0.0
                    })
            
            df = pd.DataFrame(indices_data)
            logger.info(f"Successfully fetched {len(df)} indices")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market indices: {e}")
            return pd.DataFrame()
    
    def get_index_data(self, index_name: str, period: str = "1y") -> pd.DataFrame:
        """
        Get historical data for a specific index
        
        Args:
            index_name (str): Name of the index
            period (str): Data period
            
        Returns:
            pd.DataFrame: Historical data
        """
        if index_name not in self.indices:
            logger.error(f"Unknown index: {index_name}")
            return pd.DataFrame()
        
        try:
            symbol = self.indices[index_name]
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            logger.info(f"Fetched {len(data)} rows for {index_name}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {index_name}: {e}")
            return pd.DataFrame()
    
    def is_market_open(self) -> bool:
        """
        Check if NSE market is currently open
        
        Returns:
            bool: True if market is open
        """
        now = datetime.now(self.ist)
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Market hours: 9:15 AM to 3:30 PM IST
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def get_market_status(self) -> dict:
        """
        Get detailed market status information
        
        Returns:
            dict: Market status information
        """
        now = datetime.now(self.ist)
        is_open = self.is_market_open()
        
        status = {
            'is_open': is_open,
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S IST'),
            'day_of_week': now.strftime('%A'),
            'status_text': '🟢 OPEN' if is_open else '🔴 CLOSED'
        }
        
        if not is_open:
            if now.weekday() >= 5:
                status['reason'] = 'Weekend'
            elif now.hour < 9 or (now.hour == 9 and now.minute < 15):
                status['reason'] = 'Before market hours'
            else:
                status['reason'] = 'After market hours'
        
        return status
