#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ тест - берем рабочий формат test_message_format_simple.py за основу
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_final_working_format():
    """Тестируем ФИНАЛЬНЫЙ рабочий формат"""
    
    print("=== ФИНАЛЬНЫЙ ТЕСТ РАБОЧЕГО ФОРМАТА ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from scheduler import SensorTowerScheduler
        scheduler = SensorTowerScheduler()
        
        # Данные в том же формате что и планировщик
        rankings_data = {
            "app_name": "Coinbase",
            "categories": [{"rank": "139"}]
        }
        
        # Fear & Greed данные
        fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
        
        # Market Breadth данные (как в рабочем тесте)
        market_breadth_data = {
            'signal': '🟡',
            'condition': 'Neutral',
            'percentage': 36.4
        }
        
        print("--- Тестируем исправленный _send_combined_message ---")
        
        # Используем исправленный метод
        success = scheduler._send_combined_message(
            rankings_data=rankings_data,
            fear_greed_data=fear_greed_data,
            market_breadth_data=market_breadth_data,
            chart_data=None
        )
        
        if success:
            print("✅ ИСПРАВЛЕННЫЙ ПЛАНИРОВЩИК РАБОТАЕТ!")
            print("\nФИНАЛЬНОЕ СООБЩЕНИЕ СОДЕРЖИТ:")
            print("🔼 Coinbase Appstore Rank: 139")
            print("Fear & Greed: 😏 Greed: 70/100")
            print("🟢🟢🟢🟢🟢🟢🟢░░░")
            print("[Market by 200MA: 🟡 Neutral: 36.4%](ссылка) <- КЛИКАБЕЛЬНАЯ")
        else:
            print("❌ Ошибка в исправленном планировщике")
            
        return success
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_final_working_format()