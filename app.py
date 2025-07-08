import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import threading
import queue
import os
import pytz
import logging
import json
import requests
import streamlit.components.v1 as components 

# Import custom modules
from scanners.macd_scanner import MACDScanner
from scanners.macd_scanner_original import MACDScannerOriginal
from scanners.range_breakout_scanner import RangeBreakoutScanner
from scanners.resistance_breakout_scanner import ResistanceBreakoutScanner
from scanners.support_level_scanner import SupportLevelScanner
from utils.market_indices import MarketIndices
from utils.data_fetcher import DataFetcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="🚀 NSE Stock Screener Pro - Enhanced",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    """Get current time in IST"""
    return datetime.now(IST)

def check_market_hours_ist():
    """Check if NSE market is open in IST"""
    now = get_ist_time()
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    is_weekday = now.weekday() < 5  # Monday = 0, Friday = 4
    return is_weekday and market_open <= now <= market_close

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'last_scan_time': None,
        'last_telegram_time': None,
        'scan_results': {},
        'auto_scan_enabled': True,
        'scan_interval': 15,  # Fixed 15-minute intervals
        'scan_count': 0,
        'last_heartbeat': get_ist_time(),
        'scan_errors': [],
        'next_scan_time': None,
        'auto_refresh_active': True,
        'notification_enabled': True,
        'active_scanners': {
            "MACD 15min": True,
            "MACD 4h": True,
            "MACD 1d": True,
            "Range Breakout 4h": True,
            "Resistance Breakout 4h": True,
            "Support Level 4h": True
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def should_run_auto_scan():
    """Check if auto scan should run based on timing"""
    if not st.session_state.auto_scan_enabled:
        return False
    
    current_time = get_ist_time()
    
    # Run scan immediately if no previous scan
    if st.session_state.last_scan_time is None:
        return True
    
    # Check if 15 minutes have passed since last scan
    time_since_scan = current_time - st.session_state.last_scan_time
    return time_since_scan >= timedelta(minutes=15)

def execute_scan_cycle():
    """Execute a complete scan cycle"""
    try:
        current_time = get_ist_time()
        logger.info(f"Starting scan cycle #{st.session_state.scan_count + 1}")
        
        # Get active scanners
        active_scanner_names = [name for name, active in st.session_state.active_scanners.items() if active]
        
        if not active_scanner_names:
            st.warning("No scanners selected. Please enable at least one scanner.")
            return
        
        results = {}
        
        for scanner_name in active_scanner_names:
            try:
                # Execute specific scanner
                if "MACD" in scanner_name:
                    timeframe = scanner_name.split()[-1]  # Get timeframe (15min, 4h, 1d)
                    if timeframe == "15min":
                        scanner = MACDScanner(timeframe="15m")
                    elif timeframe == "4h":
                        scanner = MACDScanner(timeframe="4h")
                    else:
                        scanner = MACDScannerOriginal()
                    results[scanner_name] = scanner.scan()
                    
                elif "Range Breakout" in scanner_name:
                    scanner = RangeBreakoutScanner()
                    results[scanner_name] = scanner.scan()
                    
                elif "Resistance Breakout" in scanner_name:
                    scanner = ResistanceBreakoutScanner()
                    results[scanner_name] = scanner.scan()
                    
                elif "Support Level" in scanner_name:
                    scanner = SupportLevelScanner()
                    results[scanner_name] = scanner.scan()
                    
            except Exception as e:
                logger.error(f"Error in {scanner_name}: {e}")
                results[scanner_name] = pd.DataFrame()  # Empty results
                
                # Log error
                error_entry = {
                    'time': get_ist_time().strftime('%H:%M:%S'),
                    'message': f"{scanner_name}: {str(e)[:100]}"
                }
                st.session_state.scan_errors.append(error_entry)
                
                # Keep only last 10 errors
                if len(st.session_state.scan_errors) > 10:
                    st.session_state.scan_errors = st.session_state.scan_errors[-10:]
        
        # Update session state
        st.session_state.scan_results = results
        st.session_state.last_scan_time = current_time
        st.session_state.scan_count += 1
        st.session_state.last_heartbeat = current_time
        st.session_state.next_scan_time = current_time + timedelta(minutes=15)
        
        # Success message
        total_signals = sum(len(df) if isinstance(df, pd.DataFrame) else 0 for df in results.values())
        logger.info(f"Scan completed! Found {total_signals} total signals across {len(active_scanner_names)} scanners.")
        
        # Send Telegram notification if enabled and there are bullish signals
        if (st.session_state.notification_enabled and total_signals > 0):
            try:
                send_telegram_notification(results)
            except Exception as e:
                logger.error(f"Telegram notification failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Scan cycle error: {e}")
        return False, {}
    return True, results

def show_auto_refresh_countdown():
    """Display auto-refresh countdown timer with browser-level refresh"""
    if st.session_state.auto_scan_enabled:
        # Calculate next scan time
        if st.session_state.next_scan_time:
            next_scan = st.session_state.next_scan_time
        else:
            next_scan = get_ist_time() + timedelta(minutes=15)
        
        # JavaScript countdown with forced page reload
        components.html(f"""
        <div style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); 
                    padding: 15px; border-radius: 10px; margin: 10px 0; text-align: center;">
            <h4 style="color: white; margin: 0;">🔄 Next Auto-Scan & Refresh</h4>
            <h2 style="color: #FFD700; margin: 5px 0;" id="countdown">15:00</h2>
            <p style="color: #E8F4FD; margin: 0; font-size: 0.9rem;">
                Browser will auto-refresh every 15 minutes
            </p>
            <p style="color: #B8D4EA; margin: 5px 0 0 0; font-size: 0.8rem;">
                Works even when minimized or tab is inactive
            </p>
        </div>
        
        <script>
        // Target time for next scan
        const targetTime = new Date("{next_scan.strftime('%Y-%m-%d %H:%M:%S')}");
        
        function updateCountdown() {{
            const now = new Date();
            const timeDiff = targetTime.getTime() - now.getTime();
            
            if (timeDiff > 0) {{
                const totalSeconds = Math.floor(timeDiff / 1000);
                const minutes = Math.floor(totalSeconds / 60);
                const seconds = totalSeconds % 60;
                
                document.getElementById('countdown').innerHTML = 
                    (minutes < 10 ? "0" + minutes : minutes) + ":" + 
                    (seconds < 10 ? "0" + seconds : seconds);
                
                setTimeout(updateCountdown, 1000);
            }} else {{
                document.getElementById('countdown').innerHTML = "Refreshing...";
                // Force page reload
                setTimeout(() => window.location.reload(), 2000);
            }}
        }}
        
        // Start countdown
        updateCountdown();
        
        // Backup: Force reload every 15 minutes regardless
        setTimeout(() => {{
            window.location.reload();
        }}, 900000); // 15 minutes = 900,000 milliseconds
        
        // Additional backup: reload every 16 minutes to ensure it happens
        setTimeout(() => {{
            window.location.reload();
        }}, 960000); // 16 minutes
        </script>
        """, height=120)
        
        # Meta refresh as additional backup
        st.markdown("""
        <meta http-equiv="refresh" content="900">
        """, unsafe_allow_html=True)

def display_system_status():
    """Display enhanced system status with health monitoring"""
    st.markdown("### 🖥️ System Health Monitor")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Auto-scan status
        if st.session_state.auto_scan_enabled:
            status = "🟢 ACTIVE"
        else:
            status = "🔴 INACTIVE"
        st.metric("Auto-Scan Status", status)
    
    with col2:
        # Time since last scan
        if st.session_state.last_scan_time:
            time_since = get_ist_time() - st.session_state.last_scan_time
            minutes_ago = int(time_since.total_seconds() / 60)
            st.metric("Last Scan", f"{minutes_ago}min ago")
        else:
            st.metric("Last Scan", "Never")
    
    with col3:
        # Total scans completed
        st.metric("Scans Completed", st.session_state.scan_count)
    
    # Next scan time
    if st.session_state.next_scan_time and st.session_state.auto_scan_enabled:
        time_to_next = st.session_state.next_scan_time - get_ist_time()
        if time_to_next.total_seconds() > 0:
            minutes_left = int(time_to_next.total_seconds() / 60)
            seconds_left = int(time_to_next.total_seconds() % 60)
            st.info(f"⏰ Next scan in: {minutes_left}m {seconds_left}s")
        else:
            st.info("⏰ Next scan: Due now")
    
    # Error log
    if st.session_state.scan_errors:
        with st.expander("⚠️ Recent Errors", expanded=False):
            for error in st.session_state.scan_errors[-3:]:  # Show last 3 errors
                st.error(f"{error['time']}: {error['message']}")

def run_manual_scan():
    """Execute manual scan with progress indication"""
    with st.spinner("🔍 Running manual scan..."):
        success = execute_scan_cycle()
        if success:
            st.success("✅ Manual scan completed successfully!")
            st.rerun()
        else:
            st.error("❌ Manual scan failed. Check error logs.")

def display_scanner_results():
    """Enhanced scanner results display with filtering and export"""
    st.markdown("### 🎯 Live Scanner Results")

    if not st.session_state.scan_results:
        st.info("🔍 No scan data available. Run a manual scan or wait for auto-scan to complete.")
        return

    # Filter scanners with data
    scanners_with_data = {
        name: results for name, results in st.session_state.scan_results.items()
        if isinstance(results, pd.DataFrame) and not results.empty
    }

    if not scanners_with_data:
        st.info("📊 No signals found in recent scans. Market conditions may not meet current criteria.")
        return

    # Create tabs for each scanner
    tab_names = list(scanners_with_data.keys())
    tabs = st.tabs(tab_names)

    for i, (scanner_name, results) in enumerate(scanners_with_data.items()):
        with tabs[i]:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

            with col1:
                st.write(f"**{scanner_name} Results**")

            with col2:
                sort_by = st.selectbox(
                    "Sort by",
                    options=results.columns.tolist(),
                    key=f"sort_{scanner_name}",
                    index=0
                )

            with col3:
                ascending = st.selectbox(
                    "Order",
                    options=["Descending", "Ascending"],
                    key=f"order_{scanner_name}"
                ) == "Ascending"

            with col4:
                max_results = st.number_input(
                    "Show",
                    min_value=5,
                    max_value=100,
                    value=20,
                    step=5,
                    key=f"max_{scanner_name}"
                )

            try:
                # Apply priority sorting for selected scanners
                priority_scanners = ["MACD 15min", "MACD 4h", "MACD 1d", "Range Breakout 4h"]
                signal_priority = ["Bullish Crossover", "Bullish Divergence","Bullish MACD Crossover","Bullish Momentum Building"]
                breakout_priority = ["Bullish Breakout", "Range Breakout", "Resistance Breakout", "Support Breakout","Bullish Range Breakout"]

                if scanner_name in priority_scanners:
                    # Detect the signal column dynamically
                    signal_col = next(
                        (col for col in results.columns if col.strip().lower() in ["signal_type", "signal"]),
                        None
                    )

                    if signal_col:
                        results["Signal_Priority"] = results[signal_col].apply(
                            lambda x: signal_priority.index(str(x).strip())
                            if str(x).strip() in signal_priority else len(signal_priority)
                        )
                    else:
                        results["Signal_Priority"] = len(signal_priority)

                    if "Breakout_Type" in results.columns:
                        results["Breakout_Priority"] = results["Breakout_Type"].apply(
                            lambda x: breakout_priority.index(str(x).strip())
                            if str(x).strip() in breakout_priority else len(breakout_priority)
                        )
                    else:
                        results["Breakout_Priority"] = len(breakout_priority)

                    # Sort with priority
                    results = results.sort_values(
                        by=["Signal_Priority", "Breakout_Priority", sort_by],
                        ascending=[True, True, ascending]
                    )
                    results.drop(columns=["Signal_Priority", "Breakout_Priority"], inplace=True, errors='ignore')
                else:
                    results = results.sort_values(by=sort_by, ascending=ascending)

                sorted_results = results.head(max_results)

                st.dataframe(sorted_results, use_container_width=True, hide_index=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Signals", len(results))
                with col2:
                    st.metric("Displayed", len(sorted_results))

            except Exception as e:
                st.error(f"Error displaying {scanner_name} results: {e}")


def display_market_indices():
    """Display live market indices"""
    st.markdown("### 📊 Live Market Indices")
    
    try:
        market_indices = MarketIndices()
        indices_data = market_indices.get_live_indices()
        
        if not indices_data.empty:
            # Create responsive columns
            cols = st.columns(min(len(indices_data), 4))
            
            for i, (index, row) in enumerate(indices_data.iterrows()):
                with cols[i % 4]:
                    name = str(row['Name'])
                    price = float(row['Price'])
                    change = float(row['Change'])
                    change_pct = float(row['Change%'])
                    
                    st.metric(
                        label=name,
                        value=f"₹{price:,.2f}",
                        delta=f"{change:+.2f} ({change_pct:+.2f}%)"
                    )
        else:
            st.warning("📊 Market indices temporarily unavailable")
            
    except Exception as e:
        st.error(f"⚠️ Error fetching market indices: {str(e)}")

def send_telegram_notification(scan_results):
    """Send filtered scanner results to Telegram"""
    try:
        if "BOT_TOKEN" not in st.secrets or "CHAT_ID" not in st.secrets:
            logger.warning("Telegram credentials not configured in secrets")
            return False

        BOT_TOKEN = st.secrets["BOT_TOKEN"]
        CHAT_ID = st.secrets["CHAT_ID"]

        if not BOT_TOKEN or not CHAT_ID:
            logger.warning("Telegram credentials not configured")
            return False

        now = get_ist_time().strftime('%d %b %Y, %I:%M %p IST')
        message = f"📊 *Market Scanner Report*\n🕒 *Scanned at:* {now}\n"

        def format_section(title, df):
            symbol_col = next((col for col in df.columns if col.lower() == "symbol"), None)
            if not symbol_col:
                return "", []
            df = df[df[symbol_col].notna()]
            df = df[df[symbol_col].astype(str).str.strip() != ""]
            if df.empty:
                return "", []

            lines = [f"\n*{title}:*"]
            buttons = []
            for _, row in df.iterrows():
                symbol = str(row[symbol_col]).strip().replace(".NS", "")
                if symbol:
                    lines.append(f"• {symbol} [🔗 Chart](https://www.tradingview.com/chart/?symbol=NSE:{symbol})")
                    buttons.append({
                        "text": f"{symbol}",
                        "url": f"https://www.tradingview.com/chart/?symbol=NSE:{symbol}"
                    })
            return "\n".join(lines), buttons

        sections = []
        all_buttons = []

        for scanner_name, df in scan_results.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue

            label = scanner_name
            filtered_df = df.copy()

            # 🟢 MACD 4H: Only Bullish Crossover
            if scanner_name == "MACD 4h":
                signal_col = next((col for col in df.columns if col.lower() in ["signal_type", "signal"]), None)
                if signal_col:
                    filtered_df = df[df[signal_col].astype(str).str.strip() == "Bullish Crossover"]
                label = "MACD 4H Bullish Crossover"

            # 🟢 MACD 1D: Only Bullish MACD Crossover
            elif scanner_name == "MACD 1d":
                signal_col = next((col for col in df.columns if col.lower() in ["signal_type", "signal"]), None)
                if signal_col:
                    filtered_df = df[df[signal_col].astype(str).str.strip() == "Bullish MACD Crossover"]
                label = "MACD 1D Bullish Crossover"

            # 🟢 Range Breakout 4h: All
            elif scanner_name == "Range Breakout 4h":
                label = "Range Breakout 4H"

            # 🟢 Resistance Breakout 4h: All
            elif scanner_name == "Resistance Breakout 4h":
                label = "Resistance Breakout 4H"

            # 🟢 Support Level 4h: All
            elif scanner_name == "Support Level 4h":
                label = "Support Level 4H"

            # ❌ Skip all others (like MACD 15min)
            else:
                continue

            if filtered_df.empty:
                continue

            sec, btns = format_section(label, filtered_df)
            if sec:
                sections.append(sec)
                all_buttons.extend(btns)

        if sections:
            message += "\n".join(sections)
        else:
            message += "\n_No matching signals found._"

        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }

        if all_buttons:
            inline_keyboard = []
            for i in range(0, len(all_buttons), 2):
                inline_keyboard.append(all_buttons[i:i+2])
            payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            logger.info("Telegram notification sent successfully")
            return True
        else:
            logger.error(f"Telegram API error: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False


def export_all_results():
    """Export all scan results to CSV"""
    if not st.session_state.scan_results:
        st.warning("No scan data to export")
        return
    
    try:
        timestamp = get_ist_time().strftime('%Y%m%d_%H%M%S')
        
        # Combine all results
        all_results = []
        for scanner_name, results in st.session_state.scan_results.items():
            if isinstance(results, pd.DataFrame) and not results.empty:
                results_copy = results.copy()
                results_copy['Scanner'] = scanner_name
                results_copy['Scan_Time'] = st.session_state.last_scan_time
                all_results.append(results_copy)
        
        if all_results:
            combined_df = pd.concat(all_results, ignore_index=True)
            csv = combined_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download All Results (CSV)",
                data=csv,
                file_name=f"nse_scanner_results_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("No data available for export")
            
    except Exception as e:
        st.error(f"Export failed: {e}")

def main():
    """Main application function with enhanced auto-scanning"""
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0; font-size: 2.5rem;">
            🚀 NSE Stock Screener Pro - Enhanced
        </h1>
        <p style="color: #E8F4FD; text-align: center; margin: 0.5rem 0 0 0; font-size: 1.2rem;">
            Continuous 15-Minute Auto-Scanning | Browser-Independent Operation
        </p>
        <p style="color: #B8D4EA; text-align: center; margin: 0.5rem 0 0 0;">
            IST: {current_time} | Market Status: {market_status}
        </p>
    </div>
    """.format(
        current_time=get_ist_time().strftime('%Y-%m-%d %H:%M:%S'),
        market_status="🟢 OPEN" if check_market_hours_ist() else "🔴 CLOSED"
    ), unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("### ⚙️ Scanner Configuration")
        
        # Auto-scan settings
        st.markdown("#### 🔄 Auto-Scan Settings")
        
        auto_scan = st.checkbox(
            "Enable Auto-Scan (15min intervals)", 
            value=st.session_state.auto_scan_enabled,
            help="Continuously scans every 15 minutes, even when browser is minimized"
        )
        
        if auto_scan != st.session_state.auto_scan_enabled:
            st.session_state.auto_scan_enabled = auto_scan
            if auto_scan:
                st.success("🟢 Auto-scan enabled! Page will refresh every 15 minutes.")
            else:
                st.info("⏸️ Auto-scan disabled.")
        
        # Manual scan button
        if st.button("🔍 Run Manual Scan", type="primary", use_container_width=True):
            run_manual_scan()
        
        # Scanner selection
        st.markdown("#### 📊 Active Scanners")
        
        # MACD Scanners
        st.markdown("**MACD Scanners:**")
        st.session_state.active_scanners["MACD 15min"] = st.checkbox("MACD 15-minute", value=st.session_state.active_scanners["MACD 15min"])
        st.session_state.active_scanners["MACD 4h"] = st.checkbox("MACD 4-hour", value=st.session_state.active_scanners["MACD 4h"])
        st.session_state.active_scanners["MACD 1d"] = st.checkbox("MACD 1-day", value=st.session_state.active_scanners["MACD 1d"])
        
        # Advanced scanners
        st.markdown("**Advanced Scanners:**")
        st.session_state.active_scanners["Range Breakout 4h"] = st.checkbox("Range Breakout (4h)", value=st.session_state.active_scanners["Range Breakout 4h"])
        st.session_state.active_scanners["Resistance Breakout 4h"] = st.checkbox("Resistance Breakout (4h)", value=st.session_state.active_scanners["Resistance Breakout 4h"])
        st.session_state.active_scanners["Support Level 4h"] = st.checkbox("Support Level (4h)", value=st.session_state.active_scanners["Support Level 4h"])
        
        # Telegram notifications
        st.markdown("#### 📱 Telegram Notifications")
        st.session_state.notification_enabled = st.checkbox(
            "Enable Telegram Notifications", 
            value=st.session_state.notification_enabled,
            help="Send bullish signals to Telegram (requires BOT_TOKEN and CHAT_ID in secrets)"
        )
        
        # Export options
        st.markdown("#### 📊 Export Options")
        if st.button("📥 Export Results", use_container_width=True):
            export_all_results()
    
    # Auto-scan logic
    if should_run_auto_scan():
        with st.spinner("🔄 Running automated scan..."):
            execute_scan_cycle()
        st.rerun()

    if should_run_auto_scan():
        with st.spinner("🔄 Running automated scan..."):
            success, results = execute_scan_cycle()
        
            if success:
                now = get_ist_time()
                if (
                    st.session_state.notification_enabled and
                    (st.session_state.last_telegram_time is None or 
                     now - st.session_state.last_telegram_time >= timedelta(minutes=15))
                ):
                    try:
                        sent = send_telegram_notification(results)
                        if sent:
                            st.session_state.last_telegram_time = now
                            logger.info("Telegram message sent after successful auto-scan.")
                    except Exception as e:
                        logger.error(f"Telegram notification failed: {e}")
            else:
                logger.warning("Auto-scan failed. Telegram not sent.")
        
        st.rerun()

    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Market indices display
        display_market_indices()
        
        # Scanner results
        display_scanner_results()
    
    with col2:
        # Auto-refresh countdown
        show_auto_refresh_countdown()
        
        # System status
        display_system_status()

if __name__ == "__main__":
    main()
