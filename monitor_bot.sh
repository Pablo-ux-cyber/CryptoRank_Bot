#!/bin/bash

# Мониторинг и автоперезапуск Coinbase Rank Telegram Bot

SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR"

# Функция проверки работает ли бот
check_bot_running() {
    if pgrep -f "python.*main.py" > /dev/null; then
        return 0  # Бот работает
    else
        return 1  # Бот не работает
    fi
}

# Функция запуска бота
start_bot() {
    echo "$(date): Запуск бота..."
    ./start_bot.sh &
    sleep 10
}

# Основной цикл мониторинга
while true; do
    if check_bot_running; then
        echo "$(date): Бот работает нормально"
    else
        echo "$(date): Бот не работает! Перезапуск..."
        start_bot
    fi
    
    # Проверка каждые 5 минут
    sleep 300
done