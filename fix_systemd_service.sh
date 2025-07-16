#!/bin/bash

# Скрипт для исправления systemd службы

echo "🔧 Исправление systemd службы"
echo "=============================="

echo "Вариант 1: Использовать gunicorn с main.py (рекомендуется)"
echo ""
cat << 'EOF'
[Unit]
Description=Coinbase Rank Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/coinbaserank_bot
ExecStart=/root/coinbaserank_bot/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 1 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "Вариант 2: Вернуться к scheduler_standalone.py"
echo ""
cat << 'EOF'
[Unit]
Description=Coinbase Rank Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/coinbaserank_bot
ExecStart=/root/coinbaserank_bot/venv/bin/python /root/coinbaserank_bot/scheduler_standalone.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "Команды для применения (выберите один вариант):"
echo ""
echo "Для gunicorn + main.py:"
echo "sudo systemctl stop coinbasebot"
echo "# Скопируйте Вариант 1 в /etc/systemd/system/coinbasebot.service"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl start coinbasebot"
echo ""
echo "Для возврата к scheduler_standalone.py:"
echo "sudo systemctl stop coinbasebot"
echo "# Скопируйте Вариант 2 в /etc/systemd/system/coinbasebot.service"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl start coinbasebot"