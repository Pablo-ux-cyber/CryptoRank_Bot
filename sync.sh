#!/bin/bash

# Скрипт для синхронизации Git репозитория на сервере
# Расположение: /root/coinbaserank_bot/sync.sh
# Использование: ssh your-server '/root/coinbaserank_bot/sync.sh'

# Переменные
APP_DIR="/root/coinbaserank_bot"
LOG_FILE="$APP_DIR/sync.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Выводим начальное сообщение
echo "=== Синхронизация репозитория Coinbase Rank Bot ==="
echo "[$TIMESTAMP] Запуск синхронизации"
echo "[$TIMESTAMP] Запуск синхронизации" >> $LOG_FILE

# Переходим в директорию приложения
cd $APP_DIR || { 
    echo "[$TIMESTAMP] ОШИБКА: Не удалось перейти в директорию $APP_DIR" | tee -a $LOG_FILE
    exit 1
}

# Сохраняем текущий статус приложения
if [ -d "$APP_DIR/.git" ]; then
    CURRENT_SHA=$(git rev-parse HEAD 2>/dev/null) || CURRENT_SHA="Неизвестно"
    echo "[$TIMESTAMP] Текущая версия: $CURRENT_SHA" | tee -a $LOG_FILE
else
    echo "[$TIMESTAMP] ПРЕДУПРЕЖДЕНИЕ: Git репозиторий не инициализирован" | tee -a $LOG_FILE
    echo "Инициализация Git репозитория..." | tee -a $LOG_FILE
    git init
    git remote add origin https://github.com/your-username/coinbasebot.git
fi

# Сохраняем локальные изменения
echo "[$TIMESTAMP] Сохранение локальных изменений..." | tee -a $LOG_FILE
git stash || echo "Нет изменений для сохранения или git не настроен"

# Получаем последнюю версию из репозитория
echo "[$TIMESTAMP] Получение изменений из репозитория..." | tee -a $LOG_FILE
git fetch origin || {
    echo "[$TIMESTAMP] ОШИБКА: Не удалось получить изменения из репозитория" | tee -a $LOG_FILE
    echo "Проверьте подключение к интернету и настройки git" | tee -a $LOG_FILE
    exit 1
}

# Обновляем код
echo "[$TIMESTAMP] Применение изменений..." | tee -a $LOG_FILE
git pull origin main || {
    echo "[$TIMESTAMP] ОШИБКА: Не удалось применить изменения" | tee -a $LOG_FILE
    echo "Возможно, есть конфликты или проблемы с репозиторием" | tee -a $LOG_FILE
    exit 1
}

# Возвращаем сохраненные локальные изменения
git stash pop 2>/dev/null || echo "Нет сохраненных изменений для применения" | tee -a $LOG_FILE

# Проверяем, изменилась ли версия
if [ -d "$APP_DIR/.git" ]; then
    NEW_SHA=$(git rev-parse HEAD 2>/dev/null) || NEW_SHA="Неизвестно"
    if [ "$CURRENT_SHA" != "$NEW_SHA" ]; then
        echo "[$TIMESTAMP] Код обновлен с $CURRENT_SHA до $NEW_SHA" | tee -a $LOG_FILE
        
        # Обновляем зависимости, если изменился файл requirements.txt
        if git diff --name-only $CURRENT_SHA $NEW_SHA | grep -q "requirements.txt"; then
            echo "[$TIMESTAMP] Обнаружены изменения в requirements.txt, обновляем зависимости..." | tee -a $LOG_FILE
            pip install -r requirements.txt || echo "[$TIMESTAMP] ОШИБКА: Не удалось обновить зависимости" | tee -a $LOG_FILE
        fi
        
        # Перезапускаем сервис
        echo "[$TIMESTAMP] Перезапуск сервиса coinbasebot..." | tee -a $LOG_FILE
        systemctl restart coinbasebot || {
            echo "[$TIMESTAMP] ОШИБКА: Не удалось перезапустить сервис" | tee -a $LOG_FILE
            exit 1
        }
        echo "[$TIMESTAMP] Сервис успешно перезапущен" | tee -a $LOG_FILE
    else
        echo "[$TIMESTAMP] Код уже актуален, обновление не требуется" | tee -a $LOG_FILE
    fi
fi

echo "[$TIMESTAMP] Синхронизация успешно завершена" | tee -a $LOG_FILE
echo "=== Синхронизация завершена ==="