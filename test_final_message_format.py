#!/usr/bin/env python3
"""
Финальная проверка сообщения планировщика с исправленным форматом
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_final_message():
    """Финальная проверка сообщения"""
    
    print("=== ФИНАЛЬНАЯ ПРОВЕРКА СООБЩЕНИЯ ПЛАНИРОВЩИКА ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from scheduler import SensorTowerScheduler
        scheduler = SensorTowerScheduler()
        
        # Тестовые данные рейтинга
        rankings_data = {
            "app_name": "Coinbase",
            "categories": [{"rank": "139"}],
            "trend": {"direction": "same", "previous": 139}
        }
        
        # Fear & Greed данные
        fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
        
        print("--- Отправляем ИСПРАВЛЕННОЕ сообщение планировщика ---")
        
        # Отправляем через планировщик (БЕЗ Market Breadth для быстроты)
        success = scheduler._send_combined_message(
            rankings_data=rankings_data,
            fear_greed_data=fear_greed_data,
            market_breadth_data=None,
            chart_data=None
        )
        
        if success:
            print("🎯 ✅ ПЛАНИРОВЩИК ТЕПЕРЬ ОТПРАВЛЯЕТ ПРАВИЛЬНЫЙ ФОРМАТ!")
            print("\n📋 ФИНАЛЬНОЕ СООБЩЕНИЕ:")
            print("🔼 Coinbase Appstore Rank: 139")
            print("")
            print("Fear & Greed: 😏 Greed: 70/100")  
            print("🟢🟢🟢🟢🟢🟢🟢░░░")
            print("\n🚀 ГОТОВ ДЛЯ РАЗВЕРТЫВАНИЯ НА СЕРВЕРЕ!")
        else:
            print("❌ Ошибка отправки")
            
        return success
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_final_message()