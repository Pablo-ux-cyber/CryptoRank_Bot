#!/bin/bash
# Очень простой скрипт синхронизации

# Переходим в директорию проекта
cd /root/coinbaserank_bot

# Сохраняем локальные изменения
git stash

# Получаем обновления с GitHub
git pull origin main

# Восстанавливаем локальные изменения (для важных файлов конфига)
git stash pop

# Перезапускаем сервис
sudo systemctl restart coinbasebot