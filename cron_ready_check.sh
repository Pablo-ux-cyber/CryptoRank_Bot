#!/bin/bash

# Быстрая проверка готовности к настройке cron

echo "⚡ Быстрая проверка готовности cron"
echo "=================================="
echo ""

# Проверка основных требований
all_good=true

# 1. Скрипт существует и исполняемый
if [ -x "run_test_message.sh" ]; then
    echo "✅ run_test_message.sh готов"
else
    echo "❌ run_test_message.sh не готов"
    all_good=false
fi

# 2. Сервер доступен
SERVER_IP=$(hostname -I | awk '{print $1}')
if curl -s --connect-timeout 3 "http://$SERVER_IP:5000/health" > /dev/null 2>&1; then
    echo "✅ Сервер доступен ($SERVER_IP:5000)"
else
    echo "❌ Сервер недоступен"
    all_good=false
fi

# 3. Быстрый тест запуска (5 секунд)
echo ""
echo "🧪 Быстрый тест запуска (5 сек)..."

timeout 5 ./run_test_message.sh > /tmp/quick_cron_test.log 2>&1 &
test_pid=$!
sleep 2

if kill -0 $test_pid 2>/dev/null; then
    echo "✅ Скрипт запускается корректно"
    kill $test_pid 2>/dev/null
    wait $test_pid 2>/dev/null
else
    echo "❌ Проблема с запуском скрипта"
    all_good=false
fi

echo ""

# Результат
if $all_good; then
    echo "🎉 ВСЕ ГОТОВО ДЛЯ CRON!"
    echo ""
    echo "📋 Команды для настройки:"
    echo "   crontab -e"
    echo "   Добавить: 1 8 * * * $(pwd)/run_test_message.sh"
    echo ""
    echo "🔍 Проверка cron после настройки:"
    echo "   tail -f /tmp/test_message_cron.log"
else
    echo "⚠️  ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ"
    echo ""
    echo "💡 Попробуйте:"
    echo "   chmod +x run_test_message.sh"
    echo "   Убедитесь что Flask запущен"
fi

echo ""
echo "📍 Текущий путь для cron: $(pwd)/run_test_message.sh"