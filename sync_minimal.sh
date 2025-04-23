#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=/root/coinbaserank_bot
SERVICE_NAME=coinbasebot

cd "$REPO_DIR"

# 1) Сохраняем локальные JSON-файлы во временную папку
TMP_DIR=$(mktemp -d)
echo "📦 Перенос JSON-файлов в $TMP_DIR …"
for f in *.json; do
  [[ -e "$f" ]] || continue
  mv -- "$f" "$TMP_DIR/"
done

# 2) Запоминаем текущий коммит
OLD_HEAD=$(git rev-parse HEAD)

# 3) Подтягиваем и жёстко сбрасываемся к origin/main
echo "⬇️  Синхронизация кода с origin/main …"
git fetch origin main
git reset --hard origin/main

# 4) Показываем, какие файлы изменились между $OLD_HEAD и новым HEAD
echo "📄 Обновленные файлы:"
git diff --name-status "$OLD_HEAD" HEAD || true

# 5) Восстанавливаем JSON обратно
echo "🔄 Восстановление JSON-файлов …"
for f in "$TMP_DIR"/*.json; do
  [[ -e "$f" ]] || continue
  mv -- "$f" "$REPO_DIR/$(basename "$f")"
done
rm -rf "$TMP_DIR"

# 6) Перезапускаем сервис
echo "🔁 Перезапуск сервиса $SERVICE_NAME …"
systemctl restart "$SERVICE_NAME"

echo "✅ Синхронизация завершена, JSON сохранены."
