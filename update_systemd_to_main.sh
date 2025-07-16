#!/bin/bash

# Скрипт для изменения systemd службы на main.py

echo "🔧 Изменение systemd службы на main.py"
echo "======================================"

# Остановить службу
echo "1. Остановка текущей службы..."
sudo systemctl stop coinbasebot

# Создать новый файл службы
echo "2. Создание нового файла службы..."
sudo tee /etc/systemd/system/coinbasebot.service > /dev/null << 'EOF'
[Unit]
Description=Coinbase Rank Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/coinbaserank_bot
ExecStart=/root/coinbaserank_bot/venv/bin/python /root/coinbaserank_bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "3. Перезагрузка systemd..."
sudo systemctl daemon-reload

echo "4. Запуск службы..."
sudo systemctl start coinbasebot

echo "5. Включение автозапуска..."
sudo systemctl enable coinbasebot

echo ""
echo "✅ Служба обновлена!"
echo ""
echo "Проверка статуса:"
sudo systemctl status coinbasebot

echo ""
echo "Для просмотра логов:"
echo "sudo journalctl -u coinbasebot -f"