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
SCHEDULE_HOUR = 8  # 8 AM
SCHEDULE_MINUTE = 10  # 10 minutes, to match the 11:10 MSK deployment time
ADDITIONAL_CHECK_HOUR = 9  # 9 AM
ADDITIONAL_CHECK_MINUTE = 5  # 12:05 MSK - дополнительная проверка для поздних обновлений

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
