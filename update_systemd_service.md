# ОБНОВЛЕНИЕ SYSTEMD СЕРВИСА

## Проблема
Systemd запускает `python main.py` что активирует блок `if __name__ == "__main__":` и создает планировщик.
Одновременно может работать gunicorn который тоже импортирует main.py.

## Решение
Создать отдельный файл `scheduler_standalone.py` и изменить systemd сервис.

## Команды для сервера:

### 1. Скопировать новый файл планировщика
```bash
# Скопируйте содержимое scheduler_standalone.py в /root/coinbaserank_bot/scheduler_standalone.py
```

### 2. Сделать файл исполняемым
```bash
chmod +x /root/coinbaserank_bot/scheduler_standalone.py
```

### 3. Остановить текущий сервис
```bash
sudo systemctl stop coinbasebot
```

### 4. Изменить systemd сервис
```bash
sudo nano /etc/systemd/system/coinbasebot.service
```

**Заменить содержимое на:**
```ini
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
```

### 5. Перезагрузить systemd и запустить сервис
```bash
sudo systemctl daemon-reload
sudo systemctl start coinbasebot
sudo systemctl status coinbasebot
```

### 6. Проверить логи
```bash
tail -f /root/coinbaserank_bot/sensortower_bot.log
```

## Ожидаемый результат
- ТОЛЬКО ОДИН планировщик
- БЕЗ ошибок "Другой экземпляр уже запущен"
- main.py остается только для веб-интерфейса Flask