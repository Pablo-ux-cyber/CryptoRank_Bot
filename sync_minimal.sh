#!/bin/bash
# Универсальный скрипт синхронизации с сохранением всех локальных модификаций

cd /root/coinbaserank_bot

# Создаем директории для резервных копий, если они не существуют
mkdir -p ./backups
mkdir -p /tmp/git_sync_backups

# Создаем временный файл для списка модифицированных файлов
MODIFIED_FILES="/tmp/modified_files.txt"

# Получаем список всех модифицированных файлов
echo "Определяю локально модифицированные файлы..."
git status --porcelain | grep -E '^ M|^MM' | awk '{print $2}' > "$MODIFIED_FILES"

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
  echo "  Резервное копирование: $file"
  cp -f "$file" "./backups/$(basename "$file").backup"
  cp -f "$file" "/tmp/git_sync_backups/$(basename "$file").temp"
done < "$MODIFIED_FILES"

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
rm -f "$MODIFIED_FILES"

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

echo "Синхронизация успешно завершена!"