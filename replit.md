# NSE Stock Screener Pro - Enhanced

## Overview

This is a comprehensive real-time NSE (National Stock Exchange) stock screener application built with Streamlit. The application provides automated technical analysis scanning capabilities for Indian stocks with enhanced 15-minute background scanning that operates continuously regardless of browser state. The system features multiple technical analysis scanners, real-time market data integration, and robust background processing with proper error handling and recovery mechanisms.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application framework with wide layout configuration
- **Visualization**: Plotly for interactive charts and real-time data visualization
- **UI Components**: Custom CSS styling with modern gradient themes and responsive design
- **Auto-refresh**: Meta refresh tags combined with Streamlit's native rerun functionality
- **Session Management**: Persistent session state across browser interactions

### Backend Architecture
- **Modular Scanner System**: Independent scanner modules implementing different technical analysis strategies
- **Threading Architecture**: Proper Streamlit context management using `add_script_run_ctx` for background operations
- **Timer-based Scheduling**: Precise 15-minute interval scanning using `threading.Timer`
- **Session Monitoring**: Heartbeat system to detect browser state changes and maintain active sessions
- **Error Recovery**: Robust retry logic and error handling for failed scans

### Data Pipeline
- **Data Source**: Yahoo Finance API integration through yfinance library
- **Rate Limiting**: Built-in delays and caching mechanisms to prevent API throttling
- **Timeframe Support**: Multiple intervals (15m, 1h, 4h, 1d) with automatic aggregation
- **Caching Layer**: 5-minute cache duration for frequently accessed data

## Key Components

### Core Application (`app.py`)
- Main Streamlit application entry point with enhanced background scanning
- Session state management for scan results, configuration, and timing
- Auto-scan functionality with browser-independent operation
- Real-time market indices display with live updates
- Interactive dashboard with filtering, sorting, and export capabilities

### Scanner Framework (`/scanners/`)
- **MACDScanner**: Multi-timeframe MACD crossover and momentum analysis (15m, 4h, 1d)
- **MACDScannerOriginal**: Original daily timeframe MACD implementation
- **RangeBreakoutScanner**: Pine Script-inspired range detection with volume confirmation
- **ResistanceBreakoutScanner**: Breakout and retracement pattern detection with risk-reward analysis
- **SupportLevelScanner**: Multi-level support and resistance zone identification

### Utility Framework (`/utils/`)
- **DataFetcher**: Enhanced Yahoo Finance API wrapper with error handling and caching
- **TechnicalIndicators**: Mathematical calculations for MACD, EMAs, and other indicators
- **MarketIndices**: Real-time NSE indices monitoring (NIFTY, BANKNIFTY, SENSEX, etc.)
- **BackgroundScannerEngine**: Core background scanning engine with proper threading
- **SessionMonitor**: Browser state detection and cleanup mechanisms

### Background Scanning Engine
- **Continuous Operation**: 15-minute intervals operating independently of browser state
- **Thread Management**: Proper Streamlit context management for background threads
- **Heartbeat Monitoring**: Active session detection with cleanup callbacks
- **Error Recovery**: Automatic retry mechanisms and graceful failure handling

## Data Flow

1. **Initialization**: Application starts and initializes session state and scanner configurations
2. **Market Data**: Real-time indices fetched and displayed in sidebar
3. **Background Scanning**: Timer-based scanner engine executes every 15 minutes
4. **Data Processing**: Each scanner processes NSE stock data through technical indicators
5. **Result Storage**: Scan results stored in session state with timestamp tracking
6. **UI Updates**: Results displayed with auto-refresh and manual refresh options
7. **Export**: Filtered results can be downloaded as CSV files

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework for the main interface
- **pandas**: Data manipulation and analysis for stock data processing
- **numpy**: Numerical computations for technical indicators
- **plotly**: Interactive charting and visualization
- **yfinance**: Yahoo Finance API client for market data

### System Libraries
- **threading**: Background processing and timer management
- **datetime/pytz**: Timezone handling (IST) and timestamp management
- **logging**: Application logging and error tracking
- **queue**: Thread-safe communication between background processes

### Market Data
- **Yahoo Finance API**: Primary data source for NSE stock prices and indices
- **NSE Stock Universe**: Curated list of 100+ major NSE stocks
- **Real-time Indices**: NIFTY 50, BANKNIFTY, SENSEX, sector indices

## Deployment Strategy

### Streamlit Cloud Optimization
- **Memory Management**: Efficient session state usage with cleanup mechanisms
- **Resource Optimization**: Rate limiting and caching to minimize API calls
- **Error Handling**: Graceful degradation when external services are unavailable
- **Threading Compatibility**: Proper context management for Streamlit Cloud environment

### Browser Independence Features
- **Meta Refresh**: Browser-level auto-refresh every 15 minutes as backup
- **Session Persistence**: Maintains operation across browser minimization/tab changes
- **Heartbeat System**: Detects and recovers from temporary disconnections
- **Cleanup Mechanisms**: Proper resource cleanup when sessions end

### Performance Considerations
- **Batch Processing**: Efficient stock data fetching with rate limiting
- **Caching Strategy**: 5-minute cache for frequently accessed data
- **Memory Efficiency**: Cleanup of old scan results and session data
- **Error Recovery**: Automatic retry with exponential backoff

## Changelog

```
Changelog:
- July 06, 2025. Initial setup
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```