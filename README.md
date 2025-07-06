# NSE Stock Screener Pro - Enhanced

A comprehensive real-time NSE (National Stock Exchange) stock screener application with continuous 15-minute background scanning that operates even when browser tabs are minimized.

## 🚀 Features

### Core Functionality
- **Continuous Auto-Scanning**: Automated 15-minute interval scanning that works independently of browser state
- **Multiple Technical Scanners**: MACD (15min, 4h, 1d), Range Breakout, Resistance Breakout, Support Level analysis
- **Real-time Market Data**: Live NSE indices display (NIFTY, BANKNIFTY, SENSEX, sector indices)
- **Browser-Independent Operation**: Continues scanning even when browser tab is minimized or inactive

### Enhanced Features
- **Smart Auto-Refresh**: JavaScript countdown timer with forced browser refresh every 15 minutes
- **Telegram Notifications**: Real-time bullish signal alerts sent to Telegram with TradingView chart links
- **System Health Monitoring**: Real-time status dashboard with scan counts and error tracking
- **Advanced Filtering**: Sort and filter scan results by multiple criteria
- **Data Export**: Download filtered results as CSV files
- **Error Recovery**: Robust error handling with automatic retry mechanisms

### Technical Analysis
- **MACD Analysis**: Multi-timeframe momentum detection (15-minute, 4-hour, daily)
- **Breakout Detection**: Range and resistance breakout patterns with volume confirmation
- **Support/Resistance**: Multi-level support and resistance zone identification
- **Risk Assessment**: Automated risk-reward ratio calculations

## 🛠️ Installation

### Requirements
- Python 3.11+
- Internet connection for real-time market data

### Quick Setup

1. **Clone or Download**:
   ```bash
   # Extract the zip file or clone the repository
   cd nse-stock-screener-enhanced
   ```

2. **Install Dependencies**:
   ```bash
   pip install streamlit pandas numpy plotly yfinance pytz
   ```

3. **Run the Application**:
   ```bash
   streamlit run app.py --server.port 5000
   ```

4. **Access the App**:
   - Open your browser to `http://localhost:5000`
   - The application will start with auto-scanning enabled

### Advanced Installation (UV Package Manager)
```bash
uv sync
uv run streamlit run app.py --server.port 5000
```

## 📱 Telegram Setup (Optional)

To enable Telegram notifications for bullish signals:

1. **Create a Telegram Bot**:
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Save the Bot Token

