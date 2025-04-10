#!/bin/bash

# Скрипт для первоначальной настройки Git на сервере
# Используйте: ./initial_git_setup.sh https://github.com/your-username/coinbasebot.git

if [ -z "$1" ]; then
    echo "Использование: $0 https://github.com/your-username/coinbasebot.git"
    exit 1
fi

REPO_URL=$1
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "[$TIMESTAMP] Начало настройки Git в каталоге $APP_DIR"

# Инициализация Git, если не инициализирован
if [ ! -d "$APP_DIR/.git" ]; then
    echo "[$TIMESTAMP] Инициализация Git репозитория..."
    git init
    echo "[$TIMESTAMP] Git репозиторий инициализирован."
else
    echo "[$TIMESTAMP] Git репозиторий уже инициализирован."
fi

# Проверка, добавлен ли уже репозиторий
REMOTE_EXISTS=$(git remote | grep -c "origin")
if [ $REMOTE_EXISTS -eq 0 ]; then
    echo "[$TIMESTAMP] Добавление удаленного репозитория origin: $REPO_URL"
    git remote add origin $REPO_URL
else
    echo "[$TIMESTAMP] Удаленный репозиторий origin уже существует. Обновление URL..."
    git remote set-url origin $REPO_URL
fi

# Проверка, есть ли хотя бы один коммит
if ! git log -1 &> /dev/null; then
    echo "[$TIMESTAMP] Создание начального коммита..."
    touch .gitkeep
    git add .gitkeep
    git commit -m "Initial commit"
fi

# Настройка ветки по умолчанию
echo "[$TIMESTAMP] Настройка ветки main..."
git checkout -b main 2>/dev/null || git checkout main

# Получение изменений
echo "[$TIMESTAMP] Получение изменений из удаленного репозитория..."
git pull origin main || echo "[$TIMESTAMP] Ошибка при получении данных. Возможно, репозиторий пуст или требуется аутентификация."

echo "[$TIMESTAMP] Настройка Git завершена."
echo "-----------------------------------"
echo "Следующие шаги:"
echo "1. Настройте учетные данные Git:"
echo "   git config --global user.name \"Your Name\""
echo "   git config --global user.email \"your.email@example.com\""
echo "   git config --global credential.helper store"
echo ""
echo "2. Настройте cron для запуска git_sync.sh:"
echo "   (crontab -l ; echo \"0 * * * * $APP_DIR/git_sync.sh\") | crontab -"
echo ""
echo "3. Сделайте скрипт синхронизации исполняемым:"
echo "   chmod +x $APP_DIR/git_sync.sh"
echo "-----------------------------------"