#!/usr/bin/env python3
"""
Тест ПОЛНОГО сообщения из исправленного scheduler.py
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_full_scheduler_message():
    """Тестируем полное сообщение из планировщика"""
    
    print("=== ТЕСТ ПОЛНОГО СООБЩЕНИЯ ИЗ ПЛАНИРОВЩИКА ===")
    
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
        
        # Имитируем Market Breadth данные
        market_breadth_data = {
            'signal': '🟡',
            'condition': 'Neutral',
            'percentage': 36.4
        }
        
        print("--- Вызываем _send_combined_message ---")
        
        # Вызываем метод отправки сообщения напрямую
        success = scheduler._send_combined_message(
            rankings_data=rankings_data,
            fear_greed_data=fear_greed_data,
            market_breadth_data=market_breadth_data,
            chart_data=None  # Пусть создает график сам
        )
        
        if success:
            print("✅ ПЛАНИРОВЩИК ОТПРАВИЛ СООБЩЕНИЕ В ПРАВИЛЬНОМ ФОРМАТЕ!")
            print("Сообщение должно содержать:")
            print("- 🔼 Coinbase Appstore Rank: 139")
            print("- Fear & Greed с прогресс-баром")
            print("- Market by 200MA как кликабельная ссылка")
        else:
            print("❌ Ошибка отправки из планировщика")
            
        return success
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_full_scheduler_message()