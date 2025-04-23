#!/bin/bash
# Улучшенный скрипт синхронизации с сохранением локальных модификаций

cd /root/coinbaserank_bot

# Создаем директорию для резервных копий, если она не существует
mkdir -p ./backups

# Сохраняем локальные модификации перед синхронизацией
echo "Создаю резервные копии локальных файлов..."
cp -f google_trends_pulse.py ./backups/google_trends_pulse.py.backup
cp -f trends_history.json ./backups/trends_history.json.backup
cp -f rank_history.json ./backups/rank_history.json.backup
cp -f fear_greed_history.json ./backups/fear_greed_history.json.backup

# Временно копируем JSON файлы в безопасное место
cp -f trends_history.json /tmp/trends_history.json.temp
cp -f rank_history.json /tmp/rank_history.json.temp
cp -f fear_greed_history.json /tmp/fear_greed_history.json.temp

# Стираем локальные изменения в отслеживаемых файлах перед синхронизацией
git checkout -- google_trends_pulse.py || true

# Синхронизируемся с удаленным репозиторием
echo "Синхронизация с удаленным репозиторием..."
git pull origin main

# Восстанавливаем наши модификации из резервной копии
echo "Восстанавливаю локальные модификации..."
cp -f ./backups/google_trends_pulse.py.backup google_trends_pulse.py

# Восстанавливаем данные JSON из временного хранилища
cp -f /tmp/trends_history.json.temp trends_history.json
cp -f /tmp/rank_history.json.temp rank_history.json
cp -f /tmp/fear_greed_history.json.temp fear_greed_history.json

# Убираем временные файлы
rm -f /tmp/trends_history.json.temp
rm -f /tmp/rank_history.json.temp
rm -f /tmp/fear_greed_history.json.temp

# Обновляем .gitignore, если нужно
if ! grep -q "trends_history.json" .gitignore; then
    echo "trends_history.json" >> .gitignore
    echo "Добавлен trends_history.json в .gitignore"
fi

if ! grep -q "rank_history.json" .gitignore; then
    echo "rank_history.json" >> .gitignore
    echo "Добавлен rank_history.json в .gitignore"
fi

if ! grep -q "fear_greed_history.json" .gitignore; then
    echo "fear_greed_history.json" >> .gitignore
    echo "Добавлен fear_greed_history.json в .gitignore"
fi

# Перезапускаем сервис
echo "Перезапуск сервиса..."
systemctl restart coinbasebot

echo "Синхронизация успешно завершена!"