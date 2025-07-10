#!/bin/bash

# Автозапуск Coinbase Rank Telegram Bot

echo "Запуск Coinbase Rank Telegram Bot..."
echo "Время запуска: $(date)"

# Переходим в директорию бота
cd "$(dirname "$0")"

# Убеждаемся что все зависимости установлены
if ! command -v python3 &> /dev/null; then
    echo "Python3 не найден!"
    exit 1
fi

# Убеждаемся что файл main.py существует
if [ ! -f "main.py" ]; then
    echo "main.py не найден в $(pwd)"
    exit 1
fi

# Убеждаемся что переменные окружения установлены
if [ -f ".env" ]; then
    source .env
    echo "Загружены переменные из .env"
fi

# Убиваем предыдущие процессы (если есть)
pkill -f "python.*main.py" 2>/dev/null || true

# Очищаем старые файлы блокировки
rm -f coinbasebot.lock

# Запускаем бота
echo "Запуск python3 main.py..."
exec python3 main.py