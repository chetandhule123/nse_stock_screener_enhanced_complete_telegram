"""
Range Breakout Scanner using Pine Script-inspired logic
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import pytz
from utils.data_fetcher import DataFetcher
from utils.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

class RangeBreakoutScanner:
    """Scanner for detecting range breakouts with volume confirmation"""
    
    def __init__(self):
        """Initialize range breakout scanner"""
        self.data_fetcher = DataFetcher()
        self.ist = pytz.timezone('Asia/Kolkata')
        logger.info("Range Breakout Scanner initialized")
    
    def scan(self) -> pd.DataFrame:
        """
        Execute range breakout scan
        
        Returns:
            pd.DataFrame: Scan results with breakout signals
        """
        try:
            logger.info("Starting range breakout scan")
            
            # Fetch 4h data for better range detection
            stocks_data = self.data_fetcher.get_nse_stocks_data(
                limit=50,
                period="60d",
                interval="1h"  # Will convert to 4h
            )
            
            if not stocks_data:
                logger.warning("No stock data available")
                return pd.DataFrame()
            
            results = []
            
            for symbol, data in stocks_data.items():
                try:
                    # Convert to 4h timeframe
                    data_4h = self._convert_to_4h(data)
                    
                    if len(data_4h) < 100:  # Need sufficient data
                        continue
                    
                    # Analyze for range breakout
                    breakout_data = self._analyze_range_breakout(symbol, data_4h)
                    
                    if breakout_data:
                        results.append(breakout_data)
                        
                except Exception as e:
                    logger.warning(f"Error processing {symbol}: {e}")
                    continue
            
            # Convert to DataFrame and sort
            if results:
                df = pd.DataFrame(results)
                df = df.sort_values('Breakout_Strength', ascending=False)
                logger.info(f"Range breakout scan completed: {len(df)} signals found")
                return df
            else:
                logger.info("Range breakout scan completed: No signals found")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Range breakout scan failed: {e}")
            return pd.DataFrame()
    
    def _convert_to_4h(self, data: pd.DataFrame) -> pd.DataFrame:
        """Convert 1h data to 4h timeframe"""
        try:
            resampled = data.resample('4h').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
            
            return resampled
            
        except Exception as e:
            logger.error(f"Error converting to 4h: {e}")
            return data
    
    def _analyze_range_breakout(self, symbol: str, data: pd.DataFrame) -> dict:
        """
        Analyze for range breakout patterns (Pine Script logic)
        
        Args:
            symbol (str): Stock symbol
            data (pd.DataFrame): 4h OHLCV data
            
        Returns:
            dict: Breakout signal data or None
        """
        try:
            # Calculate ATR for dynamic range detection
            atr_length = min(500, len(data) - 1)
            atr = TechnicalIndicators.calculate_atr(data, period=atr_length)
            current_atr = atr.iloc[-1]
            
            # Define range period (last 20 bars)
            range_period = min(20, len(data) // 4)
            recent_data = data.tail(range_period + 1)  # +1 for current bar
            
            # Calculate range boundaries
            range_high = recent_data['High'].iloc[:-1].max()  # Exclude current bar
            range_low = recent_data['Low'].iloc[:-1].min()   # Exclude current bar
            range_size = range_high - range_low
            
            # Current bar data
            current_bar = data.iloc[-1]
            current_close = current_bar['Close']
            current_high = current_bar['High']
            current_low = current_bar['Low']
            current_volume = current_bar['Volume']
            
            # Previous bar for confirmation
            prev_bar = data.iloc[-2]
            prev_close = prev_bar['Close']
            
            # Volume analysis
            avg_volume = data['Volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume
            
            # Breakout detection logic (Pine Script inspired)
            breakout_threshold = current_atr * 0.1  # 10% of ATR
            min_range_size = current_atr * 2  # Minimum range size
            
            # Check if range is significant enough
            if range_size < min_range_size:
                return None
            
            # Detect bullish breakout
            if (current_close > range_high + breakout_threshold and
                current_high > range_high and
                prev_close <= range_high):
                
                # Calculate breakout strength
                breakout_distance = current_close - range_high
                breakout_strength = (breakout_distance / current_atr) * 100
                
                # Price change
                price_change = ((current_close - prev_close) / prev_close) * 100
                
                # Risk-reward calculation
                stop_loss = range_low
                risk = current_close - stop_loss
                target = current_close + (risk * 2)  # 1:2 risk-reward
                
                return {
                    'Symbol': symbol.replace('.NS', ''),
                    'Breakout_Type': 'Bullish Range Breakout',
                    'Breakout_Strength': round(breakout_strength, 2),
                    'Current_Price': round(current_close, 2),
                    'Range_High': round(range_high, 2),
                    'Range_Low': round(range_low, 2),
                    'Range_Size': round(range_size, 2),
                    'Price_Change_%': round(price_change, 2),
                    'Volume_Ratio': round(volume_ratio, 2),
                    'Stop_Loss': round(stop_loss, 2),
                    'Target': round(target, 2),
                    'Risk_Reward': '1:2',
                    'ATR': round(current_atr, 2),
                    'Scan_Time': datetime.now(self.ist).strftime('%H:%M:%S')
                }
            
            # Detect bearish breakout
            elif (current_close < range_low - breakout_threshold and
                  current_low < range_low and
                  prev_close >= range_low):
                
                # Calculate breakout strength
                breakout_distance = range_low - current_close
                breakout_strength = (breakout_distance / current_atr) * 100
                
                # Price change
                price_change = ((current_close - prev_close) / prev_close) * 100
                
                # Risk-reward calculation
                stop_loss = range_high
                risk = stop_loss - current_close
                target = current_close - (risk * 2)  # 1:2 risk-reward
                
                return {
                    'Symbol': symbol.replace('.NS', ''),
                    'Breakout_Type': 'Bearish Range Breakout',
                    'Breakout_Strength': round(breakout_strength, 2),
                    'Current_Price': round(current_close, 2),
                    'Range_High': round(range_high, 2),
                    'Range_Low': round(range_low, 2),
                    'Range_Size': round(range_size, 2),
                    'Price_Change_%': round(price_change, 2),
                    'Volume_Ratio': round(volume_ratio, 2),
                    'Stop_Loss': round(stop_loss, 2),
                    'Target': round(target, 2),
                    'Risk_Reward': '1:2',
                    'ATR': round(current_atr, 2),
                    'Scan_Time': datetime.now(self.ist).strftime('%H:%M:%S')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing range breakout for {symbol}: {e}")
            return None
