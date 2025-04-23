#!/bin/bash
# Простой скрипт синхронизации с обработкой конфликтов

# Переходим в директорию проекта
cd /root/coinbaserank_bot

# Сохраняем важный файл конфигурации
if [ -f "config.py" ]; then
  cp config.py config.py.bak
fi

# Создаем временный .gitignore для защиты данных
cat > .gitignore.tmp << EOL
*.json
*.log
rank_history.txt
coinbasebot.lock
manual_operation.lock
EOL

# Сначала отменяем все локальные изменения, кроме исключенных файлов
git reset --hard
git clean -f -d

# Перемещаем созданный .gitignore
mv .gitignore.tmp .gitignore

# Получаем обновления с GitHub
git pull origin main

# Восстанавливаем конфигурацию
if [ -f "config.py.bak" ]; then
  cp config.py.bak config.py
  rm config.py.bak
fi

# Устанавливаем права на исполнение скриптов
chmod +x *.sh

# Перезапускаем сервис
sudo systemctl restart coinbasebot

echo "Синхронизация успешно завершена!"