#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ПЛАНИРОВЩИКА НА СЕРВЕРЕ

Команды для исправления проблемы пропуска времени 08:01:00:
"""

print("""
КОМАНДЫ ДЛЯ ИСПРАВЛЕНИЯ НА СЕРВЕРЕ:

1. Остановить планировщик:
sudo systemctl stop coinbasebot

2. Исправить scheduler.py (заменить строки 129-136):
sed -i '129,136c\
                # ИСПРАВЛЕНО: В критический период проверяем каждые 30 секунд\\
                if time_diff <= 300:  # Если до запуска меньше 5 минут\\
                    sleep_time = 30  # Проверяем каждые 30 секунд\\
                    logger.info(f"Планировщик в режиме точной проверки, спит 30 секунд")\\
                else:\\
                    # Обычный режим - спим до нужного времени, но не больше 1 часа\\
                    sleep_time = min(time_diff - 300, 3600)  # Оставляем 5 минут запаса\\
                    logger.info(f"Планировщик спит {int(sleep_time/60)} минут до следующей проверки")\\
\\
                # Спим с возможностью прерывания\\
                for _ in range(int(sleep_time)):\\
                    if self.stop_event.is_set():\\
                        break\\
                    time.sleep(1)' /root/coinbaserank_bot/scheduler.py

3. Запустить планировщик:
sudo systemctl start coinbasebot

4. Проверить логи:
tail -f /root/coinbaserank_bot/sensortower_bot.log

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- "Планировщик в режиме точной проверки, спит 30 секунд" (когда до 08:01 остается менее 5 минут)
- "ВРЕМЯ ОТПРАВКИ: Запуск полного сбора данных" (точно в 08:01:00)
""")