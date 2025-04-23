#!/bin/bash
# check_server.sh - Скрипт для проверки состояния сервера

TARGET_DIR=$(dirname "$0")
cd "$TARGET_DIR" || { echo "Error: Could not change to target directory."; exit 1; }

echo "======================================================="
echo "      ПРОВЕРКА СОСТОЯНИЯ COINBASE RANK BOT"
echo "======================================================="
echo ""

# Проверка службы systemd
echo "=== СОСТОЯНИЕ СЛУЖБЫ SYSTEMD ==="
systemctl status coinbasebot
echo ""

# Проверка процессов
echo "=== ЗАПУЩЕННЫЕ ПРОЦЕССЫ ==="
ps aux | grep "[p]ython.*main.py"
echo ""

# Проверка файлов блокировки
echo "=== ФАЙЛЫ БЛОКИРОВКИ ==="
if [ -f "$TARGET_DIR/coinbasebot.lock" ]; then
    echo "Файл блокировки coinbasebot.lock СУЩЕСТВУЕТ"
    echo "Содержимое файла:"
    cat "$TARGET_DIR/coinbasebot.lock"
else
    echo "Файл блокировки coinbasebot.lock ОТСУТСТВУЕТ"
fi
echo ""

if [ -f "$TARGET_DIR/manual_operation.lock" ]; then
    echo "Файл ручной блокировки manual_operation.lock СУЩЕСТВУЕТ"
else
    echo "Файл ручной блокировки manual_operation.lock ОТСУТСТВУЕТ"
fi
echo ""

# Проверка конфигурации
echo "=== КОНФИГУРАЦИЯ ==="
echo "TELEGRAM_BOT_TOKEN в config.py:"
grep -n "TELEGRAM_BOT_TOKEN" "$TARGET_DIR/config.py"
echo ""

echo "TELEGRAM_CHANNEL_ID в config.py:"
grep -n "TELEGRAM_CHANNEL_ID" "$TARGET_DIR/config.py"
echo ""

# Проверка логов
echo "=== ПОСЛЕДНИЕ ЗАПИСИ В ЛОГЕ ==="
if [ -f "$TARGET_DIR/sensortower_bot.log" ]; then
    tail -n 20 "$TARGET_DIR/sensortower_bot.log"
else
    echo "Файл лога не найден!"
fi
echo ""

# Проверка доступа к Telegram API
echo "=== ПРОВЕРКА ДОСТУПА К TELEGRAM API ==="
TOKEN=$(grep "TELEGRAM_BOT_TOKEN" "$TARGET_DIR/config.py" | grep -o '"[^"]*"' | tail -1 | tr -d '"')
if [ -n "$TOKEN" ]; then
    echo "Проверка токена: $TOKEN"
    RESULT=$(curl -s "https://api.telegram.org/bot$TOKEN/getMe")
    echo "Ответ API: $RESULT"
else
    echo "Токен не найден в config.py"
fi
echo ""

# Проверка веб-сервера
echo "=== ПРОВЕРКА ВЕБ-СЕРВЕРА ==="
if nc -z localhost 5000 2>/dev/null; then
    echo "Веб-сервер ДОСТУПЕН на порту 5000"
    HEALTH=$(curl -s http://localhost:5000/health)
    echo "Ответ /health: $HEALTH"
else
    echo "Веб-сервер НЕ ДОСТУПЕН на порту 5000"
fi
echo ""

# Справка по использованию скриптов восстановления
echo "=== ИНСТРУКЦИИ ПО ВОССТАНОВЛЕНИЮ ==="
echo "Если обнаружены проблемы, используйте следующие скрипты для восстановления:"
echo "1. Восстановление конфигурации: ./restore_config.sh"
echo "2. Восстановление виртуального окружения: ./setup_venv.sh"
echo "3. Перезапуск службы: systemctl restart coinbasebot"
echo "4. Полная диагностика: ./check_server.sh"
echo ""

echo "Для ручного запуска бота:"
echo "cd $TARGET_DIR && source venv/bin/activate && python main.py"
echo ""

echo "======================================================="
echo "      ПРОВЕРКА ЗАВЕРШЕНА"
echo "======================================================="