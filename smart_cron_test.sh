#!/bin/bash

# Умный скрипт для cron с автоматическим определением IP
# Работает на любом сервере без изменения настроек

# Определяем IP адрес сервера автоматически
get_server_ip() {
    # Метод 1: локальный IP
    local ip=$(hostname -I | awk '{print $1}')
    
    # Метод 2: внешний IP (если локальный не подходит)
    if [ -z "$ip" ] || [[ "$ip" == "127."* ]]; then
        ip=$(curl -s --connect-timeout 5 ifconfig.me 2>/dev/null)
    fi
    
    # Метод 3: альтернативный сервис
    if [ -z "$ip" ]; then
        ip=$(curl -s --connect-timeout 5 icanhazip.com 2>/dev/null)
    fi
    
    # Fallback: localhost
    if [ -z "$ip" ]; then
        ip="localhost"
    fi
    
    echo "$ip"
}

# Настройки
SERVER_IP=$(get_server_ip)
SERVER_URL="http://$SERVER_IP:5000"
ENDPOINT="/test-telegram-message"
LOG_FILE="/tmp/smart_cron_test.log"

# Логирование с отметкой времени и IP
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$SERVER_IP] $1" >> "$LOG_FILE"
}

log_message "=== Запуск умного cron теста ==="
log_message "Определен IP сервера: $SERVER_IP"
log_message "URL: $SERVER_URL$ENDPOINT"

# Проверяем доступность сервера
if ! curl -s --connect-timeout 10 "$SERVER_URL/health" > /dev/null 2>&1; then
    log_message "❌ ОШИБКА: Сервер недоступен по адресу $SERVER_URL"
    log_message "Возможные причины:"
    log_message "  - Flask приложение не запущено"
    log_message "  - Неправильный порт (проверьте что сервер слушает :5000)"
    log_message "  - Проблемы с сетью"
    exit 1
fi

log_message "✅ Сервер доступен, отправляем запрос..."

# Выполняем основной запрос с таймаутом
response=$(curl -s --connect-timeout 10 --max-time 300 -w "HTTP_CODE:%{http_code}" "$SERVER_URL$ENDPOINT" 2>&1)

# Обрабатываем результат
if echo "$response" | grep -q "HTTP_CODE:200"; then
    log_message "✅ Сообщение отправлено успешно"
    
    # Извлекаем полезную информацию из ответа
    if echo "$response" | grep -q "success.*true"; then
        log_message "✅ Telegram подтвердил доставку"
    else
        log_message "⚠️  Запрос выполнен, но статус Telegram неизвестен"
    fi
    
elif echo "$response" | grep -q "HTTP_CODE:"; then
    http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    log_message "❌ HTTP ошибка: код $http_code"
    log_message "Ответ сервера: $(echo "$response" | sed 's/HTTP_CODE:[0-9]*$//' | head -3)"
    
else
    log_message "❌ Ошибка сети или таймаут"
    log_message "Детали: $response"
fi

log_message "=== Завершение cron теста ==="
log_message ""

# Показываем последние записи лога (для отладки при ручном запуске)
if [ -t 1 ]; then
    echo "Последние записи лога:"
    tail -10 "$LOG_FILE"
fi