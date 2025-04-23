#!/bin/bash
# Универсальный скрипт синхронизации с сохранением всех локальных модификаций
# и защитой от удаления важных файлов/папок

cd /root/coinbaserank_bot

# Ключевые файлы и директории, которые должны быть сохранены
CRITICAL_FILES=(
  "config.py"
  "main.py"
  "models.py"
  "telegram_bot.py"
  "google_trends_pulse.py"
  "fear_greed_index.py"
  "scheduler.py"
  "scraper.py"
  "history_api.py"
  "logger.py"
  "trends_history.json"
  "rank_history.json"
  "fear_greed_history.json"
)

CRITICAL_DIRS=(
  "templates"
  "static"
  "routes"
  "backups"
)

# Создаем директории для резервных копий, если они не существуют
mkdir -p ./backups
mkdir -p /tmp/git_sync_backups

# Создаем временный файл для списка модифицированных файлов
MODIFIED_FILES="/tmp/modified_files.txt"
DELETED_FILES="/tmp/deleted_files.txt"

# Получаем список всех модифицированных файлов
echo "Определяю локально модифицированные файлы..."
git status --porcelain | grep -E '^ M|^MM' | awk '{print $2}' > "$MODIFIED_FILES"

# Получаем список файлов, которые будут удалены при pull
echo "Проверка файлов, которые могут быть удалены при синхронизации..."
git fetch origin main
git diff --name-status origin/main..HEAD | grep "^D" | awk '{print $2}' > "$DELETED_FILES"

