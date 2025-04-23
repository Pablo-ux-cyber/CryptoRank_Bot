#!/bin/bash
# restore_config.sh - Скрипт для восстановления конфигурации

TARGET_DIR=$(dirname "$0")
cd "$TARGET_DIR" || { echo "Error: Could not change to target directory."; exit 1; }

echo "====== Configuration Restoration ======"
echo "Target directory: $TARGET_DIR"

# Проверяем существование файла config.py
if [ -f "$TARGET_DIR/config.py" ]; then
    echo "config.py already exists."
    echo "Backing up as config.py.bak..."
    cp "$TARGET_DIR/config.py" "$TARGET_DIR/config.py.bak"
fi

# Восстанавливаем config.py
echo "Creating config.py with direct token values..."
cat > "$TARGET_DIR/config.py" << EOL
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
TELEGRAM_CHANNEL_ID = "@cryptorankbase"
# Канал, откуда бот получает данные о рейтинге (источник данных)
TELEGRAM_SOURCE_CHANNEL = "@coinbaseappstore"

# Scheduler Configuration
SCHEDULE_HOUR = 8  # 8 AM
SCHEDULE_MINUTE = 0  # 00 minutes

# Selenium Configuration
SELENIUM_DRIVER_PATH = "/usr/bin/chromedriver"
SELENIUM_HEADLESS = True
SELENIUM_TIMEOUT = 30  # seconds

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "sensortower_bot.log"
EOL

# Создаем .gitignore если его нет
if [ ! -f "$TARGET_DIR/.gitignore" ]; then
    echo "Creating .gitignore..."
    cat > "$TARGET_DIR/.gitignore" << EOL
# Ignore local configuration files
.env
venv/
__pycache__/
*.log
coinbasebot.lock
manual_operation.lock

# Ignore data files
*.json
*.db
rank_history.txt
EOL
fi

# Устанавливаем разрешения на выполнение для скриптов
echo "Setting execution permission for scripts..."
chmod +x "$TARGET_DIR/sync.sh"
chmod +x "$TARGET_DIR/setup_venv.sh"
chmod +x "$TARGET_DIR/restore_config.sh"

echo "Done! Your configuration has been restored."
echo "Token TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID have been set directly in config.py"
echo ""
echo "Now you should run setup_venv.sh to restore the virtual environment:"
echo "./setup_venv.sh"
exit 0