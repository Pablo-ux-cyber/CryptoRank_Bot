#!/usr/bin/env python3
"""
Тест планировщика для проверки логики времени
"""

from datetime import datetime, timedelta
import time

def test_scheduler_timing():
    """Тестируем логику планировщика"""
    
    print("=== ТЕСТ ЛОГИКИ ПЛАНИРОВЩИКА ===")
    
    # Имитируем разные времена
    test_cases = [
        # Время, описание
        (datetime(2025, 7, 16, 7, 59, 0), "За 2 минуты до запуска"),
        (datetime(2025, 7, 16, 8, 0, 30), "За 30 секунд до запуска"),
        (datetime(2025, 7, 16, 8, 1, 0), "Точно время запуска"),
        (datetime(2025, 7, 16, 8, 1, 30), "После времени запуска"),
        (datetime(2025, 7, 16, 10, 0, 0), "Обычное время"),
    ]
    
    for now, description in test_cases:
        print(f"\n--- {description} ---")
        print(f"Текущее время: {now}")
        
        # Логика из scheduler.py
        target_hour = 8
        target_minute = 1
        
        # Создаем целевое время на сегодня
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # Если целевое время уже прошло сегодня, планируем на завтра
        if now >= target_time:
            target_time = target_time.replace(day=target_time.day + 1)
        
        # Вычисляем количество секунд до целевого времени
        time_diff = (target_time - now).total_seconds()
        
        print(f"Целевое время: {target_time}")
        print(f"Разность времени: {time_diff} секунд")
        
        # Проверяем условие запуска
        should_run = time_diff <= 60
        print(f"Условие запуска (time_diff <= 60): {should_run}")
        
        # Проверяем логику сна
        if time_diff <= 300:  # Если до запуска меньше 5 минут
            sleep_time = 30  # Проверяем каждые 30 секунд
            print(f"Режим точной проверки: спит 30 секунд")
        else:
            # Обычный режим - спим до нужного времени, но не больше 1 часа
            sleep_time = min(time_diff - 300, 3600)  # Оставляем 5 минут запаса
            print(f"Обычный режим: спит {int(sleep_time/60)} минут")

if __name__ == "__main__":
    test_scheduler_timing()