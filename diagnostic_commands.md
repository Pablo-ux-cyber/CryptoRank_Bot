# ДИАГНОСТИКА ОТСУТСТВУЮЩЕГО СООБЩЕНИЯ

## Проверка логов планировщика

### 1. Основные логи
```bash
tail -50 /root/coinbaserank_bot/sensortower_bot.log
```

### 2. Логи за сегодня (16 июля)
```bash
grep "2025-07-16" /root/coinbaserank_bot/sensortower_bot.log
```

### 3. Поиск сообщений об отправке
```bash
grep -i "отправка\|sending\|telegram\|message" /root/coinbaserank_bot/sensortower_bot.log | tail -20
```

### 4. Поиск ошибок за последние 24 часа
```bash
grep -E "(ERROR|Exception|Failed)" /root/coinbaserank_bot/sensortower_bot.log | tail -20
```

### 5. Статус systemd сервиса
```bash
sudo systemctl status coinbasebot
```

### 6. Проверка времени на сервере
```bash
date
timedatectl status
```

### 7. Проверка работы планировщика
```bash
ps aux | grep python
```

## Ожидаемое в логах:
- Запись о запуске в 08:01:00 UTC (11:01 MSK)
- Сбор данных (рейтинг, Fear & Greed, и т.д.)
- Отправка сообщения в Telegram
- Запись об успешной отправке