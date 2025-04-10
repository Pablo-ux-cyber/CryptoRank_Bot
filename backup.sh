#!/bin/bash
# backup.sh - Скрипт для создания резервной копии данных и настроек бота

# Определяем директории и файлы
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BOT_DIR="$SCRIPT_DIR"
BACKUP_DIR="$BOT_DIR/backups"
DATE_STAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/coinbasebot_backup_$DATE_STAMP.tar.gz"

# Создаем директорию для резервных копий, если она не существует
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting backup process..."
echo "📂 Bot directory: $BOT_DIR"
echo "💾 Backup will be saved to: $BACKUP_FILE"

# Создаем список файлов для бэкапа
BACKUP_FILES=(
    "main.py"
    "config.py"
    "scraper.py"
    "telegram_bot.py"
    "fear_greed_index.py"
    "google_trends_pulse.py"
    "scheduler.py"
    "logger.py"
    ".env"
    "templates/"
    "/tmp/coinbasebot_rank_history.txt"
)

# Создаем временную директорию для организации файлов
TEMP_DIR=$(mktemp -d)
TEMP_BOT_DIR="$TEMP_DIR/coinbasebot"
mkdir -p "$TEMP_BOT_DIR"
mkdir -p "$TEMP_BOT_DIR/tmp"

# Копируем файлы во временную директорию
for file in "${BACKUP_FILES[@]}"; do
    # Обрабатываем специальные пути
    if [[ "$file" == "/tmp/"* ]]; then
        # Для файлов из /tmp/, копируем их в специальную tmp директорию
        filename=$(basename "$file")
        if [ -f "$file" ]; then
            cp "$file" "$TEMP_BOT_DIR/tmp/$filename"
            echo "✅ Copied $file to backup"
        else
            echo "⚠️ Warning: $file not found, skipping"
        fi
    else
        # Для обычных файлов и директорий
        if [ -f "$BOT_DIR/$file" ] || [ -d "$BOT_DIR/$file" ]; then
            cp -r "$BOT_DIR/$file" "$TEMP_BOT_DIR/"
            echo "✅ Copied $file to backup"
        else
            echo "⚠️ Warning: $BOT_DIR/$file not found, skipping"
        fi
    fi
done

# Создаем архив
tar -czf "$BACKUP_FILE" -C "$TEMP_DIR" coinbasebot
echo "✅ Created backup archive: $BACKUP_FILE"

# Удаляем временную директорию
rm -rf "$TEMP_DIR"
echo "🧹 Cleaned up temporary files"

# Выводим сообщение о успешном завершении
echo "✅ Backup completed successfully!"
echo "📦 Backup saved to: $BACKUP_FILE"

# Выводим информацию о восстановлении
echo
echo "📋 To restore this backup, run:"
echo "mkdir -p restore_temp && tar -xzf $BACKUP_FILE -C restore_temp && cp -r restore_temp/coinbasebot/* /path/to/restore/location/ && rm -rf restore_temp"
echo

# Удаляем старые резервные копии (оставляем последние 5)
echo "🧹 Cleaning up old backups (keeping the latest 5)..."
ls -t "$BACKUP_DIR"/coinbasebot_backup_*.tar.gz | tail -n +6 | xargs -r rm
echo "✅ Cleanup completed"