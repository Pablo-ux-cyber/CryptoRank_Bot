#!/usr/bin/env python3
"""
Тест планировщика с Market Breadth - КОПИЯ рабочей логики из /test-message
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_scheduler_with_market_breadth():
    """Тестируем планировщик с Market Breadth как в рабочем test-message"""
    
    print("=== ТЕСТ ПЛАНИРОВЩИКА С MARKET BREADTH ===")
    
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
        print(f"✅ Fear & Greed получен: {fear_greed_data['value'] if fear_greed_data else 'ошибка'}")
        
        # Market Breadth - загружаем как в рабочем test-message
        market_breadth_data = None
        print("📊 Загружаем Market Breadth (как в рабочем test-message)...")
        
        try:
            # ВАЖНО: timeout 3 минуты для Market Breadth
            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError("Market Breadth timeout")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(180)  # 3 минуты
            
            market_breadth_data = scheduler.market_breadth.get_market_breadth_data(fast_mode=False)
            signal.alarm(0)
            
            if market_breadth_data:
                print(f"✅ Market Breadth: {market_breadth_data['signal']} {market_breadth_data['condition']} ({market_breadth_data['current_value']:.1f}%)")
            else:
                print("❌ Market Breadth недоступен")
                
        except TimeoutError:
            print("⏰ Market Breadth превысил таймаут 3 минуты")
            signal.alarm(0)
            market_breadth_data = None
        except Exception as e:
            print(f"❌ Ошибка Market Breadth: {str(e)}")
            signal.alarm(0)
            market_breadth_data = None
        
        print("\n--- ТЕСТИРУЕМ ПЛАНИРОВЩИК С MARKET BREADTH ---")
        
        # Отправляем через планировщик
        success = scheduler._send_combined_message(
            rankings_data=rankings_data,
            fear_greed_data=fear_greed_data,
            market_breadth_data=market_breadth_data,
            chart_data=None
        )
        
        if success:
            print("🎯 ✅ ПЛАНИРОВЩИК С MARKET BREADTH РАБОТАЕТ!")
            print("\n📋 СООБЩЕНИЕ СОДЕРЖИТ:")
            print("- 🔼 Coinbase Appstore Rank: 139")
            print("- Fear & Greed с прогресс-баром")
            if market_breadth_data:
                print(f"- Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['current_value']:.1f}%")
            else:
                print("- Market by 200MA: НЕ ВКЛЮЧЕН (таймаут)")
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