2. **Get Chat ID**:
   - Start a chat with your bot
   - Send any message
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat.id` in the response

3. **Configure Secrets**:
   - In Streamlit Cloud: Go to App Settings → Secrets
   - Add the following:
   ```toml
   BOT_TOKEN = "your_bot_token_here"
   CHAT_ID = "your_chat_id_here"
   ```

4. **Enable Notifications**:
   - Use the checkbox in the app sidebar to enable/disable notifications
   - Only bullish signals will be sent to avoid spam

## 📊 Usage

### Getting Started
1. **Launch the Application**: Start the app and it will immediately begin scanning
2. **Configure Scanners**: Use the sidebar to enable/disable specific technical scanners
3. **Monitor Results**: View real-time scan results organized by scanner type
4. **Auto-Refresh**: The app automatically refreshes every 15 minutes to maintain continuous operation

### Scanner Configuration
- **MACD Scanners**: Enable 15-minute, 4-hour, or daily timeframe analysis
- **Advanced Scanners**: Configure range breakout, resistance breakout, and support level detection
- **Manual Scanning**: Use the "Run Manual Scan" button for immediate results

### Data Export
- Filter results by any column
- Sort in ascending or descending order
- Limit the number of displayed results
- Export filtered data as CSV files

## 🏗️ Architecture

### Frontend
- **Streamlit Framework**: Modern web interface with responsive design
- **Plotly Visualizations**: Interactive charts and real-time data displays
- **Auto-Refresh System**: Multiple layers of browser refresh mechanisms

### Backend
- **Modular Scanner System**: Independent technical analysis modules
- **Data Pipeline**: Yahoo Finance API integration with rate limiting
- **Error Handling**: Comprehensive error recovery and logging

### Key Components
```
app.py                    # Main application with auto-scanning logic
scanners/                 # Technical analysis scanner modules
├── macd_scanner.py      # Multi-timeframe MACD analysis
├── range_breakout_scanner.py    # Range breakout detection
├── resistance_breakout_scanner.py  # Resistance breakout patterns
└── support_level_scanner.py    # Support/resistance analysis
utils/                   # Utility modules
├── data_fetcher.py      # Market data retrieval with caching
├── market_indices.py    # Real-time indices data
└── technical_indicators.py  # Technical analysis calculations
```

## 🌐 Deployment

### Streamlit Cloud
1. Upload the code to a GitHub repository
2. Connect to Streamlit Cloud
3. Deploy with automatic dependency detection
4. The app will be available at `your-app.streamlit.app`

### Local Deployment
```bash
# Production settings
streamlit run app.py --server.port 5000 --server.headless true
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["streamlit", "run", "app.py", "--server.port", "5000", "--server.headless", "true"]
```

## 🔧 Configuration

### Auto-Scan Settings
- **Interval**: Fixed 15-minute scanning intervals
- **Browser Independence**: Works even when browser is minimized
- **Error Recovery**: Automatic retry with exponential backoff

### Scanner Configuration
- Enable/disable individual scanners through the sidebar
- Configure timeframes for MACD analysis
- Adjust risk-reward parameters for breakout detection

### Market Data
- **Data Source**: Yahoo Finance API
- **Caching**: 5-minute cache duration for performance
- **Rate Limiting**: Built-in delays to prevent API throttling

## 📈 Scanner Details

### MACD Scanner
- **15-minute**: Short-term momentum signals
- **4-hour**: Medium-term trend analysis
- **Daily**: Long-term trend confirmation
- **Signals**: Bullish/bearish crossovers with strength indicators

### Range Breakout Scanner
- **Pine Script Logic**: Professional-grade breakout detection
- **Volume Confirmation**: Validates breakouts with volume analysis
- **ATR-based Thresholds**: Dynamic breakout level calculation

### Resistance Breakout Scanner
- **Multi-level Analysis**: Identifies multiple resistance zones
- **Retracement Detection**: Finds optimal entry points after breakouts
- **Risk-Reward Calculation**: Automated position sizing suggestions

### Support Level Scanner
- **Dynamic Levels**: Real-time support and resistance identification
- **Touch Analysis**: Counts and validates level strength
- **Entry Signals**: Identifies optimal entry points near support levels

## 🚨 Important Notes

### Market Hours
- **NSE Hours**: 9:15 AM - 3:30 PM IST (Monday-Friday)
- **After Hours**: App continues scanning but with limited data updates
- **Weekend Operation**: Displays last available data

### Data Limitations
- **Yahoo Finance**: Free tier has rate limiting
- **Delayed Data**: Some data may have 15-20 minute delays
- **Accuracy**: All signals are for educational purposes only

### Performance Optimization
- **Memory Management**: Automatic cleanup of old scan results
- **Resource Usage**: Optimized for Streamlit Cloud deployment
- **Error Handling**: Graceful degradation when services are unavailable

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a virtual environment
3. Install development dependencies
4. Run tests before submitting PRs

### Code Style
- Follow PEP 8 standards
- Add type hints for new functions
- Include comprehensive docstrings
- Write unit tests for new features

## 📄 License

This project is open source and available under the MIT License.

## ⚠️ Disclaimer

This application is for educational and research purposes only. Trading decisions should not be based solely on these signals. Always conduct your own research and consider consulting with financial advisors before making investment decisions.

## 🆘 Support

For issues, feature requests, or questions:
1. Check the existing issues in the repository
2. Create a new issue with detailed description
3. Include error logs and reproduction steps

---

**Last Updated**: July 2025  
**Version**: 1.0.0 Enhanced  
**Compatible with**: Python 3.11+, Streamlit 1.28+