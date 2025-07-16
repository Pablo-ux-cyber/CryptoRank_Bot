#!/bin/bash

# Быстрый тест запуска Test Real Message
# Для проверки что система работает

# Автоматическое определение IP адреса
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "localhost")
fi

echo "🚀 Запуск Test Real Message..."
echo "📍 URL: http://$SERVER_IP:5000/test-telegram-message"
echo ""

# Показать текущее время
echo "⏰ Время запуска: $(date)"
echo ""

# Выполнить запрос в фоне и показать статус
echo "📡 Отправка запроса..."
response=$(timeout 300 curl -s "http://$SERVER_IP:5000/test-telegram-message" 2>&1)
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