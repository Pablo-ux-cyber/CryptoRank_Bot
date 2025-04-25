#!/bin/bash
# Скрипт для быстрого исправления проблем с файлами блокировки

# Определение директории скрипта
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "==== Проверка файлов блокировки ===="
echo "Текущее время: $(date)"
echo "Директория: $SCRIPT_DIR"
echo ""

# Проверка наличия файлов блокировки
if [ -f "$SCRIPT_DIR/manual_operation.lock" ]; then
    echo "Найден файл блокировки ручной операции:"
    ls -la "$SCRIPT_DIR/manual_operation.lock"
    echo "Время создания: $(stat -c %y "$SCRIPT_DIR/manual_operation.lock")"
    echo "Удаляем..."
    rm "$SCRIPT_DIR/manual_operation.lock"
    echo "Файл удален!"
else
    echo "Файл блокировки ручной операции не найден - это хорошо."
fi

echo ""

if [ -f "$SCRIPT_DIR/coinbasebot.lock" ]; then
    echo "Найден файл блокировки бота:"
    ls -la "$SCRIPT_DIR/coinbasebot.lock"
    echo "Время создания: $(stat -c %y "$SCRIPT_DIR/coinbasebot.lock")"
    
    # Проверяем возраст файла (старше 30 минут)
    FILE_AGE=$(( $(date +%s) - $(stat -c %Y "$SCRIPT_DIR/coinbasebot.lock") ))
    if [ $FILE_AGE -gt 1800 ]; then
        echo "Файл старше 30 минут ($FILE_AGE секунд). Удаляем..."
        rm "$SCRIPT_DIR/coinbasebot.lock"
        echo "Файл удален!"
    else
        echo "Файл свежий ($FILE_AGE секунд) - бот, вероятно, активен. Оставляем."
    fi
else
    echo "Файл блокировки бота не найден."
fi

echo ""
echo "==== Перезапуск бота (если настроен как сервис) ===="

# Проверяем, настроен ли сервис
if systemctl list-unit-files | grep -q coinbasebot; then
    echo "Сервис coinbasebot найден. Перезапускаем..."
    sudo systemctl restart coinbasebot
    echo "Статус сервиса:"
    sudo systemctl status coinbasebot | head -n 15
else
    echo "Сервис coinbasebot не найден в системе."
    echo "Возможно, бот запущен вручную или не настроен как systemd-сервис."
fi

echo ""
echo "==== Проверка выполнена! ===="
echo "Если вы хотите проверить работу бота, выполните:"
echo "./check_and_remove_locks.py"
echo ""
echo "Для принудительной отправки сообщения выполните:"
echo "source venv/bin/activate && python3 -c \"from scheduler import SensorTowerScheduler; scheduler = SensorTowerScheduler(); scheduler.start(); scheduler.run_now(force_send=True); scheduler.stop()\""