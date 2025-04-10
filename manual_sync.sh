#!/bin/bash

# Скрипт для ручной синхронизации кода с Git репозиторием
# Сохраните как /home/user/coinbasebot/manual_sync.sh и сделайте исполняемым: chmod +x manual_sync.sh

# Задаем переменные
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="$APP_DIR/git_sync.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Переходим в директорию приложения
cd $APP_DIR

# Записываем информацию в лог
echo "[$TIMESTAMP] Запуск ручной синхронизации Git" >> $LOG_FILE

# Сохраняем текущий статус приложения
CURRENT_SHA=$(git rev-parse HEAD)
echo "[$TIMESTAMP] Текущая версия: $CURRENT_SHA" >> $LOG_FILE

# Получаем изменения из репозитория
echo "[$TIMESTAMP] Получение изменений из репозитория..." >> $LOG_FILE
git fetch origin

# Проверяем, есть ли изменения для получения
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ $LOCAL = $REMOTE ]; then
    echo "[$TIMESTAMP] Нет изменений, код актуален" >> $LOG_FILE
    echo "Код уже актуален, обновление не требуется"
else
    echo "[$TIMESTAMP] Обнаружены изменения, обновление кода..." >> $LOG_FILE
    
    # Сохраняем локальные изменения перед обновлением
    git stash
    
    # Обновляем код
    git pull origin main
    
    # Применяем локальные изменения обратно
    git stash pop
    
    # Перезапускаем сервис после обновления
    echo "[$TIMESTAMP] Перезапуск сервиса coinbasebot..." >> $LOG_FILE
    sudo systemctl restart coinbasebot
    
    # Записываем новую версию
    NEW_SHA=$(git rev-parse HEAD)
    echo "[$TIMESTAMP] Обновлено до версии: $NEW_SHA" >> $LOG_FILE
    echo "Код успешно обновлен до последней версии и сервис перезапущен"
fi

echo "[$TIMESTAMP] Синхронизация завершена" >> $LOG_FILE
echo "-----------------------------------" >> $LOG_FILE