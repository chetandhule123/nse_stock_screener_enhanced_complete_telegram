import pandas as pd
import numpy as np
import logging
from datetime import datetime
import pytz
from utils.data_fetcher import DataFetcher
from utils.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

class RangeBreakoutScannerOld:
    """Range Breakout Scanner using Pine Script logic with 4-hour intervals"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.tech_indicators = TechnicalIndicators()
        self.ist = pytz.timezone('Asia/Kolkata')
        logger.info("Range Breakout Scanner (Old) initialized")
        
    def scan(self, timeframe="4h", lookback_days=60):
        """
        Scan for range breakout signals
        
        Args:
            timeframe: Data timeframe (4h recommended)
            lookback_days: Number of days to look back
            
        Returns:
            DataFrame with range breakout signals
        """
        try:
            logger.info("Starting range breakout scan (Old)")
            symbols = self.data_fetcher.get_nse_stock_list()
            results = []
            
            for symbol in symbols[:100]:  # Limit for performance
                try:
                    # Fetch data
                    data = self.data_fetcher.get_stock_data(
                        symbol, 
                        period=f"{lookback_days}d",
                        interval=timeframe
                    )
                    
                    if data is None or len(data) < 100:
                        continue
                    
                    # Detect ranges using Pine Script logic
                    ranges = self.detect_ranges(data)
                    
                    if ranges:
                        # Check for breakouts
                        breakout = self.detect_breakout(data, ranges[-1])
                        
                        if breakout['type'] != 'none':
                            current_price = data['Close'].iloc[-1]
                            volume = data['Volume'].iloc[-1] if 'Volume' in data else 0
                            
                            # Calculate range statistics
                            range_data = ranges[-1]
                            range_width = ((range_data['top'] - range_data['bottom']) / range_data['bottom']) * 100
                            
                            results.append({
                                'Symbol': symbol,
                                'Breakout_Type': breakout['type'],
                                'Current_Price': round(current_price, 2),
                                'Range_Top': round(range_data['top'], 2),
                                'Range_Bottom': round(range_data['bottom'], 2),
                                'Range_Width_%': round(range_width, 2),
                                'Breakout_Strength': breakout['strength'],
                                'Volume': int(volume),
                                'Days_in_Range': range_data['duration'],
                                'Timeframe': timeframe,
                                'Scan_Time': datetime.now(self.ist).strftime('%H:%M:%S')
                            })
                            
                except Exception as e:
                    logger.warning(f"Error processing {symbol}: {e}")
                    continue
            
            if results:
                df = pd.DataFrame(results)
                df = df.sort_values('Breakout_Strength', ascending=False)
                logger.info(f"Range breakout scan (Old) completed: {len(df)} signals found")
                return df
            else:
                logger.info("Range breakout scan (Old) completed: No signals found")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error in Range Breakout scanner (Old): {e}")
            return pd.DataFrame()
    
    def detect_ranges(self, data, length=20, mult=1.0, atr_length=500):
        """
        Detect price ranges using Pine Script logic
        
        Args:
            data: OHLCV DataFrame
            length: Minimum range length
            mult: Range width multiplier
            atr_length: ATR calculation length
            
        Returns:
            List of detected ranges
        """
        try:
            if len(data) < max(length, atr_length):
                return []
            
            # Calculate ATR
            atr = self.tech_indicators.calculate_atr(data, period=min(atr_length, len(data)))
            
            ranges = []
            i = length
            
            while i < len(data) - 1:
                # Calculate moving average for the range
                ma = data['Close'].iloc[i-length:i].mean()
                range_atr = atr.iloc[i] * mult
                
                # Check if price stayed within range
                price_slice = data['Close'].iloc[i-length:i]
                range_top = ma + range_atr
                range_bottom = ma - range_atr
                
                # Count price movements outside the range
                outside_count = 0
                for price in price_slice:
                    if abs(price - ma) > range_atr:
                        outside_count += 1
                
                # If no price movements outside range, we have a valid range
                if outside_count == 0:
                    # Find the end of the range
                    range_end = i
                    while (range_end < len(data) - 1 and 
                           range_bottom <= data['Close'].iloc[range_end] <= range_top):
                        range_end += 1
                    
                    range_data = {
                        'start': i - length,
                        'end': range_end,
                        'top': range_top,
                        'bottom': range_bottom,
                        'middle': ma,
                        'duration': range_end - (i - length),
                        'atr': range_atr
                    }
                    
                    ranges.append(range_data)
                    i = range_end + 1
                else:
                    i += 1
            
            return ranges
            
        except Exception as e:
            logger.error(f"Error in range detection: {e}")
            return []
    
    def detect_breakout(self, data, range_data):
        """
        Detect breakout from range
        
        Args:
            data: OHLCV DataFrame
            range_data: Range information
            
        Returns:
            Dict with breakout type and strength
        """
        try:
            if range_data['end'] >= len(data) - 1:
                return {'type': 'none', 'strength': 0}
            
            current_price = data['Close'].iloc[-1]
            previous_price = data['Close'].iloc[-2]
            
            range_top = range_data['top']
            range_bottom = range_data['bottom']
            range_middle = range_data['middle']
            
            # Upward breakout
            if current_price > range_top and previous_price <= range_top:
                # Calculate breakout strength
                breakout_distance = current_price - range_top
                range_width = range_top - range_bottom
                strength = min((breakout_distance / range_width) * 100, 100)
                
                return {'type': 'Upward Breakout', 'strength': round(strength, 1)}
            
            # Downward breakout
            elif current_price < range_bottom and previous_price >= range_bottom:
                breakout_distance = range_bottom - current_price
                range_width = range_top - range_bottom
                strength = min((breakout_distance / range_width) * 100, 100)
                
                return {'type': 'Downward Breakout', 'strength': round(strength, 1)}
            
            # Range continuation
            elif range_bottom < current_price < range_top:
                # Check proximity to boundaries
                if current_price > range_middle:
                    proximity = ((current_price - range_middle) / (range_top - range_middle)) * 100
                    if proximity > 80:
                        return {'type': 'Near Upper Boundary', 'strength': round(proximity, 1)}
                else:
                    proximity = ((range_middle - current_price) / (range_middle - range_bottom)) * 100
                    if proximity > 80:
                        return {'type': 'Near Lower Boundary', 'strength': round(proximity, 1)}
            
            return {'type': 'none', 'strength': 0}
            
        except Exception as e:
            logger.error(f"Error in breakout detection: {e}")
            return {'type': 'none', 'strength': 0}
