#!/bin/bash

# Быстрая проверка автоматического определения IP

echo "🔍 Тестирование автоматического определения IP адреса..."
echo ""

# Метод 1: hostname -I
ip1=$(hostname -I | awk '{print $1}')
echo "🔧 Метод 1 (hostname -I): $ip1"

# Метод 2: внешний IP
ip2=$(curl -s --connect-timeout 3 ifconfig.me 2>/dev/null)
echo "🌍 Метод 2 (ifconfig.me): $ip2"

# Метод 3: альтернативный сервис
ip3=$(curl -s --connect-timeout 3 icanhazip.com 2>/dev/null)
echo "🌐 Метод 3 (icanhazip.com): $ip3"

echo ""

# Выбираем лучший IP
if [ -n "$ip1" ] && [[ "$ip1" != "127."* ]]; then
    best_ip="$ip1"
    method="локальный (hostname -I)"
elif [ -n "$ip2" ]; then
    best_ip="$ip2"
    method="внешний (ifconfig.me)"
elif [ -n "$ip3" ]; then
    best_ip="$ip3"
    method="внешний (icanhazip.com)"
else
    best_ip="localhost"
    method="fallback"
fi

echo "✅ Выбранный IP: $best_ip ($method)"
echo "📍 URL для тестирования: http://$best_ip:5000/test-telegram-message"
echo ""

# Быстрая проверка доступности
echo "🔗 Проверка доступности сервера..."
if curl -s --connect-timeout 5 "http://$best_ip:5000/health" > /dev/null 2>&1; then
    echo "✅ Сервер доступен!"
    echo "🚀 Можно запускать: curl http://$best_ip:5000/test-telegram-message"
else
    echo "⚠️  Сервер недоступен или не отвечает на /health"
    echo "💡 Убедитесь что Flask приложение запущено на порту 5000"
fi