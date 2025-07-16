# Проверка и настройка systemd на сервере

## Проверка текущих настроек systemd

### 1. Найти существующие службы бота
```bash
# Поиск служб с названием содержащим coinbase или bot
sudo find /etc/systemd/system -name "*coinbase*" -o -name "*bot*"

# Альтернативный поиск
ls -la /etc/systemd/system/ | grep -i coinbase
ls -la /etc/systemd/system/ | grep -i bot
```

### 2. Проверить статус службы
```bash
# Если служба называется coinbasebot.service
sudo systemctl status coinbasebot

# Проверить все активные службы
systemctl list-units --type=service --state=active | grep -i coinbase
```

### 3. Посмотреть содержимое службы
```bash
# Если найдена служба, посмотреть её содержимое
sudo cat /etc/systemd/system/coinbasebot.service

# Или через systemctl
systemctl cat coinbasebot
```

## Изменение службы на main.py

### Создание новой службы или изменение существующей
```bash
# Создать/редактировать файл службы
sudo nano /etc/systemd/system/coinbasebot.service
```

### Содержимое файла службы для main.py:
```ini
[Unit]
Description=Coinbase Ranking Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/coinbaserank-bot
Environment=PATH=/root/coinbaserank-bot/venv/bin
ExecStart=/root/coinbaserank-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Содержимое для gunicorn (рекомендуется):
```ini
[Unit]
Description=Coinbase Ranking Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/coinbaserank-bot
Environment=PATH=/root/coinbaserank-bot/venv/bin
ExecStart=/root/coinbaserank-bot/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 1 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Применение изменений

### 1. Перезагрузить systemd
```bash
sudo systemctl daemon-reload
```

### 2. Остановить старую службу (если нужно)
```bash
sudo systemctl stop coinbasebot
```

### 3. Запустить службу
```bash
sudo systemctl start coinbasebot
```

### 4. Включить автозапуск
```bash
sudo systemctl enable coinbasebot
```

### 5. Проверить статус
```bash
sudo systemctl status coinbasebot
```

## Диагностика проблем

### Просмотр логов службы
```bash
# Последние логи
sudo journalctl -u coinbasebot -f

# Логи с определенного времени
sudo journalctl -u coinbasebot --since "1 hour ago"

# Все логи службы
sudo journalctl -u coinbasebot --no-pager
```

### Проверка процессов
```bash
# Найти процессы Python
ps aux | grep python

# Найти процессы на порту 5000
sudo netstat -tlnp | grep :5000
# или
sudo ss -tlnp | grep :5000
```

## Полезные команды systemd

```bash
# Перезапустить службу
sudo systemctl restart coinbasebot

# Остановить службу
sudo systemctl stop coinbasebot

# Отключить автозапуск
sudo systemctl disable coinbasebot

# Проверить зависимости
systemctl list-dependencies coinbasebot

# Проверить конфигурацию
systemctl show coinbasebot
```

## Пример проверочного скрипта

Создать файл `check_systemd.sh`:
```bash
#!/bin/bash
echo "=== Проверка systemd службы ==="
echo "1. Поиск служб бота:"
sudo find /etc/systemd/system -name "*coinbase*" -o -name "*bot*" 2>/dev/null

echo -e "\n2. Статус службы:"
sudo systemctl status coinbasebot 2>/dev/null || echo "Служба coinbasebot не найдена"

echo -e "\n3. Активные процессы Python:"
ps aux | grep python | grep -v grep

echo -e "\n4. Процессы на порту 5000:"
sudo netstat -tlnp 2>/dev/null | grep :5000 || sudo ss -tlnp | grep :5000

echo -e "\n5. Последние логи (если служба существует):"
sudo journalctl -u coinbasebot --lines=10 --no-pager 2>/dev/null || echo "Нет логов службы"
```

## Рекомендации

1. **Используйте gunicorn** для production - он более стабильный
2. **Всегда используйте виртуальное окружение** в ExecStart
3. **Указывайте полные пути** к Python и скриптам
4. **Настройте правильного пользователя** (обычно не root)
5. **Включите автозапуск** через systemctl enable