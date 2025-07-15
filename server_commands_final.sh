#!/bin/bash
# Финальные команды для исправления двойного планировщика на сервере

echo "=== ИСПРАВЛЕНИЕ ДВОЙНОГО ПЛАНИРОВЩИКА ==="

# Останавливаем сервис
echo "Остановка сервиса..."
sudo systemctl stop coinbasebot

# Удаляем файл блокировки  
echo "Удаление файла блокировки..."
sudo rm -f /root/coinbaserank_bot/coinbasebot.lock

# Создаем резервную копию main.py
echo "Создание резервной копии main.py..."
cp /root/coinbaserank_bot/main.py /root/coinbaserank_bot/main.py.backup_$(date +%Y%m%d_%H%M%S)

# Применяем исправления main.py
echo "Применение исправлений main.py..."
sed -i 's/# Initialize scheduler at startup - for both direct run and gunicorn/# ИСПРАВЛЕНО: НЕ запускаем планировщик автоматически из Flask приложения/' /root/coinbaserank_bot/main.py
sed -i 's/scheduler_thread = threading.Thread(target=start_scheduler_thread)/# Планировщик должен запускаться только из main.py файла когда приложение запущено напрямую/' /root/coinbaserank_bot/main.py
sed -i 's/scheduler_thread.daemon = True/# или из отдельного systemd сервиса/' /root/coinbaserank_bot/main.py
sed -i 's/scheduler_thread.start()/logger.info("Flask app initialized without starting scheduler - scheduler should be started externally")/' /root/coinbaserank_bot/main.py
sed -i 's/logger.info("Starting scheduler at app initialization")//' /root/coinbaserank_bot/main.py

# Запускаем сервис
echo "Запуск сервиса..."
sudo systemctl start coinbasebot

# Проверяем статус
echo "=== СТАТУС СЕРВИСА ==="
sudo systemctl status coinbasebot

echo ""
echo "=== ПОСЛЕДНИЕ ЛОГИ ==="
tail -20 /root/coinbaserank_bot/sensortower_bot.log

echo ""
echo "=== ГОТОВО ==="
echo "Планировщик должен запускаться только ОДИН раз без ошибок блокировки"