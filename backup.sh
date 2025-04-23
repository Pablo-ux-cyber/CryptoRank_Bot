#!/bin/bash
# Скрипт для создания резервной копии критических файлов

# Директория скрипта
DIR=$(dirname "$0")
cd "$DIR" || { echo "Error: Failed to change to script directory."; exit 1; }

# Timestamp для имени бэкапа
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_FILE="coinbaserank_bot_backup_$TIMESTAMP.tar.gz"

# Создаем список файлов для бэкапа
echo "Creating backup of critical configuration files..."
echo "Timestamp: $TIMESTAMP"

# Создаем временную директорию
TEMP_DIR=$(mktemp -d)
mkdir -p "$TEMP_DIR/files"

# Копируем важные файлы
echo "Copying configuration files..."
if [ -f "config.py" ]; then cp "config.py" "$TEMP_DIR/files/"; fi
if [ -f "rank_history.txt" ]; then cp "rank_history.txt" "$TEMP_DIR/files/"; fi
if [ -f "rank_history.json" ]; then cp "rank_history.json" "$TEMP_DIR/files/"; fi
if [ -f "fear_greed_history.json" ]; then cp "fear_greed_history.json" "$TEMP_DIR/files/"; fi
if [ -f "trends_history.json" ]; then cp "trends_history.json" "$TEMP_DIR/files/"; fi
if [ -f "sensortower_bot.log" ]; then cp "sensortower_bot.log" "$TEMP_DIR/files/"; fi
if [ -f "google_trends_debug.log" ]; then cp "google_trends_debug.log" "$TEMP_DIR/files/"; fi
if [ -f "requirements.txt" ]; then cp "requirements.txt" "$TEMP_DIR/files/"; fi

# Создаем информационный файл о системе
echo "Collecting system information..."
{
  echo "=== BACKUP INFO ==="
  echo "Date: $(date)"
  echo "Server: $(hostname)"
  echo ""
  echo "=== SYSTEM INFO ==="
  uname -a
  echo ""
  echo "=== SYSTEMD SERVICE STATUS ==="
  systemctl status coinbasebot || echo "Service not found"
  echo ""
  echo "=== PYTHON INFO ==="
  python3 --version || echo "Python not found"
  echo ""
  echo "=== BACKUP CONTENTS ==="
  ls -la "$TEMP_DIR/files/"
} > "$TEMP_DIR/backup_info.txt"

# Создаем архив
echo "Creating archive..."
tar -czf "$BACKUP_FILE" -C "$TEMP_DIR" files backup_info.txt

# Чистим временную директорию
rm -rf "$TEMP_DIR"

echo "Backup created: $BACKUP_FILE"
echo "Size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Опциональное копирование архива в безопасное место
# cp "$BACKUP_FILE" /path/to/backup/storage/

echo "Backup completed successfully."
exit 0