#!/bin/bash
# Исправление проблемы с файлом блокировки на сервере

echo "=== ИСПРАВЛЕНИЕ ФАЙЛА БЛОКИРОВКИ ==="
echo "Удаляем старый файл блокировки..."

# Останавливаем сервис
sudo systemctl stop coinbasebot

# Удаляем файл блокировки
sudo rm -f /root/coinbaserank_bot/coinbasebot.lock

# Запускаем сервис
sudo systemctl start coinbasebot

# Проверяем статус
echo "=== СТАТУС СЕРВИСА ==="
sudo systemctl status coinbasebot

echo ""
echo "=== ПОСЛЕДНИЕ ЛОГИ ==="
tail -20 /root/coinbaserank_bot/sensortower_bot.log

echo ""
echo "=== ГОТОВО ==="
echo "Планировщик должен работать без ошибок блокировки"