# Coinbase Rank Telegram Bot

## Overview

This is a Python-based Telegram bot that monitors cryptocurrency market sentiment indicators and automatically sends notifications to Telegram channels. The bot tracks Coinbase app rankings from user-provided JSON data, cryptocurrency Fear & Greed Index, Google Trends data for crypto-related terms, and Altcoin Season Index to provide comprehensive market sentiment analysis. Runs daily at 8:01 UTC (11:01 MSK).

## System Architecture

### Core Technologies
- **Backend**: Python 3.10+ with Flask web framework
- **Data Storage**: JSON files for data persistence (no database required)
- **Scheduling**: Custom threading-based scheduler with file locking mechanism
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

1. **Scheduled Execution**: The scheduler runs daily at 08:01 UTC (11:01 MSK)
2. **Data Collection**: Each module fetches its respective data from external sources
3. **Change Detection**: System compares new data with historical values stored in JSON files
4. **Message Composition**: If changes are detected, a formatted message is created
5. **Notification Delivery**: Message is sent to the configured Telegram channel
6. **Data Persistence**: New data is saved to JSON history files

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

### July 03, 2025
- **JSON File Data Source**: System now reads ranking data directly from `parsed_ranks.json` file provided by user
- **Automatic Latest Date Detection**: Bot finds entry with most recent date and uses corresponding rank
- **Simplified Data Flow**: Removed SensorTower API dependency, system reads: Manual Override → JSON File → No Data
- **Real Data Integration**: Successfully shows rank 297 for date 2025-07-03 from user's parsed data
- **Daily Auto-Updates**: When new dates added to JSON, system automatically detects and reports latest ranking
- **Data Format**: JSON structure with date/rank pairs, system sorts by date to find latest entry
- **Schedule Update**: Changed execution time from 08:25 UTC to 08:01 UTC (11:01 MSK)

### Initial Setup
- Core bot functionality with multi-source data collection
- Telegram integration with scheduled messaging
- Web dashboard for monitoring and manual controls
- JSON-based data persistence system

## User Preferences

Preferred communication style: Simple, everyday language.