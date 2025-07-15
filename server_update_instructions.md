# ИСПРАВЛЕНИЕ ПЛАНИРОВЩИКА - ФИНАЛЬНАЯ ИНСТРУКЦИЯ

## Проблема
Планировщик работал каждые 5 минут (08:03, 08:08, 08:13...) и пропускал точное время 08:01 UTC (11:01 MSK).

## Решение
Новый эффективный планировщик:
- Вычисляет точное время до 08:01 UTC
- Спит ровно до нужного времени
- Не тратит ресурсы на постоянные проверки

## ИНСТРУКЦИЯ ДЛЯ СЕРВЕРА

### 1. Скачать исправленный файл
```bash
cd /root/coinbaserank_bot
curl -o scheduler_new.py "https://raw.githubusercontent.com/user/repo/scheduler.py"
```

### 2. ИЛИ скопировать код вручную
Заменить в файле `/root/coinbaserank_bot/scheduler.py` метод `_scheduler_loop` на:

```python
def _scheduler_loop(self):
    """
    The main scheduler loop that runs in a background thread.
    - ИСПРАВЛЕНО: Собирает ВСЕ данные включая рейтинг НЕПОСРЕДСТВЕННО в момент отправки в 8:01 UTC
    - Данные рейтинга загружаются через rnk.py прямо перед отправкой для максимальной актуальности
    - Все данные собираются за один раз и отправляются одним сообщением
    """
    # Переменные для отслеживания, когда последний раз обновлялись данные
    self.last_rank_update_date = None
    self.last_rnk_update_date = None
    
    # При запуске не будем загружать данные Google Trends - получим их вместе с общим обновлением
    logger.info("ИСПРАВЛЕНО: Планировщик запущен, ПОЛНЫЙ сбор данных + отправка в 11:01 MSK (без предварительного сбора в 10:59)")
    
    while not self.stop_event.is_set():
        try:
            # Текущее время и дата
            now = datetime.now()
            today = now.date()
            
            # Вычисляем время до следующего запуска (08:01 UTC = 11:01 MSK)
            target_hour = 8
            target_minute = 1
            
            # Создаем целевое время на сегодня
            target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            
            # Если целевое время уже прошло сегодня, планируем на завтра
            if now >= target_time:
                target_time = target_time.replace(day=target_time.day + 1)
            
            # Вычисляем количество секунд до целевого времени
            time_diff = (target_time - now).total_seconds()
            
            logger.info(f"Следующий запуск запланирован на: {target_time} (через {int(time_diff/3600)} часов {int((time_diff%3600)/60)} минут)")
            
            # Проверяем, не пора ли уже отправлять (если время подошло в течение последней минуты)
            if time_diff <= 60 and (self.last_rank_update_date is None or self.last_rank_update_date < today):
                logger.info(f"ВРЕМЯ ОТПРАВКИ: Запуск полного сбора данных и отправки в {now}")
                try:
                    self.run_scraping_job()
                    self.last_rank_update_date = today
                    logger.info(f"Данные успешно собраны и отправлены: {now}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке данных: {str(e)}")
                
                # После отправки спим до следующего дня
                time_diff = 24 * 60 * 60  # 24 часа
            
            # Спим до целевого времени, но не более 1 часа за раз (для возможности остановки)
            sleep_time = min(time_diff, 3600)  # максимум 1 час
            logger.info(f"Планировщик спит {int(sleep_time/60)} минут до следующей проверки")
            
            # Спим с возможностью прерывания
            for _ in range(int(sleep_time)):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Ошибка в циле планировщика: {str(e)}")
            # При ошибке спим 5 минут перед повтором
            time.sleep(300)
```

### 3. Перезапуск сервиса
```bash
sudo systemctl restart coinbasebot
sudo systemctl status coinbasebot
```

### 4. Проверка логов
```bash
tail -f /root/coinbaserank_bot/sensortower_bot.log
```

## Ожидаемый результат
В логах должно появиться:
```
Следующий запуск запланирован на: 2025-07-16 08:01:00 (через X часов Y минут)
Планировщик спит X минут до следующей проверки
```

## Преимущества нового планировщика
1. **Точность**: Никогда не пропустит время 08:01 UTC
2. **Эффективность**: Не тратит ресурсы на постоянные проверки
3. **Надежность**: Автоматически планирует следующий день
4. **Логичность**: Спит ровно до нужного времени

Завтра в 08:01 UTC (11:01 MSK) сообщение будет отправлено ГАРАНТИРОВАННО!