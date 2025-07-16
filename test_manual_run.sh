#!/bin/bash

# Ручной тест скрипта с подробной диагностикой

echo "🧪 Ручное тестирование скрипта run_test_message.sh"
echo "=================================================="
echo ""

# Проверка наличия файла
if [ ! -f "run_test_message.sh" ]; then
    echo "❌ Файл run_test_message.sh не найден!"
    exit 1
fi

if [ ! -x "run_test_message.sh" ]; then
    echo "⚠️  Файл не исполняемый, делаем исполняемым..."
    chmod +x run_test_message.sh
fi

# Показать текущее время
echo "⏰ Время запуска: $(date)"
echo "📍 Директория: $(pwd)"
echo ""

# Проверить IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "🌐 Определенный IP: $SERVER_IP"

# Проверить доступность сервера
echo "🔗 Проверка доступности сервера..."
if curl -s --connect-timeout 5 "http://$SERVER_IP:5000/health" > /dev/null 2>&1; then
    echo "✅ Сервер доступен"
else
    echo "❌ Сервер недоступен - проверьте что Flask запущен"
    echo ""
    echo "💡 Для запуска Flask:"
    echo "   python main.py"
    echo "   или"
    echo "   gunicorn --bind 0.0.0.0:5000 main:app"
    exit 1
fi

echo ""
echo "🚀 Запуск run_test_message.sh..."
echo "Логи будут показаны в реальном времени:"
echo "----------------------------------------"

# Запуск с отображением логов в реальном времени
./run_test_message.sh

echo ""
echo "----------------------------------------"
echo "✅ Тест завершен!"
echo ""

# Показать последние записи из лога
if [ -f "/tmp/test_message_cron.log" ]; then
    echo "📝 Последние записи из лога cron:"
    tail -10 /tmp/test_message_cron.log
else
    echo "ℹ️  Лог файл /tmp/test_message_cron.log не найден"
fi

echo ""
echo "🏁 Ручной тест завершен: $(date)"