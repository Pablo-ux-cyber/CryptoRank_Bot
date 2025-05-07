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
SCHEDULE_MINUTE = 0  # 00 minutes

# Selenium Configuration
SELENIUM_DRIVER_PATH = os.getenv("SELENIUM_DRIVER_PATH", "/usr/bin/chromedriver")
SELENIUM_HEADLESS = True
SELENIUM_TIMEOUT = 30  # seconds

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "sensortower_bot.log"
