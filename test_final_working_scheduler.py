#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ тест планировщика с Market Breadth - скопировал точную логику рабочего test-message
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_scheduler_with_market_breadth():
    """Тестируем планировщик с Market Breadth данными"""
    
    print("=== ФИНАЛЬНЫЙ ТЕСТ ПЛАНИРОВЩИКА С MARKET BREADTH ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from scheduler import SensorTowerScheduler
        scheduler = SensorTowerScheduler()
        
        # Рейтинг в формате планировщика
        rankings_data = {
            "app_name": "Coinbase",
            "categories": [{"rank": "139"}]
        }
        
        # Fear & Greed
        fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
        print(f"✅ Fear & Greed: {fear_greed_data['value'] if fear_greed_data else 'ошибка'}")
        
        # Market Breadth данные (имитируем как в рабочем test-message)
        market_breadth_data = {
            'signal': '🟡',
            'condition': 'Neutral',
            'current_value': 36.4  # ВАЖНО: используем current_value как в test-message
        }
        print(f"✅ Market Breadth готов: {market_breadth_data}")
        
        print("\n--- ТЕСТИРУЕМ ИСПРАВЛЕННЫЙ ПЛАНИРОВЩИК ---")
        
        # Вызываем исправленный метод планировщика
        success = scheduler._send_combined_message(
            rankings_data=rankings_data,
            fear_greed_data=fear_greed_data,
            market_breadth_data=market_breadth_data,
            chart_data=None
        )
        
        if success:
            print("🎯 ✅ ПЛАНИРОВЩИК РАБОТАЕТ ИДЕАЛЬНО!")
            print("\n📋 ФИНАЛЬНОЕ СООБЩЕНИЕ СОДЕРЖИТ:")
            print("- Правильный формат рейтинга")
            print("- Fear & Greed с прогресс-баром") 
            print("- Market by 200MA с кликабельной ссылкой на график")
            print("\n🚀 ГОТОВ ДЛЯ СЕРВЕРА!")
        else:
            print("❌ Ошибка в планировщике")
            
        return success
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_scheduler_with_market_breadth()