#!/bin/bash
# Скрипт для восстановления критически важных конфигурационных файлов
# Используется в случае, если файлы были удалены или повреждены

# Директория проекта
PROJECT_DIR="/root/coinbaserank_bot"
SERVICE_NAME="coinbasebot"

echo "Starting configuration restoration for CoinbaseRank Bot..."
cd "$PROJECT_DIR" || { echo "Error: Could not change to project directory."; exit 1; }

# Проверяем наличие бэкапов
BACKUP_FOUND=0
for BACKUP_FILE in "$PROJECT_DIR/.env.backup" "$PROJECT_DIR/backup_tmp/.env" "$PROJECT_DIR/.env.old"; do
    if [ -f "$BACKUP_FILE" ]; then
        echo "Found backup .env file: $BACKUP_FILE"
        cp "$BACKUP_FILE" "$PROJECT_DIR/.env"
        echo "Restored .env from backup: $BACKUP_FILE"
        BACKUP_FOUND=1
        break
    fi
done

# Если бэкап не найден, нужно создать новый файл
if [ $BACKUP_FOUND -eq 0 ]; then
    echo "No backup .env file found. Creating a new template."
    echo "Please enter your Telegram bot token (from @BotFather):"
    read -p "TELEGRAM_BOT_TOKEN=" BOT_TOKEN
    
    echo "Please enter your Telegram channel ID (e.g., -100xxxxxxxxx for @cryptorankbase):"
    read -p "TELEGRAM_CHANNEL_ID=" CHANNEL_ID
    
    # Создаем .env файл с введенными данными
    cat > "$PROJECT_DIR/.env" << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_CHANNEL_ID=$CHANNEL_ID
EOF
    echo "Created new .env file with provided tokens."
fi

# Проверяем наличие config.py
BACKUP_FOUND=0
for BACKUP_FILE in "$PROJECT_DIR/config.py.backup" "$PROJECT_DIR/backup_tmp/config.py" "$PROJECT_DIR/config.py.old"; do
    if [ -f "$BACKUP_FILE" ]; then
        echo "Found backup config.py file: $BACKUP_FILE"
        cp "$BACKUP_FILE" "$PROJECT_DIR/config.py"
        echo "Restored config.py from backup: $BACKUP_FILE"
        BACKUP_FOUND=1
        break
    fi
done

# Если бэкап не найден, нужно создать новый файл
if [ $BACKUP_FOUND -eq 0 ]; then
    echo "No backup config.py file found. Creating a new template."
    
    # Если уже создали .env, используем эти же значения
    if [ -f "$PROJECT_DIR/.env" ]; then
        BOT_TOKEN=$(grep "TELEGRAM_BOT_TOKEN" "$PROJECT_DIR/.env" | cut -d "=" -f2)
        CHANNEL_ID=$(grep "TELEGRAM_CHANNEL_ID" "$PROJECT_DIR/.env" | cut -d "=" -f2)
    else
        echo "Please enter your Telegram bot token (from @BotFather):"
        read -p "TELEGRAM_BOT_TOKEN=" BOT_TOKEN
        
        echo "Please enter your Telegram channel ID (e.g., -100xxxxxxxxx for @cryptorankbase):"
        read -p "TELEGRAM_CHANNEL_ID=" CHANNEL_ID
    fi
    
    # Создаем config.py файл с введенными данными
    cat > "$PROJECT_DIR/config.py" << EOF
# Telegram bot token (получается от @BotFather)
TELEGRAM_BOT_TOKEN = "$BOT_TOKEN" # Токен вашего бота

# ID канала для отправки сообщений
TELEGRAM_CHANNEL_ID = "$CHANNEL_ID" # ID вашего канала @cryptorankbase

# Имя и логин Telegram бота
TELEGRAM_BOT_NAME = "CoinbaseRank Bot"
TELEGRAM_BOT_USERNAME = "baserank_bot"

# Настройки для Fear & Greed Index
FEAR_GREED_INDEX_URL = "https://api.alternative.me/fng/?limit=1"

# Интервал проверки данных в секундах (по умолчанию 5 минут = 300 секунд)
CHECK_INTERVAL = 300

# Час для ежедневной проверки Google Trends (по умолчанию 11:00)
GOOGLE_TRENDS_CHECK_HOUR = 11

# Время кеширования данных Google Trends в часах (по умолчанию 48 часов)
GOOGLE_TRENDS_CACHE_HOURS = 48
EOF
    echo "Created new config.py file with provided tokens."
fi

# Перезапускаем службу
echo "Restarting the service..."
sudo systemctl daemon-reload
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME"

echo "Configuration restoration completed!"
echo "If the bot is still not working, try running setup_venv.sh to rebuild the virtual environment."
exit 0