# Coinbase Rank Telegram Bot

## Overview

This is a Python-based Telegram bot that monitors cryptocurrency market sentiment indicators and automatically sends notifications to Telegram channels. The bot tracks Coinbase app rankings from user-provided JSON data, cryptocurrency Fear & Greed Index, Google Trends data for crypto-related terms, and Altcoin Season Index to provide comprehensive market sentiment analysis. Runs daily at 8:01 UTC (11:01 MSK).

## System Architecture

### Core Technologies
- **Backend**: Python 3.10+ with Flask web framework
- **Data Storage**: JSON files for data persistence (no database required)
- **Scheduling**: Custom threading-based scheduler with file locking mechanism (10:59 MSK data collection, 11:01 MSK messaging)
- **External APIs**: 
  - Telegram Bot API for messaging
  - Alternative.me API for Fear & Greed Index
  - Google Trends API via pytrends library
  - CoinGecko API for altcoin season calculations
  - SensorTower web scraping for app rankings
- **Web Interface**: Flask-based dashboard for manual controls and monitoring

### Architecture Pattern
The system follows a modular, event-driven architecture with separate components for data collection, processing, and notification delivery. Each module operates independently and communicates through a shared data layer using JSON files.

## Key Components

### 1. Data Collection Modules
- **SensorTowerScraper** (`scraper.py`): Monitors Coinbase app ranking with fallback to rank 300 (source channel deleted)
- **FearGreedIndexTracker** (`fear_greed_index.py`): Fetches cryptocurrency Fear & Greed Index
- **GoogleTrendsPulse** (`google_trends_pulse.py`): Analyzes search trends for crypto-related terms
- **AltcoinSeasonIndex** (`altcoin_season_index.py`): Calculates altcoin season indicators
- **OrderBookImbalance** (`order_book_imbalance.py`): Analyzes market order book data

### 2. Communication Layer
- **TelegramBot** (`telegram_bot.py`): Handles message formatting and delivery to Telegram channels
- **HistoryAPI** (`history_api.py`): Manages data persistence using JSON files

### 3. Orchestration
- **SensorTowerScheduler** (`scheduler.py`): Coordinates data collection and message sending
- **Flask Web Interface** (`main.py`): Provides manual controls and status monitoring

### 4. Configuration Management
- **Config System** (`config.py`): Centralized configuration with environment variable support
- **Environment Loading** (`load_dotenv.py`): Custom .env file loader

## Data Flow

1. **Pre-collection**: The scheduler runs rnk.py at 07:59 UTC (10:59 MSK) to collect fresh SensorTower data
2. **Scheduled Execution**: The scheduler runs daily at 08:01 UTC (11:01 MSK)
3. **Data Collection**: Each module fetches its respective data from external sources
4. **Change Detection**: System compares new data with historical values stored in JSON files
5. **Message Composition**: If changes are detected, a formatted message is created
6. **Notification Delivery**: Message is sent to the configured Telegram channel
7. **Data Persistence**: New data is saved to JSON history files

### Data Storage Structure
- `rank_history.json`: Coinbase app ranking history
- `fear_greed_history.json`: Fear & Greed Index history  
- `trends_history.json`: Google Trends analysis history
- `altseason_history.json`: Altcoin season index history
- `gbi_history.json`: Global order book imbalance history

## External Dependencies

### APIs and Services
- **Telegram Bot API**: For sending messages to channels
- **Alternative.me Fear & Greed API**: Cryptocurrency sentiment data
- **Google Trends**: Search interest analysis via pytrends
- **CoinGecko API**: Cryptocurrency market data for altcoin analysis
- **SensorTower**: Web scraping for app store rankings

### Python Libraries
- `flask`: Web framework for dashboard
- `requests`: HTTP client for API calls
- `pytrends`: Google Trends API wrapper
- `trafilatura`: Web content extraction
- `ccxt`: Cryptocurrency exchange integration
- `telegram`: Telegram Bot API wrapper

## Deployment Strategy

### Production Environment
- **Runtime**: Python 3.10+ virtual environment
- **Process Management**: systemd service (`coinbasebot.service`)
- **Web Server**: Built-in Flask development server (suitable for this use case)
- **File Locking**: Custom file-based locking to prevent multiple instances
- **Logging**: Rotating file logs with configurable retention

### Configuration Management
- Environment variables for sensitive data (bot tokens, channel IDs)
- Fallback to `.env` file for local development
- Centralized configuration in `config.py` with environment overrides

### Monitoring and Maintenance
- Web dashboard for manual operations and status monitoring
- Detailed logging with separate log files for different modules
- Lock file cleanup utilities for maintenance
- Built-in error handling and fallback mechanisms

## Recent Changes

