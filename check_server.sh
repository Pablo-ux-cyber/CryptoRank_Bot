#!/bin/bash
# Скрипт для проверки состояния сервера и бота
# Выводит отчет о текущем состоянии системы, компонентов и сервисов

# Директория проекта
PROJECT_DIR="/root/coinbaserank_bot"
SERVICE_NAME="coinbasebot"

echo "============================================================"
echo "      CoinbaseRank Bot - Отчет о состоянии системы"
echo "============================================================"
echo "Дата и время: $(date)"
echo "Хост: $(hostname)"
echo "Пользователь: $(whoami)"
echo "============================================================"

# Проверка основных компонентов системы
echo -e "\n--- Проверка системных ресурсов ---"
echo "CPU использование:"
top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}' | awk '{print $1"%"}'

echo -e "\nПамять:"
free -h | grep "Mem" | awk '{print "Всего: " $2 ", Использовано: " $3 ", Свободно: " $4}'

echo -e "\nДисковое пространство:"
df -h / | tail -n 1 | awk '{print "Всего: " $2 ", Использовано: " $3 " (" $5 "), Свободно: " $4}'

echo -e "\n--- Проверка сервисов ---"
echo "Статус службы $SERVICE_NAME:"
systemctl status "$SERVICE_NAME" | grep -E "Active:|●" | head -n 1

echo -e "\n--- Проверка виртуального окружения ---"
if [ -d "$PROJECT_DIR/venv" ] && [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    echo "Виртуальное окружение: СУЩЕСТВУЕТ"
    echo "Путь: $PROJECT_DIR/venv"
    echo "Python версия:"
    $PROJECT_DIR/venv/bin/python3 --version
    
    echo -e "\nУстановленные пакеты:"
    $PROJECT_DIR/venv/bin/pip freeze | wc -l | awk '{print "Всего пакетов: " $1}'
    
    # Проверка наличия критически важных пакетов
    CRITICAL_PACKAGES=("flask" "flask-sqlalchemy" "apscheduler" "trafilatura" "pytrends" "pandas" "python-telegram-bot" "gunicorn")
    for package in "${CRITICAL_PACKAGES[@]}"; do
        if $PROJECT_DIR/venv/bin/pip freeze | grep -i "$package" > /dev/null; then
            echo "✓ $package: УСТАНОВЛЕН"
        else
            echo "✗ $package: НЕ НАЙДЕН!"
        fi
    done
else
    echo "❌ Виртуальное окружение: НЕ НАЙДЕНО"
    echo "Требуется восстановление. Выполните ./setup_venv.sh"
fi

echo -e "\n--- Проверка конфигурационных файлов ---"
# Проверка наличия критически важных файлов
if [ -f "$PROJECT_DIR/config.py" ]; then
    echo "✓ config.py: СУЩЕСТВУЕТ"
    # Проверяем, содержит ли файл токен
    if grep -q "TELEGRAM_BOT_TOKEN" "$PROJECT_DIR/config.py"; then
        TOKEN_VALUE=$(grep "TELEGRAM_BOT_TOKEN" "$PROJECT_DIR/config.py" | grep -o '"[^"]*"' | head -1)
        if [ "$TOKEN_VALUE" = '"YOUR_BOT_TOKEN_HERE"' ] || [ -z "$TOKEN_VALUE" ]; then
            echo "  ❌ ВНИМАНИЕ: Токен не установлен или использует значение по умолчанию!"
        else
            echo "  ✓ Токен установлен"
        fi
    else
        echo "  ❌ ВНИМАНИЕ: Не найден параметр TELEGRAM_BOT_TOKEN!"
    fi
else
    echo "❌ config.py: НЕ НАЙДЕН!"
    echo "  Требуется восстановление. Выполните ./restore_config.sh"
fi

if [ -f "$PROJECT_DIR/.env" ]; then
    echo "✓ .env: СУЩЕСТВУЕТ"
    # Проверяем, содержит ли файл токен
    if grep -q "TELEGRAM_BOT_TOKEN" "$PROJECT_DIR/.env"; then
        TOKEN_VALUE=$(grep "TELEGRAM_BOT_TOKEN" "$PROJECT_DIR/.env" | cut -d "=" -f2)
        if [ "$TOKEN_VALUE" = "YOUR_BOT_TOKEN_HERE" ] || [ -z "$TOKEN_VALUE" ]; then
            echo "  ❌ ВНИМАНИЕ: Токен не установлен или использует значение по умолчанию!"
        else
            echo "  ✓ Токен установлен"
        fi
    else
        echo "  ❌ ВНИМАНИЕ: Не найден параметр TELEGRAM_BOT_TOKEN!"
    fi
else
    echo "❌ .env: НЕ НАЙДЕН!"
    echo "  Требуется восстановление. Выполните ./restore_config.sh"
fi

echo -e "\n--- Проверка файлов истории ---"
for history_file in "$PROJECT_DIR/rank_history.json" "$PROJECT_DIR/trends_history.json" "$PROJECT_DIR/fear_greed_history.json" "$PROJECT_DIR/rank_history.txt"; do
    if [ -f "$history_file" ]; then
        file_size=$(du -h "$history_file" | cut -f1)
        records=$(wc -l "$history_file" | cut -d' ' -f1)
        echo "✓ $(basename "$history_file"): СУЩЕСТВУЕТ (размер: $file_size, записей: $records)"
    else
        echo "❌ $(basename "$history_file"): НЕ НАЙДЕН!"
    fi
done

echo -e "\n--- Проверка логов ---"
for log_file in "$PROJECT_DIR/sensortower_bot.log" "$PROJECT_DIR/google_trends_debug.log"; do
    if [ -f "$log_file" ]; then
        file_size=$(du -h "$log_file" | cut -f1)
        last_modified=$(stat -c "%y" "$log_file" | cut -d. -f1)
        echo "✓ $(basename "$log_file"): СУЩЕСТВУЕТ (размер: $file_size, последнее изменение: $last_modified)"
        echo "  Последние ошибки в логе (если есть):"
        tail -n 100 "$log_file" | grep -i "error\|exception\|fail" | tail -n 5
    else
        echo "❌ $(basename "$log_file"): НЕ НАЙДЕН!"
    fi
done

echo -e "\n--- Проверка подключения к Telegram ---"
if [ -f "$PROJECT_DIR/venv/bin/python3" ] && [ -f "$PROJECT_DIR/telegram_bot.py" ]; then
    echo "Проверка возможности подключения к API Telegram..."
    $PROJECT_DIR/venv/bin/python3 -c "
import os, sys
sys.path.append('$PROJECT_DIR')
import config
from telegram import Bot
from telegram.error import TelegramError

try:
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    bot_info = bot.get_me()
    print(f'✓ Успешное подключение к Telegram API как {bot_info.first_name} (@{bot_info.username})')
except TelegramError as e:
    print(f'❌ Ошибка подключения к Telegram API: {e}')
except Exception as e:
    print(f'❌ Неизвестная ошибка: {e}')
"
else
    echo "❌ Невозможно выполнить проверку подключения к Telegram API (отсутствует Python или telegram_bot.py)"
fi

echo -e "\n============================================================"
echo "Рекомендации:"
echo "- Если обнаружены проблемы с виртуальным окружением, выполните: ./setup_venv.sh"
echo "- Если отсутствуют конфигурационные файлы, выполните: ./restore_config.sh"
echo "- Для перезапуска сервиса, выполните: sudo systemctl restart $SERVICE_NAME"
echo "- Для просмотра логов в реальном времени: tail -f $PROJECT_DIR/sensortower_bot.log"
echo "============================================================"