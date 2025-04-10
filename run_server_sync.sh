#!/bin/bash

# Скрипт для запуска синхронизации на сервере из Replit
# Использование: ./run_server_sync.sh [server_ip]

# Получаем IP-адрес сервера из аргумента командной строки или используем значение по умолчанию
SERVER_IP=${1:-"your-server-ip"}

# Проверяем наличие переменной окружения SERVER_IP в Replit (если сценарий запускается из Replit)
if [ -z "$1" ] && [ ! -z "$SERVER_IP" ]; then
    echo "Используется IP-адрес сервера из переменной окружения Replit: $SERVER_IP"
else
    echo "Используется IP-адрес сервера: $SERVER_IP"
fi

echo "Запуск синхронизации на сервере..."
ssh root@$SERVER_IP "/root/coinbaserank_bot/sync.sh"

# Проверяем статус выполнения
if [ $? -eq 0 ]; then
    echo "Синхронизация успешно завершена!"
else
    echo "Произошла ошибка при синхронизации."
    echo "Проверьте журнал синхронизации на сервере:"
    echo "ssh root@$SERVER_IP \"cat /root/coinbaserank_bot/sync.log | tail -n 30\""
fi