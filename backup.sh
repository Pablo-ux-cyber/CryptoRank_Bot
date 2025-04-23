#!/bin/bash

# Создание резервной копии всех данных Coinbase Rank Bot
# Запуск: ./backup.sh

BACKUP_DIR="/root/coinbaserank_bot_backup/$(date +%Y%m%d_%H%M%S)"
SOURCE_DIR="/root/coinbaserank_bot"

# Создаем директорию для бэкапа с текущей датой и временем
mkdir -p "$BACKUP_DIR"

echo "Starting backup to $BACKUP_DIR..."

# Копируем только исходные коды (игнорируя файлы из .gitignore)
echo "Backing up source code..."
rsync -av --exclude-from="$SOURCE_DIR/.gitignore" "$SOURCE_DIR"/ "$BACKUP_DIR"/

# Особое внимание к файлам с данными
echo "Backing up data files..."
for file in rank_history.json trends_history.json fear_greed_history.json rank_history.txt sensortower_bot.log google_trends_debug.log coinbasebot.lock; do
    if [ -f "$SOURCE_DIR/$file" ]; then
        cp "$SOURCE_DIR/$file" "$BACKUP_DIR/"
        echo "  - $file copied successfully"
    else
        echo "  - Warning: $file not found, skipping"
    fi
done

# Копируем скрытые файлы (не включенные в rsync)
if [ -f "$SOURCE_DIR/.env" ]; then
    cp "$SOURCE_DIR/.env" "$BACKUP_DIR/"
    echo "  - .env copied successfully"
fi

if [ -f "$SOURCE_DIR/.env.backup" ]; then
    cp "$SOURCE_DIR/.env.backup" "$BACKUP_DIR/"
    echo "  - .env.backup copied successfully"
fi

# Создаем архив
echo "Creating archive..."
tar -czvf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"

echo "Backup completed successfully!"
echo "Backup location: $BACKUP_DIR"
echo "Archive: $BACKUP_DIR.tar.gz"