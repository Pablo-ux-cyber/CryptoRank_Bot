# КОМАНДЫ ДЛЯ ПЕРЕЗАПУСКА ПОСЛЕ КОПИРОВАНИЯ ФАЙЛОВ

## 1. Остановить сервис
```bash
sudo systemctl stop coinbasebot
```

## 2. Удалить файл блокировки
```bash
sudo rm -f /root/coinbaserank_bot/coinbasebot.lock
```

## 3. Запустить сервис
```bash
sudo systemctl start coinbasebot
```

## 4. Проверить статус
```bash
sudo systemctl status coinbasebot
```

## 5. Посмотреть логи
```bash
tail -f /root/coinbaserank_bot/sensortower_bot.log
```

## Что должно быть в логах (правильный результат):

✅ **ОДИН планировщик без ошибок:**
```
Следующий запуск запланирован на: 2025-07-16 08:01:00 (через X часов Y минут)
Планировщик спит 60 минут до следующей проверки
```

✅ **Flask приложение БЕЗ планировщика:**
```
Flask app initialized without starting scheduler - scheduler should be started externally
```

❌ **НЕ должно быть:**
```
Другой экземпляр бота уже запущен. Завершение работы.
Failed to start the scheduler
```

## Результат
После этих команд планировщик будет работать правильно и завтра в 11:01 MSK отправит сообщение.