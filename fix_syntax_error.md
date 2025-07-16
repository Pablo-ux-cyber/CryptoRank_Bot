# ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ

## Проблема
Команда sed сломала отступы в Python коде, возникла IndentationError.

## Быстрое исправление на сервере:

```bash
# 1. Остановить сервис
sudo systemctl stop coinbasebot

# 2. Восстановить из бэкапа
cp /root/coinbaserank_bot/scheduler.py.backup /root/coinbaserank_bot/scheduler.py

# 3. Исправить вручную правильно
nano /root/coinbaserank_bot/scheduler.py
```

## В nano найти строки 115-116 и заменить:

**ЗАМЕНИТЬ ЭТИ СТРОКИ:**
```python
                # Проверяем, не пора ли уже отправлять (если время подошло в течение последней минуты)
                if time_diff <= 60 and (self.last_rank_update_date is None or self.last_rank_update_date < today):
```

**НА ЭТИ СТРОКИ:**
```python
                # ИСПРАВЛЕНО: Проверяем точное время - если сейчас 08:01:XX и еще не отправляли сегодня
                current_time_match = (now.hour == target_hour and now.minute == target_minute)
                if current_time_match and (self.last_rank_update_date is None or self.last_rank_update_date < today):
```

## После исправления:
```bash
# 4. Сохранить (Ctrl+X, Y, Enter)
# 5. Запустить сервис
sudo systemctl start coinbasebot
sudo systemctl status coinbasebot
```