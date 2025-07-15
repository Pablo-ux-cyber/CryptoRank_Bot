# Команды для диагностики проблемы с планировщиком

## 1. Проверка состояния systemd сервиса
```bash
sudo systemctl status coinbasebot
```

## 2. Проверка логов systemd сервиса
```bash
sudo journalctl -u coinbasebot -f --since "2025-07-15 08:00:00"
```

## 3. Проверка основных логов приложения
```bash
tail -50 /root/coinbaserank-bot/sensortower_bot.log | grep -E "2025-07-15|08:01|11:01"
```

## 4. Проверка логов за период утреннего запуска
```bash
grep -E "2025-07-15 08:0[0-5]|2025-07-15 05:0[0-5]" /root/coinbaserank-bot/sensortower_bot.log
```

## 5. Проверка процессов Python
```bash
ps aux | grep python | grep -v grep
```

## 6. Проверка файлов блокировки
```bash
ls -la /root/coinbaserank-bot/coinbasebot.lock
```

## 7. Проверка последних записей в логе
```bash
tail -20 /root/coinbaserank-bot/sensortower_bot.log
```

## 8. Проверка статуса планировщика
```bash
grep -E "Scheduler started|планировщик|scheduler" /root/coinbaserank-bot/sensortower_bot.log | tail -10
```

## 9. Проверка ошибок в логах
```bash
grep -E "Error|Exception|Failed" /root/coinbaserank-bot/sensortower_bot.log | tail -20
```

## 10. Проверка времени последнего изменения файлов
```bash
ls -la /root/coinbaserank-bot/ | grep -E "\.py$|\.log$"
```

## Выполните эти команды и пришлите результаты