#!/bin/bash
# Скрипт для синхронизации кода из GitHub с вашим сервером
# Использование: ./sync.sh [reponame] [branch]
# Пример: ./sync.sh coinbase-rank-bot main
# Если параметры не указаны, используются значения по умолчанию

# Получение имени репозитория из аргументов или использование значения по умолчанию
REPO_NAME="${1:-coinbase-rank-bot}"
BRANCH="${2:-main}"

# Настройки
GITHUB_USERNAME="yourusername"  # Ваше имя пользователя GitHub
REPO_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
TARGET_DIR="/root/coinbaserank_bot"  # Директория назначения на вашем сервере
SERVICE_NAME="coinbasebot"  # Имя systemd-сервиса для Telegram-бота

# Если вы используете SSH вместо HTTPS для клонирования, раскомментируйте строку ниже
# REPO_URL="git@github.com:$GITHUB_USERNAME/$REPO_NAME.git"

echo "Starting synchronization process..."
echo "Repository: $REPO_URL"
echo "Target directory: $TARGET_DIR"
echo "Branch: $BRANCH"

# Проверка существования директории
if [ ! -d "$TARGET_DIR" ]; then
    echo "Target directory does not exist. Creating..."
    mkdir -p "$TARGET_DIR"
    
    # Клонирование репозитория, если директория была только что создана
    echo "Cloning repository..."
    git clone --branch "$BRANCH" "$REPO_URL" "$TARGET_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to clone repository."
        exit 1
    fi
else
    # Директория существует, выполняем pull
    echo "Target directory exists. Updating..."
    cd "$TARGET_DIR" || { echo "Error: Could not change to target directory."; exit 1; }
    
    # Сохраняем локальные изменения, если они есть
    git stash
    
    # Переключаемся на нужную ветку
    git checkout "$BRANCH"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to checkout branch $BRANCH."
        exit 1
    fi
    
    # Получаем последние изменения
    git pull origin "$BRANCH"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to pull changes from origin."
        exit 1
    fi
    
    # При необходимости, применяем сохраненные локальные изменения
    git stash pop
fi

# Дополнительные действия после обновления кода
# Например, перезапуск сервисов, обновление зависимостей и т.д.
echo "Updating dependencies..."
if [ -f "$TARGET_DIR/requirements.txt" ]; then
    cd "$TARGET_DIR" && pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found. Skipping pip install."
fi

echo "Setting proper permissions..."
chmod +x "$TARGET_DIR/sync.sh"

# Сохранение переменных окружения (если есть)
if [ -f "$TARGET_DIR/.env" ]; then
    echo "Backing up environment variables..."
    cp "$TARGET_DIR/.env" "$TARGET_DIR/.env.backup"
fi

# Восстановление переменных окружения из бэкапа (если исходный файл был перезаписан)
if [ -f "$TARGET_DIR/.env.backup" ] && [ ! -f "$TARGET_DIR/.env" ]; then
    echo "Restoring environment variables from backup..."
    cp "$TARGET_DIR/.env.backup" "$TARGET_DIR/.env"
fi

echo "Restarting services..."
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME

echo "Synchronization completed successfully!"
exit 0