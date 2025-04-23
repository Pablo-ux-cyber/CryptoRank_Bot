#!/bin/bash
# Простой скрипт синхронизации с исключением логов и JSON файлов

# Переходим в директорию проекта
cd /root/coinbaserank_bot

# Создаем .gitignore если его нет
if [ ! -f ".gitignore" ]; then
  echo "*.json" > .gitignore
  echo "*.log" >> .gitignore
  echo "rank_history.txt" >> .gitignore
  echo "coinbasebot.lock" >> .gitignore
fi

# Получаем обновления с GitHub
git pull origin main

# Перезапускаем сервис
sudo systemctl restart coinbasebot