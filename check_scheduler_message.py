#!/usr/bin/env python3
"""
Проверяем ТОЧНОЕ сообщение которое отправляет планировщик
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def check_scheduler_message():
    """Проверяем точное сообщение планировщика"""
    
    print("=== ПРОВЕРКА СООБЩЕНИЯ ПЛАНИРОВЩИКА ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from scheduler import SensorTowerScheduler
        from scraper import SensorTowerScraper
        
        # Инициализируем компоненты
        scheduler = SensorTowerScheduler()
        scraper = SensorTowerScraper()
        
        # 1. Проверяем данные рейтинга
        rankings_data = scraper.scrape_category_rankings()
        print(f"Данные рейтинга: {rankings_data}")
        
        # 2. Проверяем форматирование рейтинга
        rankings_message = scraper.format_rankings_message(rankings_data)
        print(f"\nФорматированное сообщение рейтинга:")
        print(f"'{rankings_message}'")
        
        # 3. Проверяем Fear & Greed
        fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
        fear_greed_message = scheduler.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
        print(f"\nFear & Greed сообщение:")
        print(f"'{fear_greed_message}'")
        
        # 4. Собираем комбинированное сообщение как в планировщике
        combined_message = rankings_message
        combined_message += "\n\n" + fear_greed_message
        
        print(f"\n=== ФИНАЛЬНОЕ КОМБИНИРОВАННОЕ СООБЩЕНИЕ ===")
        print(combined_message)
        print("=" * 50)
        
        # 5. Проверяем отправку (БЕЗ реальной отправки)
        print(f"\nДлина сообщения: {len(combined_message)} символов")
        print(f"Количество строк: {combined_message.count(chr(10)) + 1}")
        
        return combined_message
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    check_scheduler_message()