# Проверка на удаление критических файлов
if [[ -s "$DELETED_FILES" ]]; then
  CRITICAL_DELETE=0
  while IFS= read -r file; do
    for critical in "${CRITICAL_FILES[@]}"; do
      if [[ "$file" == "$critical" ]]; then
        echo "⚠️ ВНИМАНИЕ: Критический файл будет удалён при синхронизации: $file"
        CRITICAL_DELETE=1
      fi
    done
    
    for dir in "${CRITICAL_DIRS[@]}"; do
      if [[ "$file" == "$dir"/* ]]; then
        echo "⚠️ ВНИМАНИЕ: Файл из критической директории будет удалён: $file"
        CRITICAL_DELETE=1
      fi
    done
  done < "$DELETED_FILES"
  
  if [[ $CRITICAL_DELETE -eq 1 ]]; then
    echo "⛔ Обнаружена попытка удаления критических файлов!"
    echo "Выполняю резервное копирование всех критических файлов..."
    
    # Создаем дополнительную резервную копию с временной меткой
    BACKUP_DIR="./backups/full_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Копируем все критические файлы
    for file in "${CRITICAL_FILES[@]}"; do
      if [[ -f "$file" ]]; then
        cp -f "$file" "$BACKUP_DIR/$(basename "$file")"
        echo "  Сохранён: $file"
      fi
    done
    
    # Копируем все критические директории
    for dir in "${CRITICAL_DIRS[@]}"; do
      if [[ -d "$dir" ]]; then
        mkdir -p "$BACKUP_DIR/$dir"
        cp -rf "$dir"/* "$BACKUP_DIR/$dir/" 2>/dev/null || true
        echo "  Сохранена директория: $dir"
      fi
    done
    
    echo "Полная резервная копия сохранена в: $BACKUP_DIR"
  fi
fi

# Создаем список *.json файлов, которые могут содержать данные
DATA_FILES=(
  "trends_history.json"
  "rank_history.json" 
  "fear_greed_history.json"
  "*.json"
)

# Сохраняем все модифицированные файлы
echo "Создаю резервные копии модифицированных файлов..."
while IFS= read -r file; do
  if [[ -f "$file" ]]; then
    echo "  Резервное копирование: $file"
    cp -f "$file" "./backups/$(basename "$file").backup"
    cp -f "$file" "/tmp/git_sync_backups/$(basename "$file").temp"
  fi
done < "$MODIFIED_FILES"

# Делаем резервные копии критических файлов независимо от их статуса
echo "Создаю резервные копии критических файлов..."
for critical in "${CRITICAL_FILES[@]}"; do
  if [[ -f "$critical" ]]; then
    echo "  Резервное копирование критического файла: $critical"
    cp -f "$critical" "./backups/$(basename "$critical").critical"
    cp -f "$critical" "/tmp/git_sync_backups/$(basename "$critical").critical"
  fi
done

# Делаем резервные копии файлов данных независимо от их статуса в git
echo "Создаю резервные копии файлов данных..."
for data_file in "${DATA_FILES[@]}"; do
  if [[ "$data_file" == *"*"* ]]; then  # Если есть шаблон с '*'
    for f in $data_file; do
      if [[ -f "$f" ]]; then
        echo "  Резервное копирование данных: $f"
        cp -f "$f" "/tmp/git_sync_backups/$(basename "$f").temp"
      fi
    done
  elif [[ -f "$data_file" ]]; then
    echo "  Резервное копирование данных: $data_file"
    cp -f "$data_file" "/tmp/git_sync_backups/$(basename "$data_file").temp"
  fi
done

# Проверяем, есть ли модифицированные файлы
if [[ -s "$MODIFIED_FILES" ]]; then
  # Сбрасываем локальные изменения перед синхронизацией
  echo "Временно сбрасываю локальные изменения для синхронизации..."
  git stash save "Временное сохранение перед sync_minimal $(date)"
  STASHED=1
else
  STASHED=0
fi

# Синхронизируемся с удаленным репозиторием
echo "Синхронизация с удаленным репозиторием..."
git pull origin main

# Проверяем, что критические файлы и директории всё ещё существуют
RESTORED_FILES=0
for critical in "${CRITICAL_FILES[@]}"; do
  if [[ ! -f "$critical" && -f "/tmp/git_sync_backups/$(basename "$critical").critical" ]]; then
    echo "⚠️ Критический файл удалён, восстанавливаю: $critical"
    cp -f "/tmp/git_sync_backups/$(basename "$critical").critical" "$critical"
    RESTORED_FILES=1
  fi
done

for dir in "${CRITICAL_DIRS[@]}"; do
  if [[ ! -d "$dir" ]]; then
    echo "⚠️ Критическая директория удалена, создаю: $dir"
    mkdir -p "$dir"
    RESTORED_FILES=1
  fi
done

if [[ $RESTORED_FILES -eq 1 ]]; then
  echo "✅ Критические файлы и директории восстановлены после синхронизации"
fi

# Восстанавливаем модифицированные файлы
echo "Восстанавливаю модифицированные файлы..."
while IFS= read -r file; do
  if [[ -f "/tmp/git_sync_backups/$(basename "$file").temp" ]]; then
    echo "  Восстановление: $file"
    cp -f "/tmp/git_sync_backups/$(basename "$file").temp" "$file"
  fi
done < "$MODIFIED_FILES"

# Восстанавливаем файлы данных
echo "Восстанавливаю файлы данных..."
for data_file in "${DATA_FILES[@]}"; do
  if [[ "$data_file" == *"*"* ]]; then  # Если есть шаблон с '*'
    for f in /tmp/git_sync_backups/*.temp; do
      if [[ -f "$f" ]]; then
        base_name=$(basename "$f" .temp)
        if [[ -f "$base_name" ]]; then
          echo "  Восстановление данных: $base_name"
          cp -f "$f" "$base_name"
        fi
      fi
    done
  elif [[ -f "/tmp/git_sync_backups/$(basename "$data_file").temp" ]]; then
    echo "  Восстановление данных: $data_file"
    cp -f "/tmp/git_sync_backups/$(basename "$data_file").temp" "$data_file"
  fi
done

# Убираем временные файлы
echo "Очистка временных файлов..."
rm -f /tmp/git_sync_backups/*.temp
rm -f /tmp/git_sync_backups/*.critical
rm -f "$MODIFIED_FILES"
rm -f "$DELETED_FILES"

# Обновляем .gitignore для всех файлов данных
echo "Проверка .gitignore..."
for data_file in "${DATA_FILES[@]}"; do
  if [[ "$data_file" != *"*"* ]]; then
    if ! grep -q "$data_file" .gitignore; then
      echo "$data_file" >> .gitignore
      echo "Добавлен $data_file в .gitignore"
    fi
  fi
done

# Перезапускаем сервис
echo "Перезапуск сервиса..."
systemctl restart coinbasebot

echo "✅ Синхронизация успешно завершена!"
echo "📋 Все критические файлы и данные сохранены"