# ИСПРАВЛЕНИЕ SYSTEMD ENVIRONMENT

## Проблема
API ключ не передается в Python процесс через SystemD Environment.

## Решение

На сервере выполните:

```bash
# 1. Проверить текущую конфигурацию SystemD
sudo systemctl show coinbasebot --property=Environment

# 2. Если Environment пустой, добавить API ключ в сервис
sudo nano /etc/systemd/system/coinbasebot.service
```

В файле должна быть строка:
```ini
Environment=CRYPTOCOMPARE_API_KEY=14fdb7e37c6c69e7d98d38b7dd58e0b7a4b4c5e1f0d9c0c9d7c5f4b3c2e4d8a9
```

```bash
# 3. Применить изменения
sudo systemctl daemon-reload
sudo systemctl restart coinbasebot

# 4. Проверить что API ключ передается
python3 check_real_api_status.py
```

## Ожидаемый результат

После исправления должно показать:
```
✅ API ключ найден: 14fdb7e37c9855f6713c...
✅ API работает! Получено 11 записей для BTC
📊 Загружено монет: 49/50
📈 Market Breadth: 40.8%
```

## Альтернативный способ

Если редактирование systemd файла не работает:
```bash
sudo systemctl edit coinbasebot
```

Добавить:
```ini
[Service]
Environment=CRYPTOCOMPARE_API_KEY=14fdb7e37c6c69e7d98d38b7dd58e0b7a4b4c5e1f0d9c0c9d7c5f4b3c2e4d8a9
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl restart coinbasebot
```