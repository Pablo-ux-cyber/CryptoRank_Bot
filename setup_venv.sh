#!/bin/bash
# Скрипт для автоматического создания виртуального окружения и установки зависимостей
# Используется в случае, если виртуальное окружение было удалено или повреждено

# Директория проекта
PROJECT_DIR="/root/coinbaserank_bot"
SERVICE_NAME="coinbasebot"

echo "Starting environment setup for CoinbaseRank Bot..."
cd "$PROJECT_DIR" || { echo "Error: Could not change to project directory."; exit 1; }

# Проверка существования виртуального окружения
if [ -d "$PROJECT_DIR/venv" ] && [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    echo "Virtual environment already exists."
    read -p "Do you want to recreate it? (y/n): " RECREATE
    if [ "$RECREATE" != "y" ]; then
        echo "Setup aborted. Using existing virtual environment."
        exit 0
    else
        echo "Removing existing virtual environment..."
        rm -rf "$PROJECT_DIR/venv"
    fi
fi

# Создание нового виртуального окружения
echo "Creating new virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment."
    exit 1
fi

# Активация виртуального окружения и установка зависимостей
echo "Activating virtual environment and installing dependencies..."
source "$PROJECT_DIR/venv/bin/activate"

# Обновление pip
echo "Upgrading pip..."
pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo "Warning: Failed to upgrade pip. Continuing anyway..."
fi

# Установка зависимостей
echo "Installing dependencies..."
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies from requirements.txt."
        echo "Trying to install essential packages manually..."
    fi
else
    echo "requirements.txt not found. Installing essential packages manually..."
fi

# Установка основных пакетов вручную в случае проблем с requirements.txt
pip install flask flask-sqlalchemy apscheduler trafilatura pytrends pandas requests pytz selenium email-validator python-telegram-bot gunicorn psycopg2-binary telegram
if [ $? -ne 0 ]; then
    echo "Error: Failed to install essential packages."
    exit 1
fi

# Создание requirements.txt из установленных пакетов
echo "Creating requirements.txt from installed packages..."
pip freeze > "$PROJECT_DIR/requirements.txt"

# Проверка наличия конфигурационных файлов
echo "Checking configuration files..."
if [ ! -f "$PROJECT_DIR/config.py" ]; then
    echo "Warning: config.py not found!"
    read -p "Do you want to create a template config.py? (y/n): " CREATE_CONFIG
    if [ "$CREATE_CONFIG" == "y" ]; then
        cat > "$PROJECT_DIR/config.py" << 'EOF'
# Telegram bot token (получается от @BotFather)
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE" # Замените на ваш настоящий токен

# ID канала для отправки сообщений
TELEGRAM_CHANNEL_ID = "YOUR_CHANNEL_ID_HERE" # Замените на ID вашего канала @cryptorankbase

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
        echo "Created template config.py. Please edit it with your actual tokens!"
    fi
fi

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Warning: .env file not found!"
    read -p "Do you want to create a template .env file? (y/n): " CREATE_ENV
    if [ "$CREATE_ENV" == "y" ]; then
        cat > "$PROJECT_DIR/.env" << 'EOF'
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHANNEL_ID=YOUR_CHANNEL_ID_HERE
EOF
        echo "Created template .env file. Please edit it with your actual tokens!"
    fi
fi

# Восстановление сервиса
echo "Restarting the service..."
sudo systemctl daemon-reload
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME"

echo "Environment setup completed successfully!"
echo "Please check that all required configuration files have been created and contain the correct data."
echo "You can now use the bot!"
exit 0