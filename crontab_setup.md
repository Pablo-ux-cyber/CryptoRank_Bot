# Настройка автозапуска для VPS

## Для systemd систем (Ubuntu/CentOS/etc):

1. Создать файл сервиса:
```bash
sudo nano /etc/systemd/system/coinbasebot.service
```

2. Содержимое файла:
```ini
[Unit]
Description=Coinbase Rank Telegram Bot
After=network.target

[Service]
Type=simple
User=runner
Group=runner
WorkingDirectory=/home/runner/workspace
Environment=PATH=/home/runner/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=coinbasebot

[Install]
WantedBy=multi-user.target
```

3. Активировать:
```bash
sudo systemctl daemon-reload
sudo systemctl enable coinbasebot.service
sudo systemctl start coinbasebot.service
```

## Для cron (если systemd недоступен):

```bash
# Добавить в crontab:
# Проверка и перезапуск каждые 5 минут
*/5 * * * * /home/runner/workspace/monitor_bot.sh >> /home/runner/workspace/monitor.log 2>&1

# Принудительный перезапуск раз в день в 05:00 UTC (08:00 MSK)
0 5 * * * /home/runner/workspace/start_bot.sh >> /home/runner/workspace/startup.log 2>&1
```

## Ручной запуск (аварийный):
```bash
cd /home/runner/workspace
./start_bot.sh
```

## Мониторинг:
```bash
# Проверить работает ли бот
ps aux | grep python | grep main

# Проверить логи
tail -f sensortower_bot.log
```