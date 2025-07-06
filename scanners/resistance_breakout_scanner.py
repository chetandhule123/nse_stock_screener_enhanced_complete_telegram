"""
Resistance Breakout Scanner for identifying breakout and retracement opportunities
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import pytz
from utils.data_fetcher import DataFetcher
from utils.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

class ResistanceBreakoutScanner:
    """Scanner for resistance breakout patterns and retracements"""
    
    def __init__(self):
        """Initialize resistance breakout scanner"""
        self.data_fetcher = DataFetcher()
        self.ist = pytz.timezone('Asia/Kolkata')
        logger.info("Resistance Breakout Scanner initialized")
    
    def scan(self) -> pd.DataFrame:
        """
        Execute resistance breakout scan
        
        Returns:
            pd.DataFrame: Scan results with resistance breakout signals
        """
        try:
            logger.info("Starting resistance breakout scan")
            
            # Fetch 4h data
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
                    
                    if len(data_4h) < 100:
                        continue
                    
                    # Analyze for resistance breakout
                    breakout_data = self._analyze_resistance_breakout(symbol, data_4h)
                    
                    if breakout_data:
                        results.append(breakout_data)
                        
                except Exception as e:
                    logger.warning(f"Error processing {symbol}: {e}")
                    continue
            
            # Convert to DataFrame and sort
            if results:
                df = pd.DataFrame(results)
                df = df.sort_values('Breakout_Score', ascending=False)
                logger.info(f"Resistance breakout scan completed: {len(df)} signals found")
                return df
            else:
                logger.info("Resistance breakout scan completed: No signals found")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Resistance breakout scan failed: {e}")
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
    
    def _analyze_resistance_breakout(self, symbol: str, data: pd.DataFrame) -> dict:
        """
        Analyze for resistance breakout patterns
        
        Args:
            symbol (str): Stock symbol
            data (pd.DataFrame): 4h OHLCV data
            
        Returns:
            dict: Breakout signal data or None
        """
        try:
            # Calculate support and resistance levels
            sr_levels = TechnicalIndicators.calculate_support_resistance(
                data, window=10, min_touches=2
            )
            
            resistance_levels = sr_levels['resistance_levels']
            support_levels = sr_levels['support_levels']
            
            if not resistance_levels:
                return None
            
            # Current price data
            current_bar = data.iloc[-1]
            current_close = current_bar['Close']
            current_high = current_bar['High']
            current_volume = current_bar['Volume']
            
            # Previous bars for pattern analysis
            prev_bars = data.tail(5)
            
            # Find relevant resistance level
            relevant_resistance = None
            for resistance in resistance_levels:
                if resistance <= current_close * 1.05:  # Within 5% above current price
                    relevant_resistance = resistance
                    break
            
            if relevant_resistance is None:
                return None
            
            # Check for fresh breakout
            breakout_confirmed = False
            retracement_opportunity = False
            signal_type = ""
            
            # Volume analysis
            avg_volume = data['Volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume
            
            # Price analysis
            price_above_resistance = current_close > relevant_resistance
            high_above_resistance = current_high > relevant_resistance
            
            # Check if this is a fresh breakout (price was below resistance recently)
            recent_closes = prev_bars['Close'].iloc[-5:]
            was_below_resistance = any(close <= relevant_resistance for close in recent_closes)
            
            if price_above_resistance and high_above_resistance and was_below_resistance:
                # Fresh breakout detected
                breakout_confirmed = True
                signal_type = "Fresh Resistance Breakout"
                
                # Check breakout strength
                breakout_distance = current_close - relevant_resistance
                breakout_percentage = (breakout_distance / relevant_resistance) * 100
                
                # Volume confirmation
                volume_confirmed = volume_ratio > 1.2
                
                # Calculate score
                score = 70
                if volume_confirmed:
                    score += 15
                if breakout_percentage > 2:  # Strong breakout
                    score += 10
                if breakout_percentage > 5:  # Very strong breakout
                    score += 5
                
            else:
                # Check for retracement opportunity
                # Price broke resistance recently but now pulling back
                for i in range(2, min(10, len(data))):
                    past_high = data.iloc[-i]['High']
                    past_close = data.iloc[-i]['Close']
                    
                    if (past_high > relevant_resistance and 
                        past_close > relevant_resistance and
                        current_close < relevant_resistance):
                        
                        retracement_opportunity = True
                        signal_type = "Resistance Retracement"
                        
                        # Calculate retracement score
                        distance_from_resistance = abs(current_close - relevant_resistance)
                        retracement_percentage = (distance_from_resistance / relevant_resistance) * 100
                        
                        score = 60
                        if retracement_percentage < 3:  # Close to resistance
                            score += 15
                        if volume_ratio > 1.0:
                            score += 10
                        
                        break
            
            # Return signal if found
            if breakout_confirmed or retracement_opportunity:
                # Calculate risk-reward
                if support_levels:
                    nearest_support = max([s for s in support_levels if s < current_close], default=current_close * 0.95)
                else:
                    nearest_support = current_close * 0.95
                
                stop_loss = nearest_support
                risk = current_close - stop_loss
                target = current_close + (risk * 2)  # 1:2 risk-reward
                
                # Price change
                prev_close = data.iloc[-2]['Close']
                price_change = ((current_close - prev_close) / prev_close) * 100
                
                return {
                    'Symbol': symbol.replace('.NS', ''),
                    'Signal_Type': signal_type,
                    'Breakout_Score': score,
                    'Current_Price': round(current_close, 2),
                    'Resistance_Level': round(relevant_resistance, 2),
                    'Price_Change_%': round(price_change, 2),
                    'Volume_Ratio': round(volume_ratio, 2),
                    'Stop_Loss': round(stop_loss, 2),
                    'Target': round(target, 2),
                    'Risk_Amount': round(risk, 2),
                    'Risk_Reward': '1:2',
                    'Distance_from_Resistance_%': round(abs(current_close - relevant_resistance) / relevant_resistance * 100, 2),
                    'Scan_Time': datetime.now(self.ist).strftime('%H:%M:%S')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing resistance breakout for {symbol}: {e}")
            return None
