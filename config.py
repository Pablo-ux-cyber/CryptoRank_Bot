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
# Используем переменные окружения для хранения чувствительных данных
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_BOT_TOKEN:
    # Выводим предупреждение, если не найден токен бота
    import logging
    logging.warning(
        "TELEGRAM_BOT_TOKEN not found in environment variables. "
        "Please setup environment variables or create .env file with token."
    )

# Может быть ID канала (@channel_name) или ID группы (вида -1001234567890)
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@cryptorankbase")  # Основной канал для отправки сообщений
# Тестовая группа: "@telegrm_hub"

# Канал, откуда бот получает данные о рейтинге (источник данных)
TELEGRAM_SOURCE_CHANNEL = os.environ.get("TELEGRAM_SOURCE_CHANNEL", "@coinbaseappstore")

# Scheduler Configuration
SCHEDULE_HOUR = 5  # 5 AM UTC (8:01 MSK)
SCHEDULE_MINUTE = 1  # 1 minute - 5:01 AM UTC (8:01 MSK)

# Selenium Configuration
SELENIUM_DRIVER_PATH = os.getenv("SELENIUM_DRIVER_PATH", "/usr/bin/chromedriver")
SELENIUM_HEADLESS = True
SELENIUM_TIMEOUT = 30  # seconds

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "sensortower_bot.log"

# Altcoin Season Index Configuration
ASI_VS_CURRENCY = os.getenv('ASI_VS_CURRENCY', 'usd')
ASI_TOP_N = int(os.getenv('ASI_TOP_N', '50'))
ASI_PERIOD = os.getenv('ASI_PERIOD', '30d')
ASI_THRESHOLD_STRONG = float(os.getenv('ASI_THRESHOLD_STRONG', '0.75'))
ASI_THRESHOLD_MODERATE = float(os.getenv('ASI_THRESHOLD_MODERATE', '0.50'))
ASI_THRESHOLD_WEAK = float(os.getenv('ASI_THRESHOLD_WEAK', '0.25'))

# MA200 Indicator Configuration
MA200_TOP_N = int(os.getenv('MA200_TOP_N', '50'))
MA200_MA_PERIOD = int(os.getenv('MA200_MA_PERIOD', '200'))
MA200_HISTORY_DAYS = int(os.getenv('MA200_HISTORY_DAYS', '365'))
MA200_OVERBOUGHT_THRESHOLD = float(os.getenv('MA200_OVERBOUGHT_THRESHOLD', '80'))
MA200_OVERSOLD_THRESHOLD = float(os.getenv('MA200_OVERSOLD_THRESHOLD', '10'))
MA200_CACHE_FILE = os.getenv('MA200_CACHE_FILE', 'ma200_cache.json')
MA200_RESULTS_FILE = os.getenv('MA200_RESULTS_FILE', 'ma200_data.csv')
MA200_CHART_FILE = os.getenv('MA200_CHART_FILE', 'ma200_chart.png')

# Global Order Book Imbalance Configuration
GBI_EXCHANGE = os.getenv('GBI_EXCHANGE', 'binance')
GBI_MARKETS = os.getenv('GBI_MARKETS', 'BTC/USDT,ETH/USDT,SOL/USDT,ADA/USDT,BNB/USDT')
GBI_LIMIT = int(os.getenv('GBI_LIMIT', '100'))
GBI_THRESHOLD_STRONG_BULL = float(os.getenv('GBI_THRESHOLD_STRONG_BULL', '0.50'))
GBI_THRESHOLD_WEAK_BULL = float(os.getenv('GBI_THRESHOLD_WEAK_BULL', '0.20'))
GBI_THRESHOLD_WEAK_BEAR = float(os.getenv('GBI_THRESHOLD_WEAK_BEAR', '-0.20'))
GBI_THRESHOLD_STRONG_BEAR = float(os.getenv('GBI_THRESHOLD_STRONG_BEAR', '-0.50'))
