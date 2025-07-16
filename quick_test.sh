#!/bin/bash

# Быстрый тест запуска Test Real Message
# Для проверки что система работает

echo "🚀 Запуск Test Real Message..."
echo "📍 URL: http://172.31.128.39:5000/test-telegram-message"
echo ""

# Показать текущее время
echo "⏰ Время запуска: $(date)"
echo ""

# Выполнить запрос в фоне и показать статус
echo "📡 Отправка запроса..."
response=$(timeout 300 curl -s "http://172.31.128.39:5000/test-telegram-message" 2>&1)
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ Запрос завершен успешно!"
    # Показать только первые строки ответа
    echo "$response" | head -5
    echo "..."
else
    echo "⚠️  Запрос прервался (возможно timeout или ошибка)"
    echo "Exit code: $exit_code"
fi

echo ""
echo "🏁 Завершено: $(date)"