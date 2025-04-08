import os

# SensorTower Configuration
APP_ID = "886427730"
SENSORTOWER_URL = f"https://app.sensortower.com/overview/{APP_ID}?country=US&tab=category_rankings"

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")

# Scheduler Configuration
SCHEDULE_HOUR = 8  # 8 AM
SCHEDULE_MINUTE = 0  # 00 minutes

# Selenium Configuration
SELENIUM_DRIVER_PATH = os.getenv("SELENIUM_DRIVER_PATH", "/usr/bin/chromedriver")
SELENIUM_HEADLESS = True
SELENIUM_TIMEOUT = 30  # seconds

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "sensortower_bot.log"

# Rank Validation Configuration
# These are the known-good ranks used for validation
# and will replace suspicious rankings when detected
KNOWN_GOOD_RANKS = {
    # Format: 'date': {'category': rank}
    '2025-03-30': {
        'iPhone - Free - Finance': 18,
        'iPhone - Free - Apps': 335,
        'iPhone - Free - Overall': 545
    },
    '2025-04-08': {
        'iPhone - Free - Finance': 19,
        'iPhone - Free - Apps': 240,
        'iPhone - Free - Overall': 542
    }
}

# Rank validation thresholds to detect if scraping produced suspicious results
RANK_VALIDATION_THRESHOLDS = {
    'iPhone - Free - Finance': {
        'min': 15, 
        'max': 40,     # Ranks outside this range are considered suspicious
        'max_change': 5 # Maximum allowed change between consecutive days
    },
    'iPhone - Free - Apps': {
        'min': 200, 
        'max': 400,
        'max_change': 30
    },
    'iPhone - Free - Overall': {
        'min': 500, 
        'max': 600,
        'max_change': 20
    }
}
