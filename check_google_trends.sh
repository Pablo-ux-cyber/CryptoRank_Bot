#!/bin/bash

# Скрипт для проверки работы Google Trends API на вашем сервере
# Запускает тестовый скрипт и создает лог для анализа

echo "=== Тестирование Google Trends API ==="
echo "Дата: $(date)"
echo

# Проверка активации виртуального окружения
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Активация виртуального окружения..."
    source venv/bin/activate
else
    echo "Виртуальное окружение активно: $VIRTUAL_ENV"
fi

# Создаем директорию для логов, если она не существует
mkdir -p logs

# Имя лог-файла с текущей датой
LOG_FILE="logs/google_trends_test_$(date +%Y%m%d_%H%M%S).log"

echo "Запуск теста с принудительным обновлением данных..."
echo "Результаты будут сохранены в файле: $LOG_FILE"

# Запуск теста с записью вывода в лог
python test_google_trends.py --force --repeat 1 | tee "$LOG_FILE"

echo
echo "=== Тестирование альтернативных периодов ==="
python test_period.py | tee -a "$LOG_FILE"

echo
echo "=== Тестирование завершено ==="
echo "Полные результаты доступны в файле: $LOG_FILE"

# Проверка наличия ключевых слов в логе
if grep -q "УСПЕХ" "$LOG_FILE"; then
    echo "✓ Найдены УСПЕШНЫЕ запросы к Google Trends API!"
    echo "Рекомендации:"
    echo "  1. Проверьте в логе, какие периоды работают"
    echo "  2. Обновите google_trends_pulse.py, если нужно"
else
    echo "✗ УСПЕШНЫЕ запросы не найдены."
    echo "Рекомендации:"
    echo "  1. Проверьте подключение к интернету"
    echo "  2. Попробуйте изменить период с 'now 14-d' на 'today 3-m' в google_trends_pulse.py"
    echo "  3. Увеличьте паузу между запросами до 10 секунд"
fi