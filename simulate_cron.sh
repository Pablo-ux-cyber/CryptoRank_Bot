#!/bin/bash

# Симуляция cron окружения для тестирования

echo "⏱️  Симуляция cron окружения"
echo "============================"
echo ""

# Сохранить текущие переменные окружения
echo "💾 Сохранение текущего окружения..."
current_path="$PATH"
current_home="$HOME"
current_user="$USER"

# Симулировать ограниченное cron окружение
export PATH="/usr/bin:/bin"
export HOME="/tmp"
unset USER

echo "🔧 Установлено ограниченное cron окружение:"
echo "   PATH=$PATH"
echo "   HOME=$HOME"
echo "   USER=$USER"
echo ""

# Перейти в директорию скрипта
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

echo "📂 Рабочая директория: $script_dir"
echo ""

# Проверить что скрипт существует
if [ ! -f "run_test_message.sh" ]; then
    echo "❌ run_test_message.sh не найден в $script_dir"
    exit 1
fi

# Сделать исполняемым если нужно
if [ ! -x "run_test_message.sh" ]; then
    chmod +x run_test_message.sh
fi

echo "🚀 Запуск скрипта в cron-подобном окружении..."
echo "Время запуска: $(date)"
echo ""

# Запуск скрипта с перенаправлением вывода (как в cron)
echo "📝 Выполнение: ./run_test_message.sh > /tmp/cron_simulation.log 2>&1"
echo ""

./run_test_message.sh > /tmp/cron_simulation.log 2>&1
exit_code=$?

echo "📊 Результат выполнения:"
echo "   Exit code: $exit_code"

if [ $exit_code -eq 0 ]; then
    echo "   ✅ Успешно завершен"
else
    echo "   ❌ Завершен с ошибкой"
fi

echo ""
echo "📄 Вывод скрипта (последние 20 строк):"
echo "----------------------------------------"
if [ -f "/tmp/cron_simulation.log" ]; then
    tail -20 /tmp/cron_simulation.log
else
    echo "❌ Лог файл не создан"
fi

echo "----------------------------------------"
echo ""

# Восстановить переменные окружения
export PATH="$current_path"
export HOME="$current_home"
export USER="$current_user"

echo "💾 Окружение восстановлено"
echo ""

# Показать cron логи если есть
if [ -f "/tmp/test_message_cron.log" ]; then
    echo "📝 Последние записи из основного лога:"
    tail -10 /tmp/test_message_cron.log
fi

echo ""
echo "🏁 Симуляция cron завершена: $(date)"
echo ""

if [ $exit_code -eq 0 ]; then
    echo "✅ Скрипт готов для использования в cron!"
else
    echo "⚠️  Скрипт имеет проблемы - проверьте логи выше"
fi