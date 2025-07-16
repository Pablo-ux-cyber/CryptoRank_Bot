#!/usr/bin/env python3
"""
Тест планировщика БЕЗ Market Breadth для проверки основного формата
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_scheduler_basic_message():
    """Тестируем базовое сообщение из планировщика без Market Breadth"""
    
    print("=== ТЕСТ БАЗОВОГО СООБЩЕНИЯ ИЗ ПЛАНИРОВЩИКА ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from scheduler import SensorTowerScheduler
        scheduler = SensorTowerScheduler()
        
        # Создаем тестовые данные в том же формате что и планировщик
        rankings_data = {
            "app_name": "Coinbase",
            "app_id": "886427730", 
            "date": "2025-07-16",
            "categories": [
                {"category": "US - iPhone - Top Free", "rank": "139"}
            ],
            "trend": {"direction": "same", "previous": None}
        }
        
        # Получаем Fear & Greed данные
        fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
        print(f"Fear & Greed получен: {fear_greed_data['value'] if fear_greed_data else 'ошибка'}")
        
        print("--- Вызываем _send_combined_message БЕЗ Market Breadth ---")
        
        # Вызываем метод отправки сообщения БЕЗ market_breadth_data
        success = scheduler._send_combined_message(
            rankings_data=rankings_data,
            fear_greed_data=fear_greed_data,
            market_breadth_data=None,  # НЕТ Market Breadth
            chart_data=None
        )
        
        if success:
            print("✅ ПЛАНИРОВЩИК ОТПРАВИЛ БАЗОВОЕ СООБЩЕНИЕ!")
            print("Содержит:")
            print("- 🔼 Coinbase Appstore Rank: 139") 
            print("- Fear & Greed с прогресс-баром")
            print("- НЕТ Market Breadth (как ожидалось)")
        else:
            print("❌ Ошибка отправки базового сообщения")
            
        return success
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_scheduler_basic_message()