#!/usr/bin/env python3
"""
Тест исправленного планировщика
"""

from datetime import datetime

def test_fixed_logic():
    """Тестируем исправленную логику планировщика"""
    
    print("=== ТЕСТ ИСПРАВЛЕННОЙ ЛОГИКИ ===")
    
    test_cases = [
        (datetime(2025, 7, 16, 7, 59, 0), "За 2 минуты до запуска"),
        (datetime(2025, 7, 16, 8, 0, 30), "За 30 секунд до запуска"),
        (datetime(2025, 7, 16, 8, 1, 0), "Точно время запуска"),
        (datetime(2025, 7, 16, 8, 1, 30), "После времени запуска"),
    ]
    
    for now, description in test_cases:
        print(f"\n--- {description} ---")
        print(f"Время: {now}")
        
        # Исправленная логика
        target_hour = 8
        target_minute = 1
        today = now.date()
        last_rank_update_date = None  # Имитируем что сегодня еще не отправляли
        
        # Создаем целевое время
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        if now >= target_time:
            target_time = target_time.replace(day=target_time.day + 1)
        time_diff = (target_time - now).total_seconds()
        
        # ИСПРАВЛЕННАЯ ПРОВЕРКА
        is_exact_time = (now.hour == target_hour and now.minute == target_minute)
        is_time_window = time_diff <= 60
        not_sent_today = (last_rank_update_date is None or last_rank_update_date < today)
        
        should_run = (is_exact_time or is_time_window) and not_sent_today
        
        print(f"is_exact_time: {is_exact_time}")
        print(f"is_time_window: {is_time_window}")
        print(f"not_sent_today: {not_sent_today}")
        print(f"ДОЛЖЕН ЗАПУСТИТЬСЯ: {should_run}")

if __name__ == "__main__":
    test_fixed_logic()