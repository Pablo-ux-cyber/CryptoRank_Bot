#!/bin/bash
# setup_venv.sh - Скрипт для восстановления виртуального окружения

TARGET_DIR=$(dirname "$0")
cd "$TARGET_DIR" || { echo "Error: Could not change to target directory."; exit 1; }

echo "====== Virtual Environment Setup ======"
echo "Target directory: $TARGET_DIR"

# Проверяем существование виртуального окружения
if [ -d "$TARGET_DIR/venv" ] && [ -f "$TARGET_DIR/venv/bin/activate" ]; then
    echo "Virtual environment already exists."
    read -p "Do you want to recreate it? (y/n): " recreate
    if [ "$recreate" != "y" ]; then
        echo "Keeping existing virtual environment."
        echo "Setting execution permission for scripts..."
        chmod +x "$TARGET_DIR/sync.sh"
        chmod +x "$TARGET_DIR/setup_venv.sh"
        chmod +x "$TARGET_DIR/restore_config.sh"
        
        echo "Done! Your virtual environment is ready."
        exit 0
    fi
    
    echo "Removing existing virtual environment..."
    rm -rf "$TARGET_DIR/venv"
fi

# Создание нового виртуального окружения
echo "Creating new virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment."
    echo "Make sure python3-venv is installed:"
    echo "sudo apt-get update && sudo apt-get install -y python3-venv"
    exit 1
fi

# Активация виртуального окружения
echo "Activating virtual environment..."
source venv/bin/activate

# Обновление pip
echo "Upgrading pip..."
pip install --upgrade pip

# Установка зависимостей
echo "Installing dependencies..."
if [ -f "$TARGET_DIR/requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies."
        exit 1
    fi
else
    echo "requirements.txt not found, installing default dependencies..."
    pip install flask flask-sqlalchemy apscheduler trafilatura pytrends pandas requests pytz selenium email-validator python-telegram-bot gunicorn psycopg2-binary telegram
    
    echo "Generating requirements.txt from installed packages..."
    pip freeze > requirements.txt
fi

# Установка разрешений на выполнение для скриптов
echo "Setting execution permission for scripts..."
chmod +x "$TARGET_DIR/sync.sh"
chmod +x "$TARGET_DIR/setup_venv.sh"
chmod +x "$TARGET_DIR/restore_config.sh"

echo "Done! Virtual environment has been set up successfully."
echo "To activate it manually: source venv/bin/activate"
exit 0