# ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ SYSTEMD СЕРВИСА

## Проблема
SystemD сервис не загружает переменные окружения из .env файла. Нужно настроить сервис на загрузку .env.

## Решение 1: Обновить systemd сервис

```bash
# 1. Проверить текущий сервис файл
sudo systemctl cat coinbasebot

# 2. Отредактировать сервис файл
sudo nano /etc/systemd/system/coinbasebot.service
```

В файле сервиса должно быть:
```ini
[Unit]
Description=Coinbase Rank Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/coinbaserank_bot
Environment=PATH=/root/coinbaserank_bot/venv/bin
EnvironmentFile=/root/coinbaserank_bot/.env
ExecStart=/root/coinbaserank_bot/venv/bin/gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Ключевая строка:** `EnvironmentFile=/root/coinbaserank_bot/.env`

## Решение 2: Применить изменения

```bash
# 3. Перезагрузить конфигурацию
sudo systemctl daemon-reload

# 4. Перезапустить сервис
sudo systemctl restart coinbasebot

# 5. Проверить статус
sudo systemctl status coinbasebot
```

## Решение 3: Проверить результат

```bash
# Проверить что API ключ теперь найден
python3 server_api_limit_fix.py
```

Должно показать:
- ✅ "API ключ: 14fdb7e37c..." вместо "НЕ НАЙДЕН"
- ✅ 48-49/50 монет вместо 13/50
- ✅ Стабильный результат ~40.8%

## Альтернативное решение

Если не можете редактировать systemd файл, добавьте переменную напрямую в сервис:

```bash
sudo systemctl edit coinbasebot
```

Добавьте:
```ini
[Service]
Environment=CRYPTOCOMPARE_API_KEY=14fdb7e37c6c69e7d98d38b7dd58e0b7a4b4c5e1f0d9c0c9d7c5f4b3c2e4d8a9
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl restart coinbasebot
```

## Проверка переменных окружения

```bash
# Проверить какие переменные видит сервис
sudo systemctl show coinbasebot --property=Environment
```