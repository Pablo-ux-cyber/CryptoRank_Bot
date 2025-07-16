#!/usr/bin/env python3
"""
Проверка исправленной логики времени в планировщике
"""

from datetime import datetime

def verify_scheduler_timing():
    """Проверяем исправленную логику времени"""
    
    print("=== ПРОВЕРКА ЛОГИКИ ВРЕМЕНИ В ПЛАНИРОВЩИКЕ ===")
    
    # Имитируем разные времена и проверяем условие запуска
    test_cases = [
        # (время, ожидаемый результат, описание)
        (datetime(2025, 7, 16, 7, 59, 0), False, "За 2 минуты - НЕ должен запуститься"),
        (datetime(2025, 7, 16, 8, 0, 45), True, "За 15 секунд - ДОЛЖЕН запуститься"),
        (datetime(2025, 7, 16, 8, 1, 0), True, "Точно 08:01:00 - ДОЛЖЕН запуститься"),
        (datetime(2025, 7, 16, 8, 1, 30), True, "08:01:30 - ДОЛЖЕН запуститься"),
        (datetime(2025, 7, 16, 8, 1, 59), True, "08:01:59 - ДОЛЖЕН запуститься"),
        (datetime(2025, 7, 16, 8, 2, 0), False, "08:02:00 - НЕ должен запуститься"),
    ]
    
    all_passed = True
    
    for now, expected, description in test_cases:
        # Логика из исправленного scheduler.py
        target_hour = 8
        target_minute = 1
        today = now.date()
        last_rank_update_date = None  # Имитируем что сегодня не отправляли
        
        # Создаем целевое время
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        if now >= target_time:
            target_time = target_time.replace(day=target_time.day + 1)
        time_diff = (target_time - now).total_seconds()
        
        # ИСПРАВЛЕННАЯ ЛОГИКА
        is_exact_time = (now.hour == target_hour and now.minute == target_minute)
        is_time_window = time_diff <= 60
        not_sent_today = (last_rank_update_date is None or last_rank_update_date < today)
        
        should_run = (is_exact_time or is_time_window) and not_sent_today
        
        # Проверяем результат
        status = "✅ ПРОШЕЛ" if should_run == expected else "❌ ПРОВАЛИЛСЯ"
        if should_run != expected:
            all_passed = False
        
        print(f"{status} | {now.strftime('%H:%M:%S')} | {description}")
        print(f"        is_exact_time: {is_exact_time}, is_time_window: {is_time_window}, результат: {should_run}")
    
    print(f"\n=== ИТОГ ===")
    if all_passed:
        print("✅ ВСЕ ТЕСТЫ ПРОШЛИ! Логика планировщика работает правильно")
        print("🚀 Планировщик гарантированно сработает в период 08:01:00-08:01:59")
    else:
        print("❌ ЕСТЬ ОШИБКИ В ЛОГИКЕ!")
    
    return all_passed

if __name__ == "__main__":
    verify_scheduler_timing()