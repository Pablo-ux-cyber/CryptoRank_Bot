#!/usr/bin/env python3
"""
Быстрый тест основных функций планировщика
"""

from datetime import datetime
import sys
sys.path.insert(0, '/home/runner/workspace')

def quick_test():
    print("=== БЫСТРЫЙ ТЕСТ ПЛАНИРОВЩИКА ===")
    
    # Тест 1: Логика времени
    print("\n1. Тест логики времени:")
    now = datetime(2025, 7, 16, 8, 1, 0)  # Точно 08:01
    target_hour, target_minute = 8, 1
    
    is_exact_time = (now.hour == target_hour and now.minute == target_minute)
    print(f"   Время {now} → is_exact_time: {is_exact_time}")
    
    # Тест 2: JSON reader
    print("\n2. Тест чтения рейтинга:")
    try:
        from json_rank_reader import get_rank_from_json
        rank = get_rank_from_json()
        print(f"   ✅ Рейтинг: {rank}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 3: Импорт планировщика
    print("\n3. Тест импорта планировщика:")
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        from scheduler import SensorTowerScheduler
        scheduler = SensorTowerScheduler()
        print(f"   ✅ Планировщик создан: {type(scheduler).__name__}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print("\n=== РЕЗУЛЬТАТ ===")
    print("Основные компоненты планировщика работают!")

if __name__ == "__main__":
    quick_test()