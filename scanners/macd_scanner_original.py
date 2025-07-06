"""
Original MACD Scanner (1-day timeframe)
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import pytz
from utils.data_fetcher import DataFetcher
from utils.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

class MACDScannerOriginal:
    """Original MACD scanner for daily timeframe analysis"""
    
    def __init__(self):
        """Initialize original MACD scanner"""
        self.data_fetcher = DataFetcher()
        self.ist = pytz.timezone('Asia/Kolkata')
        logger.info("Original MACD Scanner initialized")
    
    def scan(self) -> pd.DataFrame:
        """
        Execute MACD scan on daily timeframe
        
        Returns:
            pd.DataFrame: Scan results with MACD signals
        """
        try:
            logger.info("Starting original MACD scan (daily)")
            
            # Fetch daily data for NSE stocks
            stocks_data = self.data_fetcher.get_nse_stocks_data(
                limit=50,
                period="1y",
                interval="1d"
            )
            
            if not stocks_data:
                logger.warning("No stock data available")
                return pd.DataFrame()
            
            results = []
            
            for symbol, data in stocks_data.items():
                try:
                    if len(data) < 50:  # Need sufficient data
                        continue
                    
                    # Calculate MACD
                    macd_data = TechnicalIndicators.calculate_macd(data)
                    
                    if macd_data.empty:
                        continue
                    
                    # Analyze for signals
                    signal_data = self._analyze_macd_pattern(symbol, data, macd_data)
                    
                    if signal_data:
                        results.append(signal_data)
                        
                except Exception as e:
                    logger.warning(f"Error processing {symbol}: {e}")
                    continue
            
            # Convert to DataFrame and sort
            if results:
                df = pd.DataFrame(results)
                df = df.sort_values('Score', ascending=False)
                logger.info(f"Original MACD scan completed: {len(df)} signals found")
                return df
            else:
                logger.info("Original MACD scan completed: No signals found")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Original MACD scan failed: {e}")
            return pd.DataFrame()
    
    def _analyze_macd_pattern(self, symbol: str, price_data: pd.DataFrame, macd_data: pd.DataFrame) -> dict:
        """
        Analyze MACD pattern for trading opportunities
        
        Args:
            symbol (str): Stock symbol
            price_data (pd.DataFrame): Price data
            macd_data (pd.DataFrame): MACD data
            
        Returns:
            dict: Signal data or None
        """
        try:
            if len(macd_data) < 10:
                return None
            
            # Recent MACD values
            recent_macd = macd_data['MACD'].tail(5)
            recent_signal = macd_data['Signal'].tail(5)
            recent_histogram = macd_data['Histogram'].tail(5)
            
            # Current values
            current_macd = recent_macd.iloc[-1]
            current_signal = recent_signal.iloc[-1]
            current_histogram = recent_histogram.iloc[-1]
            
            # Previous values
            prev_macd = recent_macd.iloc[-2]
            prev_signal = recent_signal.iloc[-2]
            prev_histogram = recent_histogram.iloc[-2]
            
            # Price information
            current_price = price_data['Close'].iloc[-1]
            prev_price = price_data['Close'].iloc[-2]
            price_change = ((current_price - prev_price) / prev_price) * 100
            
            # Volume analysis
            current_volume = price_data['Volume'].iloc[-1]
            avg_volume = price_data['Volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume
            
            # Signal detection
            signal_found = False
            signal_type = ""
            score = 0
            
            # Bullish crossover
            if prev_macd <= prev_signal and current_macd > current_signal:
                signal_found = True
                signal_type = "Bullish MACD Crossover"
                score = 85
                
                # Enhance score based on conditions
                if current_macd < 0:  # Crossover below zero line (stronger)
                    score += 10
                if volume_ratio > 1.5:  # High volume confirmation
                    score += 5
                if price_change > 0:  # Price confirmation
                    score += 5
            
            # Bearish crossover
            elif prev_macd >= prev_signal and current_macd < current_signal:
                signal_found = True
                signal_type = "Bearish MACD Crossover"
                score = 85
                
                # Enhance score
                if current_macd > 0:  # Crossover above zero line
                    score += 10
                if volume_ratio > 1.5:
                    score += 5
                if price_change < 0:
                    score += 5
            
            # MACD line crossing zero
            elif len(recent_macd) >= 2:
                if recent_macd.iloc[-2] <= 0 and current_macd > 0:
                    signal_found = True
                    signal_type = "MACD Above Zero"
                    score = 75
                    
                elif recent_macd.iloc[-2] >= 0 and current_macd < 0:
                    signal_found = True
                    signal_type = "MACD Below Zero"
                    score = 75
            
            # Histogram divergence
            if not signal_found:
                histogram_trend = recent_histogram.diff().sum()
                if abs(histogram_trend) > 0.01:  # Significant trend
                    if histogram_trend > 0 and current_histogram > 0:
                        signal_found = True
                        signal_type = "Bullish Momentum Building"
                        score = 65
                    elif histogram_trend < 0 and current_histogram < 0:
                        signal_found = True
                        signal_type = "Bearish Momentum Building"
                        score = 65
            
            # Return signal data
            if signal_found:
                return {
                    'Symbol': symbol.replace('.NS', ''),
                    'Signal': signal_type,
                    'Score': score,
                    'Price': round(current_price, 2),
                    'Change_%': round(price_change, 2),
                    'MACD': round(current_macd, 4),
                    'Signal_Line': round(current_signal, 4),
                    'Histogram': round(current_histogram, 4),
                    'Volume_Ratio': round(volume_ratio, 2),
                    'Scan_Time': datetime.now(self.ist).strftime('%H:%M:%S')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing MACD pattern for {symbol}: {e}")
            return None