### July 05, 2025
- **Market Breadth Integration**: Fully integrated user's Streamlit code into Flask web interface
- **Plotly Visualization**: Created dual-panel charts with Bitcoin price and market breadth indicator
- **Correlation Analysis**: Added correlation table with Bitcoin for all analyzed cryptocurrencies
- **Real-time Analysis**: System analyzes 47 cryptocurrencies (50 minus 3 stablecoins) with 6-hour data caching
- **Stablecoin Exclusion**: Removed USDT, USDC, DAI from analysis for more accurate market dynamics
- **Interactive Controls**: Configurable parameters for top coins count, MA period, and history days
- **User's Algorithm**: Direct implementation of user's crypto_analyzer_cryptocompare.py and data_cache.py
- **Modern TradingView Style**: Updated chart design with light theme, professional colors, and clean interface
- **Extended Analysis Period**: Default analysis period increased to 3 years (1095 days) for comprehensive market insights
- **Full English Interface**: Complete translation of web interface from Russian to English including all buttons, labels, chart titles, annotations (Overbought/Oversold/Neutral Zone), loading messages, and error alerts
- **Professional Chart Titles**: Updated market breadth chart title to "% Of Cryptocurrencies Above 200-Day Moving Average" matching professional financial terminology
- **Embedded Chart Explanation**: Added informative annotation directly in the chart explaining the indicator purpose and interpretation, displayed in a bordered box within the graph area for immediate user understanding
- **Telegram Chart Integration**: Added market breadth indicator data to daily Telegram messages with automated chart screenshots
- **Visual Market Reports**: System now generates and sends Plotly chart images alongside text data for comprehensive market analysis
- **Chart Screenshot Function**: Created automatic PNG generation from interactive Plotly charts for Telegram delivery
- **Enhanced Message Format**: Telegram messages now include both text indicators and visual chart data for complete market picture
- **3-Year Historical Analysis**: Updated chart screenshot function to display 3 years of market data instead of 1 year for comprehensive historical context
- **Robust Chart Generation**: Implemented dual-engine chart creation with Plotly/Kaleido primary and matplotlib fallback for reliable PNG generation
- **Telegram Chart Testing**: Added "Test Chart to Telegram" functionality working successfully with automatic fallback to matplotlib when system dependencies unavailable
- **Chart Function Synchronization**: Updated Telegram chart generation to use `create_web_ui_chart_screenshot()` ensuring exact match with web interface display
- **Scheduler Chart Integration**: Modified daily scheduler to use web-interface-matching chart function for consistent visual reports across all channels
- **Fast Chart Generation Solution**: Replaced web endpoint chart generation with optimized `create_chart_from_web_endpoint()` function that creates charts using local data processing instead of HTTP requests
- **Telegram Chart Success**: Implemented working chart delivery system using matplotlib with 1-year data fallback (365 days) to ensure reliable chart generation and delivery to Telegram
- **Reliable Chart Pipeline**: Created dual-approach system: uses existing scheduler data when available, otherwise generates new charts with reduced complexity for guaranteed delivery
- **Chart Link Delivery**: Replaced chart image attachments with URL links to reduce message size and provide access to full interactive web interface
- **External Service Integration**: Successfully implemented chart upload to real external services (Imgur, Telegraph) for secure link-based delivery
- **Catbox Exclusive Hosting**: Charts are exclusively uploaded to Catbox.moe and shared as direct links in Telegram messages (removed all fallback services for simplicity)
- **Complete Server Privacy**: Real server address remains completely hidden while providing functional chart links through external hosting
- **Working Link Solution**: Users receive clickable chart links (`https://i.imgur.com/xxxxx.png`) that open charts directly without exposing server location
- **Extended Historical Data**: Updated chart system to display 3 years (1095 days) of data instead of 1 year for comprehensive market analysis
- **Fixed Date Processing**: Resolved 1970 date display issue by properly setting date index in market breadth calculations and improved date handling in chart generation functions
- **Disabled Link Preview**: Added `disable_web_page_preview=True` parameter to Telegram API calls to completely disable automatic link preview while keeping links clickable
- **Removed Chart Title**: Removed "Cryptocurrency Market Breadth Analysis" main title from chart screenshots for cleaner appearance

### July 03, 2025
- **JSON File Data Source**: System now reads ranking data directly from `parsed_ranks.json` file provided by user
- **Automatic Latest Date Detection**: Bot finds entry with most recent date and uses corresponding rank
- **Simplified Data Flow**: Removed SensorTower API dependency, system reads: Manual Override → JSON File → No Data
- **Real Data Integration**: Successfully shows rank 297 for date 2025-07-03 from user's parsed data
- **Daily Auto-Updates**: When new dates added to JSON, system automatically detects and reports latest ranking
- **Data Format**: JSON structure with date/rank pairs, system sorts by date to find latest entry
- **Schedule Update**: Changed execution time to 08:01 UTC (11:01 MSK)
- **Pre-execution Script**: Added rnk.py execution at 07:59 UTC (10:59 MSK) before main data collection
- **SensorTower Integration**: Implemented user's SensorTower API code in rnk.py for automated data collection
- **Dual Process System**: rnk.py collects fresh data at 10:59 MSK, main bot reads and sends at 11:01 MSK

### Initial Setup
- Core bot functionality with multi-source data collection
- Telegram integration with scheduled messaging
- Web dashboard for monitoring and manual controls
- JSON-based data persistence system

## User Preferences

Preferred communication style: Simple, everyday language.