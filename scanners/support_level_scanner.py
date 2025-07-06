"""
Support Level Scanner for identifying support/resistance zones and entry opportunities
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import pytz
from utils.data_fetcher import DataFetcher
from utils.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

class SupportLevelScanner:
    """Scanner for support/resistance analysis and trading opportunities"""
    
    def __init__(self):
        """Initialize support level scanner"""
        self.data_fetcher = DataFetcher()
        self.ist = pytz.timezone('Asia/Kolkata')
        logger.info("Support Level Scanner initialized")
    
    def scan(self) -> pd.DataFrame:
        """
        Execute support level scan
        
        Returns:
            pd.DataFrame: Scan results with support/resistance signals
        """
        try:
            logger.info("Starting support level scan")
            
            # Fetch 4h data for better level detection
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
                    
                    # Analyze support/resistance levels
                    level_data = self._analyze_support_resistance(symbol, data_4h)
                    
                    if level_data:
                        results.append(level_data)
                        
                except Exception as e:
                    logger.warning(f"Error processing {symbol}: {e}")
                    continue
            
            # Convert to DataFrame and sort
            if results:
                df = pd.DataFrame(results)
                df = df.sort_values('Signal_Strength', ascending=False)
                logger.info(f"Support level scan completed: {len(df)} signals found")
                return df
            else:
                logger.info("Support level scan completed: No signals found")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Support level scan failed: {e}")
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
    
    def _analyze_support_resistance(self, symbol: str, data: pd.DataFrame) -> dict:
        """
        Analyze support and resistance levels for trading opportunities
        
        Args:
            symbol (str): Stock symbol
            data (pd.DataFrame): 4h OHLCV data
            
        Returns:
            dict: Signal data or None
        """
        try:
            # Calculate support and resistance levels
            sr_levels = TechnicalIndicators.calculate_support_resistance(
                data, window=15, min_touches=2
            )
            
            support_levels = sr_levels['support_levels']
            resistance_levels = sr_levels['resistance_levels']
            
            if not support_levels and not resistance_levels:
                return None
            
            # Current price data
            current_bar = data.iloc[-1]
            current_close = current_bar['Close']
            current_low = current_bar['Low']
            current_high = current_bar['High']
            current_volume = current_bar['Volume']
            
            # Previous close for price change
            prev_close = data.iloc[-2]['Close']
            price_change = ((current_close - prev_close) / prev_close) * 100
            
            # Volume analysis
            avg_volume = data['Volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume
            
            # Find relevant levels
            signal_type = ""
            signal_strength = 0
            key_level = 0
            distance_to_level = 0
            
            # Check for support opportunities
            if support_levels:
                # Find nearest support below current price
                relevant_supports = [s for s in support_levels if s <= current_close * 1.02]  # Within 2%
                
                if relevant_supports:
                    nearest_support = max(relevant_supports)
                    distance_to_support = abs(current_close - nearest_support)
                    distance_percentage = (distance_to_support / current_close) * 100
                    
                    # Check if price is near support (within 3%)
                    if distance_percentage <= 3:
                        signal_type = "Near Support Level"
                        signal_strength = 80 - (distance_percentage * 10)  # Closer = stronger
                        key_level = nearest_support
                        distance_to_level = distance_percentage
                        
                        # Boost score for volume confirmation
                        if volume_ratio > 1.2:
                            signal_strength += 10
                        
                        # Check for bounce pattern
                        if current_low <= nearest_support <= current_close:
                            signal_type = "Support Bounce"
                            signal_strength += 15
            
            # Check for resistance opportunities
            if resistance_levels and signal_strength < 70:  # Only if no strong support signal
                # Find nearest resistance above current price
                relevant_resistances = [r for r in resistance_levels if r >= current_close * 0.98]  # Within 2%
                
                if relevant_resistances:
                    nearest_resistance = min(relevant_resistances)
                    distance_to_resistance = abs(current_close - nearest_resistance)
                    distance_percentage = (distance_to_resistance / current_close) * 100
                    
                    # Check if price is near resistance (within 3%)
                    if distance_percentage <= 3:
                        signal_type = "Near Resistance Level"
                        signal_strength = 75 - (distance_percentage * 10)  # Closer = stronger
                        key_level = nearest_resistance
                        distance_to_level = distance_percentage
                        
                        # Volume confirmation
                        if volume_ratio > 1.2:
                            signal_strength += 10
                        
                        # Check for rejection pattern
                        if current_high >= nearest_resistance >= current_close:
                            signal_type = "Resistance Rejection"
                            signal_strength += 15
            
            # Enhanced analysis for strong levels
            if signal_strength > 70:
                # Calculate risk-reward ratios
                if "Support" in signal_type:
                    # For support signals
                    stop_loss = key_level * 0.98  # 2% below support
                    risk = current_close - stop_loss
                    
                    # Find target (next resistance or 1:2 risk-reward)
                    if resistance_levels:
                        next_resistance = min([r for r in resistance_levels if r > current_close], default=current_close + (risk * 2))
                        target = min(next_resistance, current_close + (risk * 2))
                    else:
                        target = current_close + (risk * 2)
                    
                else:
                    # For resistance signals
                    stop_loss = key_level * 1.02  # 2% above resistance
                    risk = stop_loss - current_close
                    
                    # Find target (next support or 1:2 risk-reward)
                    if support_levels:
                        next_support = max([s for s in support_levels if s < current_close], default=current_close - (risk * 2))
                        target = max(next_support, current_close - (risk * 2))
                    else:
                        target = current_close - (risk * 2)
                
                # Calculate risk-reward ratio
                reward = abs(target - current_close)
                risk_reward_ratio = reward / risk if risk > 0 else 0
                
                return {
                    'Symbol': symbol.replace('.NS', ''),
                    'Signal_Type': signal_type,
                    'Signal_Strength': round(signal_strength, 2),
                    'Current_Price': round(current_close, 2),
                    'Key_Level': round(key_level, 2),
                    'Distance_to_Level_%': round(distance_to_level, 2),
                    'Price_Change_%': round(price_change, 2),
                    'Volume_Ratio': round(volume_ratio, 2),
                    'Stop_Loss': round(stop_loss, 2),
                    'Target': round(target, 2),
                    'Risk_Amount': round(risk, 2),
                    'Reward_Amount': round(reward, 2),
                    'Risk_Reward_Ratio': f"1:{round(risk_reward_ratio, 2)}",
                    'Total_Support_Levels': len(support_levels),
                    'Total_Resistance_Levels': len(resistance_levels),
                    'Scan_Time': datetime.now(self.ist).strftime('%H:%M:%S')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing support/resistance for {symbol}: {e}")
            return None
