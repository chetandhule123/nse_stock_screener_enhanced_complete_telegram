"""
Technical Indicators for Stock Analysis
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Collection of technical indicators for stock analysis"""
    
    @staticmethod
    def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            data (pd.DataFrame): Stock data with 'Close' column
            fast (int): Fast EMA period
            slow (int): Slow EMA period
            signal (int): Signal line EMA period
            
        Returns:
            pd.DataFrame: DataFrame with MACD indicators
        """
        try:
            if 'Close' not in data.columns:
                raise ValueError("Data must contain 'Close' column")
            
            # Calculate EMAs
            ema_fast = data['Close'].ewm(span=fast).mean()
            ema_slow = data['Close'].ewm(span=slow).mean()
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line
            signal_line = macd_line.ewm(span=signal).mean()
            
            # Calculate histogram
            histogram = macd_line - signal_line
            
            result = pd.DataFrame({
                'MACD': macd_line,
                'Signal': signal_line,
                'Histogram': histogram
            }, index=data.index)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate RSI (Relative Strength Index)
        
        Args:
            data (pd.DataFrame): Stock data with 'Close' column
            period (int): RSI period
            
        Returns:
            pd.Series: RSI values
        """
        try:
            if 'Close' not in data.columns:
                raise ValueError("Data must contain 'Close' column")
            
            delta = data['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series()
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.DataFrame, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """
        Calculate Bollinger Bands
        
        Args:
            data (pd.DataFrame): Stock data with 'Close' column
            period (int): Moving average period
            std_dev (float): Standard deviation multiplier
            
        Returns:
            pd.DataFrame: DataFrame with Bollinger Bands
        """
        try:
            if 'Close' not in data.columns:
                raise ValueError("Data must contain 'Close' column")
            
            # Calculate middle band (SMA)
            middle_band = data['Close'].rolling(window=period).mean()
            
            # Calculate standard deviation
            std = data['Close'].rolling(window=period).std()
            
            # Calculate upper and lower bands
            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)
            
            result = pd.DataFrame({
                'Upper_Band': upper_band,
                'Middle_Band': middle_band,
                'Lower_Band': lower_band
            }, index=data.index)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate ATR (Average True Range)
        
        Args:
            data (pd.DataFrame): Stock data with OHLC columns
            period (int): ATR period
            
        Returns:
            pd.Series: ATR values
        """
        try:
            required_cols = ['High', 'Low', 'Close']
            if not all(col in data.columns for col in required_cols):
                raise ValueError("Data must contain High, Low, Close columns")
            
            # Calculate True Range
            prev_close = data['Close'].shift(1)
            
            tr1 = data['High'] - data['Low']
            tr2 = abs(data['High'] - prev_close)
            tr3 = abs(data['Low'] - prev_close)
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Calculate ATR
            atr = true_range.rolling(window=period).mean()
            
            return atr
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return pd.Series()
    
    @staticmethod
    def calculate_support_resistance(data: pd.DataFrame, window: int = 20, min_touches: int = 2) -> dict:
        """
        Calculate support and resistance levels
        
        Args:
            data (pd.DataFrame): Stock data with OHLC columns
            window (int): Window for local extrema detection
            min_touches (int): Minimum touches for level confirmation
            
        Returns:
            dict: Support and resistance levels
        """
        try:
            if len(data) < window * 2:
                return {'support_levels': [], 'resistance_levels': []}
            
            # Find local minima (support) and maxima (resistance)
            highs = data['High']
            lows = data['Low']
            
            # Local maxima (resistance levels)
            resistance_candidates = []
            for i in range(window, len(highs) - window):
                if highs.iloc[i] == highs.iloc[i-window:i+window+1].max():
                    resistance_candidates.append((i, highs.iloc[i]))
            
            # Local minima (support levels)
            support_candidates = []
            for i in range(window, len(lows) - window):
                if lows.iloc[i] == lows.iloc[i-window:i+window+1].min():
                    support_candidates.append((i, lows.iloc[i]))
            
            # Group similar levels and count touches
            tolerance = 0.02  # 2% tolerance
            
            def group_levels(candidates):
                if not candidates:
                    return []
                
                levels = []
                for idx, price in candidates:
                    # Find if this price is close to existing level
                    found_group = False
                    for level in levels:
                        if abs(price - level['price']) / level['price'] <= tolerance:
                            level['touches'] += 1
                            level['indices'].append(idx)
                            level['price'] = (level['price'] * (level['touches'] - 1) + price) / level['touches']
                            found_group = True
                            break
                    
                    if not found_group:
                        levels.append({
                            'price': price,
                            'touches': 1,
                            'indices': [idx]
                        })
                
                # Filter by minimum touches
                return [level for level in levels if level['touches'] >= min_touches]
            
            support_levels = group_levels(support_candidates)
            resistance_levels = group_levels(resistance_candidates)
            
            return {
                'support_levels': [level['price'] for level in support_levels],
                'resistance_levels': [level['price'] for level in resistance_levels]
            }
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {'support_levels': [], 'resistance_levels': []}
    
    @staticmethod
    def detect_range_breakout(data: pd.DataFrame, atr_length: int = 500, range_threshold: float = 0.1) -> dict:
        """
        Detect range breakout patterns
        
        Args:
            data (pd.DataFrame): Stock data with OHLC columns
            atr_length (int): ATR calculation period
            range_threshold (float): Range threshold multiplier
            
        Returns:
            dict: Breakout detection results
        """
        try:
            if len(data) < atr_length:
                return {'is_breakout': False, 'direction': None, 'strength': 0}
            
            # Calculate ATR
            atr = TechnicalIndicators.calculate_atr(data, atr_length)
            current_atr = atr.iloc[-1]
            
            # Define range (last 20 periods)
            recent_data = data.tail(20)
            range_high = recent_data['High'].max()
            range_low = recent_data['Low'].min()
            range_size = range_high - range_low
            
            current_close = data['Close'].iloc[-1]
            
            # Check for breakout
            breakout_threshold = current_atr * range_threshold
            
            if current_close > range_high + breakout_threshold:
                return {
                    'is_breakout': True,
                    'direction': 'bullish',
                    'strength': (current_close - range_high) / current_atr,
                    'range_high': range_high,
                    'range_low': range_low
                }
            elif current_close < range_low - breakout_threshold:
                return {
                    'is_breakout': True,
                    'direction': 'bearish',
                    'strength': (range_low - current_close) / current_atr,
                    'range_high': range_high,
                    'range_low': range_low
                }
            else:
                return {
                    'is_breakout': False,
                    'direction': None,
                    'strength': 0,
                    'range_high': range_high,
                    'range_low': range_low
                }
                
        except Exception as e:
            logger.error(f"Error detecting range breakout: {e}")
            return {'is_breakout': False, 'direction': None, 'strength': 0}
