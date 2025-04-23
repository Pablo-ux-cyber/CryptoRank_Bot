#!/bin/bash
# Упрощенный скрипт для синхронизации кода из GitHub
# Автоматически исключает логи и данные из синхронизации

TARGET_DIR="/root/coinbaserank_bot"
SERVICE_NAME="coinbasebot"
GIT_REPO="origin"
GIT_BRANCH="main"

echo "====== ПРОСТАЯ СИНХРОНИЗАЦИЯ ======"
echo "Target directory: $TARGET_DIR"
echo "Service: $SERVICE_NAME"
echo "Branch: $GIT_BRANCH"

# Создаем .gitignore, если его нет
if [ ! -f "$TARGET_DIR/.gitignore" ]; then
    echo "Creating .gitignore..."
    cat > "$TARGET_DIR/.gitignore" << EOL
# Игнорировать файлы с данными
*.json
*.log
rank_history.txt
coinbasebot.lock
manual_operation.lock
# Игнорировать виртуальное окружение
venv/
__pycache__/
EOL
fi

# Проверяем наличие файла config.py и создаем бэкап
if [ -f "$TARGET_DIR/config.py" ]; then
    echo "Backing up config.py..."
    cp "$TARGET_DIR/config.py" "$TARGET_DIR/config.py.bak"
fi

# Переходим в директорию проекта
cd "$TARGET_DIR" || { echo "Error: Could not change to target directory"; exit 1; }

# Получаем изменения с сервера
echo "Getting changes from GitHub..."
git stash
git pull "$GIT_REPO" "$GIT_BRANCH"

# Восстанавливаем config.py, если он был изменен
if [ -f "$TARGET_DIR/config.py.bak" ]; then
    if ! diff -q "$TARGET_DIR/config.py" "$TARGET_DIR/config.py.bak" >/dev/null 2>&1; then
        echo "Restoring config.py from backup..."
        cp "$TARGET_DIR/config.py.bak" "$TARGET_DIR/config.py"
    fi
fi

# Устанавливаем разрешения на выполнение для скриптов
echo "Setting execution permissions..."
chmod +x "$TARGET_DIR"/*.sh

# Перезапускаем сервис
echo "Restarting service..."
systemctl restart "$SERVICE_NAME"

echo "Synchronization completed!"
echo "Check service status: systemctl status $SERVICE_NAME"
exit 0