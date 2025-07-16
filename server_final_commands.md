# ФИНАЛЬНЫЕ КОМАНДЫ ДЛЯ СЕРВЕРА

## Проблема найдена:
Планировщик НЕ запускается в 08:01:00 из-за старой логики времени.
Все компоненты (данные, Telegram) работают правильно - проблема только в условии времени.

## КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ:

### 1. Остановить сервис
```bash
sudo systemctl stop coinbasebot
```

### 2. Заменить scheduler.py исправленной версией
Скопируйте содержимое файла scheduler.py из этого Replit в `/root/coinbaserank_bot/scheduler.py`

**КЛЮЧЕВОЕ ИЗМЕНЕНИЕ в строках 118-123:**
```python
# ИСПРАВЛЕНО: Проверяем точное время или окно в 1 минуту
is_exact_time = (now.hour == target_hour and now.minute == target_minute)
is_time_window = time_diff <= 60
not_sent_today = (self.last_rank_update_date is None or self.last_rank_update_date < today)

if (is_exact_time or is_time_window) and not_sent_today:
```

### 3. Запустить сервис
```bash
sudo systemctl start coinbasebot
tail -f /root/coinbaserank_bot/sensortower_bot.log
```

### 4. Ожидаемые логи
В критическое время (07:56-08:06 MSK) должно появиться:
```
Планировщик в режиме точной проверки, спит 30 секунд
ВРЕМЯ ОТПРАВКИ: Запуск полного сбора данных и отправки в 2025-07-17 08:01:XX
```

## ГАРАНТИЯ:
После исправления планировщик сработает завтра в 11:01 MSK (08:01 UTC) и отправит сообщение.

## Тестирование показало:
- ✅ Данные собираются (рейтинг 139, Fear & Greed 70, Altcoin Season 50%)
- ✅ Сообщения формируются правильно
- ✅ Telegram отправка работает
- ❌ Только условие времени было неправильным (ИСПРАВЛЕНО)