#!/bin/bash
# Скрипт для удаления всех файлов блокировок

echo "Удаляю все файлы блокировок..."

# Удаляем файл блокировки бота
if [ -f "coinbasebot.lock" ]; then
    echo "Удаляю coinbasebot.lock"
    rm coinbasebot.lock
fi

# Удаляем файл блокировки ручной операции
if [ -f "manual_operation.lock" ]; then
    echo "Удаляю manual_operation.lock"
    rm manual_operation.lock
fi

echo "Готово! Все файлы блокировок удалены."
echo "Перезапустите бота, чтобы изменения вступили в силу."