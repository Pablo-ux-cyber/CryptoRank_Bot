import os
from datetime import datetime, timedelta

# SensorTower Configuration
APP_ID = "886427730"

# Формируем URL с датами для последних 90 дней
today = datetime.now()
start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")

# Новый URL для анализа категорий и рейтингов
SENSORTOWER_URL = f"https://app.sensortower.com/app-analysis/category-rankings?os=ios&edit=1&granularity=daily&start_date={start_date}&end_date={end_date}&duration=P90D&country=US&breakdown_attribute=category&metricType=absolute&measure=revenue&rolling_days=0&selected_tab=0&session_count=sessionCount&time_spent=timeSpent&chart_plotting_type=line&sia={APP_ID}&ssia={APP_ID}&chart_type=free&chart_type=paid&chart_type=grossing&device=iphone&device=ipad&category=0&category=36&category=6015&time_period=day"

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "7973595268:AAG_Pz_xZFnAXRHtVbTH5Juo8qtssPUof8E"
# Может быть ID канала (@channel_name) или ID группы (вида -1001234567890)
TELEGRAM_CHANNEL_ID = "@telegrm_hub"  # Тестовая группа для отправки сообщений
# Для возврата в основной канал: "@cryptorankbase"
# Канал, откуда бот получает данные о рейтинге (источник данных)
TELEGRAM_SOURCE_CHANNEL = "@coinbaseappstore"

# Scheduler Configuration
SCHEDULE_HOUR = 8  # 8 AM
SCHEDULE_MINUTE = 10  # 10 minutes, to match the 11:10 MSK deployment time

# Selenium Configuration
SELENIUM_DRIVER_PATH = os.getenv("SELENIUM_DRIVER_PATH", "/usr/bin/chromedriver")
SELENIUM_HEADLESS = True
SELENIUM_TIMEOUT = 30  # seconds

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "sensortower_bot.log"

# Order Book Imbalance Configuration
GBI_EXCHANGE = os.getenv('GBI_EXCHANGE', 'binance')
GBI_MARKETS = os.getenv('GBI_MARKETS', 'BTC/USDT,ETH/USDT,SOL/USDT,ADA/USDT,BNB/USDT')
GBI_LIMIT = int(os.getenv('GBI_LIMIT', '100'))
GBI_THRESHOLD_STRONG_BULL = float(os.getenv('GBI_THRESHOLD_STRONG_BULL', '0.50'))
GBI_THRESHOLD_WEAK_BULL = float(os.getenv('GBI_THRESHOLD_WEAK_BULL', '0.20'))
GBI_THRESHOLD_WEAK_BEAR = float(os.getenv('GBI_THRESHOLD_WEAK_BEAR', '-0.20'))
GBI_THRESHOLD_STRONG_BEAR = float(os.getenv('GBI_THRESHOLD_STRONG_BEAR', '-0.50'))
