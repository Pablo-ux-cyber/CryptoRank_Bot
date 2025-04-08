import os

# SensorTower Configuration
APP_ID = "886427730"
SENSORTOWER_URL = f"https://app.sensortower.com/overview/{APP_ID}?country=US&tab=category_rankings"
SENSORTOWER_DETAILED_URL = f"https://app.sensortower.com/app-analysis/category-rankings?os=ios&edit=1&granularity=daily&start_date=2025-01-09&end_date=2025-04-08&duration=P90D&country=US&breakdown_attribute=category&metricType=absolute&measure=revenue&rolling_days=0&selected_tab=0&session_count=sessionCount&time_spent=timeSpent&chart_plotting_type=line&sia={APP_ID}&ssia={APP_ID}&chart_type=free&chart_type=paid&chart_type=grossing&device=iphone&device=ipad&category=0&category=36&category=6015&time_period=day"

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")

# Scheduler Configuration
SCHEDULE_HOUR = 8  # 8 AM
SCHEDULE_MINUTE = 0  # 00 minutes

# Selenium Configuration
# Используем chromedriver-py для автоматического нахождения пути к драйверу
try:
    from chromedriver_py import binary_path
    SELENIUM_DRIVER_PATH = binary_path
except ImportError:
    SELENIUM_DRIVER_PATH = os.getenv("SELENIUM_DRIVER_PATH", "/usr/bin/chromedriver")
    
SELENIUM_HEADLESS = True
SELENIUM_TIMEOUT = 30  # seconds

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "sensortower_bot.log"
