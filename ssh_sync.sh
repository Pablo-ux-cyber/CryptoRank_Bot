#!/bin/bash

# Скрипт для синхронизации кода с сервером через SSH
# Используйте: ./ssh_sync.sh user@your-server /path/to/coinbasebot

# Проверяем переданы ли аргументы
if [ $# -lt 2 ]; then
    echo "Использование: $0 user@your-server /path/to/coinbasebot"
    echo "Пример: $0 root@123.45.67.89 /home/user/coinbasebot"
    exit 1
fi

SERVER=$1
REMOTE_PATH=$2
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "[$TIMESTAMP] Начало синхронизации с сервером $SERVER"

# Проверяем, есть ли несохраненные изменения
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️ Обнаружены несохраненные изменения в локальном репозитории."
    echo "Рекомендуется сначала сделать коммит:"
    echo "  git add ."
    echo "  git commit -m \"Ваше сообщение\""
    echo "  git push origin main"
    
    read -p "Продолжить синхронизацию без коммита изменений? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "[$TIMESTAMP] Синхронизация отменена."
        exit 1
    fi
fi

# Запускаем rsync для синхронизации файлов (исключая .git и другие служебные файлы)
echo "[$TIMESTAMP] Копирование файлов на сервер $SERVER..."
rsync -avz --exclude '.git' --exclude 'venv' --exclude '__pycache__' \
      --exclude '*.pyc' --exclude '*.log' --exclude '.DS_Store' \
      --exclude 'manual_sync.sh' --exclude 'ssh_sync.sh' \
      --exclude '.replit' --exclude 'replit.nix' \
      . $SERVER:$REMOTE_PATH

# Проверяем результат rsync
if [ $? -eq 0 ]; then
    echo "[$TIMESTAMP] Файлы успешно скопированы на сервер."
    
    # Перезапускаем сервис на сервере
    echo "[$TIMESTAMP] Перезапуск сервиса coinbasebot..."
    ssh $SERVER "cd $REMOTE_PATH && sudo systemctl restart coinbasebot"
    
    if [ $? -eq 0 ]; then
        echo "[$TIMESTAMP] Сервис успешно перезапущен."
    else
        echo "[$TIMESTAMP] ⚠️ Возникла ошибка при перезапуске сервиса."
    fi
else
    echo "[$TIMESTAMP] ❌ Ошибка при копировании файлов на сервер."
    exit 1
fi

echo "[$TIMESTAMP] Синхронизация завершена успешно."