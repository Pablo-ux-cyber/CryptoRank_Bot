# Настройка автоматического запуска Test Real Message

## Вариант 1: Запуск по прямой ссылке (GET запрос)

Теперь кнопку "Test Real Message" можно вызвать простым GET запросом:

```bash
# Прямой вызов через curl
curl http://localhost:5000/test-telegram-message

# Или через браузер
http://localhost:5000/test-telegram-message
```

## Вариант 2: Настройка cron для автоматического запуска

### Шаг 1: Сделать скрипт исполняемым
```bash
chmod +x run_test_message.sh
```

### Шаг 2: Открыть crontab для редактирования
```bash
crontab -e
```

### Шаг 3: Добавить задание в cron

#### Пример: каждый день в 08:01 UTC (11:01 MSK)
```bash
1 8 * * * /path/to/your/project/run_test_message.sh
```

#### Пример: каждый день в 15:30 MSK (12:30 UTC)
```bash
30 12 * * * /path/to/your/project/run_test_message.sh
```

#### Пример: каждые 10 минут (для тестирования)
```bash
*/10 * * * * /path/to/your/project/run_test_message.sh
```

#### Пример: только по рабочим дням в 09:00 MSK (06:00 UTC)
```bash
0 6 * * 1-5 /path/to/your/project/run_test_message.sh
```

### Шаг 4: Проверить статус cron
```bash
# Проверить запущен ли cron
sudo systemctl status cron

# Посмотреть логи cron
sudo journalctl -u cron

# Посмотреть логи нашего скрипта
tail -f /tmp/test_message_cron.log
```

## Вариант 3: Использование systemd timer

### Создать service файл
```bash
sudo nano /etc/systemd/system/test-message.service
```

Содержимое:
```ini
[Unit]
Description=Send Test Real Message
After=network.target

[Service]
Type=oneshot
ExecStart=/path/to/your/project/run_test_message.sh
User=your_username
```

### Создать timer файл
```bash
sudo nano /etc/systemd/system/test-message.timer
```

Содержимое:
```ini
[Unit]
Description=Run test message daily
Requires=test-message.service

[Timer]
OnCalendar=*-*-* 08:01:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Запустить timer
```bash
sudo systemctl daemon-reload
sudo systemctl enable test-message.timer
sudo systemctl start test-message.timer

# Проверить статус
sudo systemctl status test-message.timer
```

## Проверка и отладка

### Просмотр логов нашего скрипта
```bash
tail -f /tmp/test_message_cron.log
```

### Тестовый запуск скрипта
```bash
./run_test_message.sh
```

### Проверка работы через браузер
Откройте в браузере: `http://localhost:5000/test-telegram-message`

## Форматы времени для cron

```
# ┌───────────── минута (0 - 59)
# │ ┌───────────── час (0 - 23)
# │ │ ┌───────────── день месяца (1 - 31)
# │ │ │ ┌───────────── месяц (1 - 12)
# │ │ │ │ ┌───────────── день недели (0 - 6) (воскресенье=0)
# │ │ │ │ │
# * * * * * команда
```

Примеры:
- `0 8 * * *` - каждый день в 08:00
- `30 14 * * 1-5` - по рабочим дням в 14:30
- `0 */6 * * *` - каждые 6 часов
- `0 0 1 * *` - 1 числа каждого месяца в полночь