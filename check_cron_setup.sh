#!/bin/bash

# Проверка настройки cron и готовности скриптов

echo "🔍 Проверка настройки cron и скриптов..."
echo ""

# 1. Проверка файлов скриптов
echo "📂 Проверка файлов:"
files=("run_test_message.sh" "quick_test.sh" "smart_cron_test.sh")

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        if [ -x "$file" ]; then
            echo "✅ $file - существует и исполняемый"
        else
            echo "⚠️  $file - существует, но НЕ исполняемый (chmod +x $file)"
        fi
    else
        echo "❌ $file - НЕ НАЙДЕН"
    fi
done

echo ""

# 2. Проверка crontab
echo "📅 Проверка crontab:"
if crontab -l 2>/dev/null | grep -q "run_test_message.sh\|smart_cron_test.sh\|test-telegram-message"; then
    echo "✅ Найдены задания cron:"
    crontab -l 2>/dev/null | grep -E "run_test_message.sh|smart_cron_test.sh|test-telegram-message" | while read line; do
        echo "   📌 $line"
    done
else
    echo "⚠️  Задания cron НЕ НАЙДЕНЫ"
    echo "💡 Добавьте задание: crontab -e"
    echo "   Пример: 1 8 * * * $(pwd)/run_test_message.sh"
fi

echo ""

# 3. Тест определения IP
echo "🌐 Тест определения IP:"
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -n "$SERVER_IP" ]; then
    echo "✅ IP определился: $SERVER_IP"
    
    # Проверка доступности сервера
    if curl -s --connect-timeout 5 "http://$SERVER_IP:5000/health" > /dev/null 2>&1; then
        echo "✅ Сервер доступен на $SERVER_IP:5000"
    else
        echo "❌ Сервер НЕ доступен на $SERVER_IP:5000"
        echo "💡 Убедитесь что Flask приложение запущено"
    fi
else
    echo "❌ Не удалось определить IP"
fi

echo ""

# 4. Тест логирования
echo "📝 Проверка логов:"
log_files=("/tmp/test_message_cron.log" "/tmp/smart_cron_test.log")

for log_file in "${log_files[@]}"; do
    if [ -f "$log_file" ]; then
        echo "✅ $log_file существует"
        echo "   📄 Последние 3 строки:"
        tail -3 "$log_file" | sed 's/^/      /'
    else
        echo "ℹ️  $log_file пока не создан (будет создан при первом запуске)"
    fi
done

echo ""

# 5. Быстрый тест скрипта
echo "🧪 Быстрый тест скрипта:"
if [ -x "run_test_message.sh" ]; then
    echo "🚀 Запуск тестового вызова run_test_message.sh..."
    echo "   (Это может занять 1-2 минуты)"
    
    # Запускаем в фоне с таймаутом
    timeout 180 ./run_test_message.sh > /tmp/cron_check_test.log 2>&1 &
    test_pid=$!
    
    # Ждем несколько секунд
    sleep 5
    
    # Проверяем что процесс еще работает
    if kill -0 $test_pid 2>/dev/null; then
        echo "✅ Скрипт запустился и работает (PID: $test_pid)"
        echo "📊 Промежуточный лог:"
        head -10 /tmp/cron_check_test.log | sed 's/^/      /'
        
        # Убиваем тестовый процесс
        kill $test_pid 2>/dev/null
        wait $test_pid 2>/dev/null
        echo "   🛑 Тестовый процесс остановлен"
    else
        echo "❌ Скрипт завершился слишком быстро - возможна ошибка"
        echo "📊 Лог ошибки:"
        cat /tmp/cron_check_test.log | sed 's/^/      /'
    fi
else
    echo "❌ run_test_message.sh не исполняемый или не найден"
fi

echo ""

# 6. Рекомендации
echo "💡 Рекомендации:"
echo "   📌 Для добавления в cron: crontab -e"
echo "   📌 Пример ежедневного запуска: 1 8 * * * $(pwd)/run_test_message.sh"
echo "   📌 Для тестирования: ./quick_test.sh"
echo "   📌 Просмотр логов: tail -f /tmp/test_message_cron.log"
echo "   📌 Проверка cron логов: tail -f /var/log/cron (если доступно)"

echo ""
echo "🏁 Проверка завершена!"