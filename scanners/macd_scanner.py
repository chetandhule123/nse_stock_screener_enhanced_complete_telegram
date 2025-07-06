"""
Enhanced MACD Scanner with multiple timeframes
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import pytz
from utils.data_fetcher import DataFetcher
from utils.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

class MACDScanner:
    """MACD-based scanner for momentum analysis"""
    
    def __init__(self, timeframe="15m"):
        """
        Initialize MACD scanner
        
        Args:
            timeframe (str): Timeframe for analysis (15m, 4h, 1d)
        """
        self.timeframe = timeframe
        self.data_fetcher = DataFetcher()
        self.ist = pytz.timezone('Asia/Kolkata')
        
        # Timeframe mapping for yfinance
        self.timeframe_mapping = {
            "15m": {"period": "5d", "interval": "15m"},
            "4h": {"period": "60d", "interval": "1h"},  # Use 1h and aggregate to 4h
            "1d": {"period": "1y", "interval": "1d"}
        }
        
        logger.info(f"MACD Scanner initialized for {timeframe}")
    
    def scan(self) -> pd.DataFrame:
        """
        Execute MACD scan across NSE stocks
        
        Returns:
            pd.DataFrame: Scan results with MACD signals
        """
        try:
            logger.info(f"Starting MACD scan for {self.timeframe}")
            
            # Get timeframe parameters
            if self.timeframe not in self.timeframe_mapping:
                logger.error(f"Unsupported timeframe: {self.timeframe}")
                return pd.DataFrame()
            
            params = self.timeframe_mapping[self.timeframe]
            
            # Fetch data for NSE stocks
            stocks_data = self.data_fetcher.get_nse_stocks_data(
                limit=50,  # Limit for performance
                period=params["period"],
                interval=params["interval"]
            )
            
            if not stocks_data:
                logger.warning("No stock data available")
                return pd.DataFrame()
            
            results = []
            
            for symbol, data in stocks_data.items():
                try:
                    # Convert to 4h timeframe if needed
                    if self.timeframe == "4h":
                        data = self._convert_to_4h(data)
                    
                    if len(data) < 50:  # Need sufficient data for MACD
                        continue
                    
                    # Calculate MACD
                    macd_data = TechnicalIndicators.calculate_macd(data)
                    
                    if macd_data.empty:
                        continue
                    
                    # Analyze MACD signals
                    signal_data = self._analyze_macd_signals(symbol, data, macd_data)
                    
                    if signal_data:
                        results.append(signal_data)
                        
                except Exception as e:
                    logger.warning(f"Error processing {symbol}: {e}")
                    continue
            
            # Convert to DataFrame
            if results:
                df = pd.DataFrame(results)
                df = df.sort_values('Signal_Strength', ascending=False)
                logger.info(f"MACD scan completed: {len(df)} signals found")
                return df
            else:
                logger.info("MACD scan completed: No signals found")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"MACD scan failed: {e}")
            return pd.DataFrame()
    
    def _convert_to_4h(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Convert 1h data to 4h timeframe
        
        Args:
            data (pd.DataFrame): 1h OHLCV data
            
        Returns:
            pd.DataFrame: 4h OHLCV data
        """
        try:
            # Resample to 4h intervals
            resampled = data.resample('4H').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
            
            return resampled
            
        except Exception as e:
            logger.error(f"Error converting to 4h timeframe: {e}")
            return data
    
    def _analyze_macd_signals(self, symbol: str, price_data: pd.DataFrame, macd_data: pd.DataFrame) -> dict:
        """
        Analyze MACD for trading signals
        
        Args:
            symbol (str): Stock symbol
            price_data (pd.DataFrame): Price data
            macd_data (pd.DataFrame): MACD data
            
        Returns:
            dict: Signal data or None
        """
        try:
            if len(macd_data) < 3:
                return None
            
            # Get recent MACD values
            current_macd = macd_data['MACD'].iloc[-1]
            current_signal = macd_data['Signal'].iloc[-1]
            current_histogram = macd_data['Histogram'].iloc[-1]
            
            prev_macd = macd_data['MACD'].iloc[-2]
            prev_signal = macd_data['Signal'].iloc[-2]
            prev_histogram = macd_data['Histogram'].iloc[-2]
            
            # Current price info
            current_price = price_data['Close'].iloc[-1]
            prev_price = price_data['Close'].iloc[-2]
            price_change = ((current_price - prev_price) / prev_price) * 100
            
            # Detect signals
            signal_type = None
            signal_strength = 0
            
            # Bullish signals
            if (prev_macd <= prev_signal and current_macd > current_signal):
                signal_type = "Bullish Crossover"
                signal_strength = abs(current_histogram) * 10
                
            elif (current_histogram > 0 and prev_histogram <= 0):
                signal_type = "Bullish Momentum"
                signal_strength = current_histogram * 8
                
            elif (current_macd > current_signal and current_histogram > prev_histogram and current_histogram > 0):
                signal_type = "Bullish Divergence"
                signal_strength = (current_histogram - prev_histogram) * 5
            
            # Bearish signals
            elif (prev_macd >= prev_signal and current_macd < current_signal):
                signal_type = "Bearish Crossover"
                signal_strength = abs(current_histogram) * 10
                
            elif (current_histogram < 0 and prev_histogram >= 0):
                signal_type = "Bearish Momentum"
                signal_strength = abs(current_histogram) * 8
                
            elif (current_macd < current_signal and current_histogram < prev_histogram and current_histogram < 0):
                signal_type = "Bearish Divergence"
                signal_strength = abs(current_histogram - prev_histogram) * 5
            
            # Return signal if found
            if signal_type:
                return {
                    'Symbol': symbol.replace('.NS', ''),
                    'Signal_Type': signal_type,
                    'Signal_Strength': round(signal_strength, 2),
                    'Current_Price': round(current_price, 2),
                    'Price_Change_%': round(price_change, 2),
                    'MACD': round(current_macd, 4),
                    'Signal_Line': round(current_signal, 4),
                    'Histogram': round(current_histogram, 4),
                    'Timeframe': self.timeframe,
                    'Scan_Time': datetime.now(self.ist).strftime('%H:%M:%S')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing MACD signals for {symbol}: {e}")
            return None
