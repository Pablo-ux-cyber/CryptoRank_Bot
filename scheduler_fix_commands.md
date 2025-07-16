# КОМАНДЫ ДЛЯ ИСПРАВЛЕНИЯ SCHEDULER.PY НА СЕРВЕРЕ

## Проблема
Планировщик не отправляет сообщения потому что проверяет `time_diff <= 60`, но в момент 08:01:00 time_diff уже становится ~86400 секунд (до завтрашнего дня).

## Исправление
Заменить проверку `time_diff <= 60` на точную проверку времени `now.hour == 8 and now.minute == 1`.

## Команды для сервера:

```bash
# 1. Остановить сервис
sudo systemctl stop coinbasebot

# 2. Сделать бэкап
cp /root/coinbaserank_bot/scheduler.py /root/coinbaserank_bot/scheduler.py.backup

# 3. Исправить проблемную строку
sed -i '119s/.*/                current_time_match = (now.hour == target_hour and now.minute == target_minute)/' /root/coinbaserank_bot/scheduler.py
sed -i '120s/.*/                if current_time_match and (self.last_rank_update_date is None or self.last_rank_update_date < today):/' /root/coinbaserank_bot/scheduler.py

# 4. Проверить что исправилось
grep -A 3 -B 1 "current_time_match" /root/coinbaserank_bot/scheduler.py

# 5. Запустить сервис
sudo systemctl start coinbasebot

# 6. Проверить логи
tail -f /root/coinbaserank_bot/sensortower_bot.log
```

## Ожидаемый результат в логах
```
INFO - Следующий запуск запланирован на: 2025-07-17 08:01:00
INFO - Планировщик спит 60 минут до следующей проверки
```

## Завтра в 08:01 UTC должно появиться
```
INFO - ВРЕМЯ ОТПРАВКИ: Запуск полного сбора данных и отправки
```