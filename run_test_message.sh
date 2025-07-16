#!/bin/bash

# Скрипт для автоматического запуска Test Real Message через cron
# Отправляет POST запрос к эндпоинту test-telegram-message

# Настройки
# Автоматическое определение IP адреса сервера
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    # Fallback: попробуем получить IP через другие методы
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "localhost")
fi
SERVER_URL="http://$SERVER_IP:5000"
ENDPOINT="/test-telegram-message"
LOG_FILE="/tmp/test_message_cron.log"

echo "$(date): Запуск Test Real Message через cron" >> "$LOG_FILE"

# Выполняем запрос
response=$(curl -s -X POST "$SERVER_URL$ENDPOINT" -w "HTTP_CODE:%{http_code}")

# Извлекаем HTTP код
http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
response_body=$(echo "$response" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$http_code" = "200" ]; then
    echo "$(date): ✅ Сообщение отправлено успешно" >> "$LOG_FILE"
    echo "$response_body" >> "$LOG_FILE"
else
    echo "$(date): ❌ Ошибка отправки (HTTP $http_code)" >> "$LOG_FILE"
    echo "$response_body" >> "$LOG_FILE"
fi

echo "$(date): Завершение cron задания" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"