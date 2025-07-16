#!/usr/bin/env python3
"""
Ручной тест планировщика с имитацией времени 08:01
"""

import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, '/home/runner/workspace')

from load_dotenv import load_dotenv
load_dotenv()

from logger import logger
from scheduler import SensorTowerScheduler

def test_scheduler_execution():
    """Тестируем выполнение планировщика в момент 08:01"""
    
    print("=== ТЕСТ ВЫПОЛНЕНИЯ ПЛАНИРОВЩИКА ===")
    
    # Создаем планировщик
    scheduler = SensorTowerScheduler()
    
    # Имитируем время 08:01:00
    test_time = datetime(2025, 7, 16, 8, 1, 0)
    
    print(f"Имитируем время: {test_time}")
    
    # Проверяем условия запуска
    target_hour = 8
    target_minute = 1
    
    # Создаем целевое время на сегодня
    target_time = test_time.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    # Если целевое время уже прошло сегодня, планируем на завтра
    if test_time >= target_time:
        target_time = target_time.replace(day=target_time.day + 1)
    
    # Вычисляем количество секунд до целевого времени
    time_diff = (target_time - test_time).total_seconds()
    
    print(f"Целевое время: {target_time}")
    print(f"Разность времени: {time_diff} секунд")
    
    # Проверяем условие запуска
    today = test_time.date()
    should_run = time_diff <= 60 and (scheduler.last_rank_update_date is None or scheduler.last_rank_update_date < today)
    
    print(f"last_rank_update_date: {scheduler.last_rank_update_date}")
    print(f"today: {today}")
    print(f"Условие запуска: {should_run}")
    
    if should_run:
        print("✅ ПЛАНИРОВЩИК ДОЛЖЕН ЗАПУСТИТЬСЯ!")
        print("Попробуем запустить run_scraping_job()...")
        
        try:
            # Попробуем запустить функцию сбора данных
            print("Тестируем только сбор данных без отправки...")
            
            # Тестируем получение рейтинга
            from json_rank_reader import get_rank_from_json
            rank = get_rank_from_json()
            print(f"Получен рейтинг: {rank}")
            
            # Тестируем Fear & Greed
            fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
            if fear_greed_data:
                print(f"Fear & Greed Index: {fear_greed_data['value']}")
            
            # Тестируем Altcoin Season
            altseason_data = scheduler.altcoin_season_index.get_altseason_index()
            if altseason_data:
                print(f"Altcoin Season Index: {altseason_data['index']:.1%}")
            
            print("✅ Все компоненты данных работают!")
            
        except Exception as e:
            print(f"❌ Ошибка при тестировании: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Планировщик НЕ должен запуститься")

if __name__ == "__main__":
    test_scheduler_execution()