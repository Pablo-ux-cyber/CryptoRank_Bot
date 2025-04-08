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
