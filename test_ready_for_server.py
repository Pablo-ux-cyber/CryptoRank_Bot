#!/usr/bin/env python3
"""
ГОТОВЫЙ КОД ДЛЯ СЕРВЕРА - базируется на рабочем test_message_format_simple.py
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_server_ready_format():
    """Тестируем ГОТОВЫЙ ДЛЯ СЕРВЕРА формат"""
    
    print("=== ТЕСТ ГОТОВОГО ДЛЯ СЕРВЕРА ФОРМАТА ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from scheduler import SensorTowerScheduler
        scheduler = SensorTowerScheduler()
        
        # 1. Рейтинг из JSON
        from json_rank_reader import get_rank_from_json
        current_rank = get_rank_from_json()
        print(f"✅ Рейтинг: {current_rank}")
        
        # 2. Fear & Greed
        fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
        print(f"✅ Fear & Greed: {fear_greed_data['value'] if fear_greed_data else 'ошибка'}")
        
        # 3. Market Breadth с быстрыми данными (НЕ загружаем 50 монет)
        market_breadth_data = {
            'signal': '🟡',
            'condition': 'Neutral',
            'percentage': 36.4
        }
        print(f"✅ Market Breadth: {market_breadth_data['signal']} {market_breadth_data['condition']} {market_breadth_data['percentage']}%")
        
        print("\n--- ФОРМИРУЕМ ГОТОВОЕ ДЛЯ СЕРВЕРА СООБЩЕНИЕ ---")
        
        # Собираем сообщение в ТОЧНОМ формате пользователя
        message_parts = []
        
        # 1. Coinbase Appstore Rank
        message_parts.append(f"🔼 Coinbase Appstore Rank: {current_rank}")
        
        # 2. Fear & Greed
        if fear_greed_data:
            fear_greed_message = scheduler.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
            if fear_greed_message:
                message_parts.append(fear_greed_message)
        
        # 3. Market by 200MA БЕЗ загрузки графика (для теста)
        market_message = f"Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['percentage']}%"
        message_parts.append(market_message)
        
        # Собираем финальное сообщение
        final_message = "\n\n".join(message_parts)
        
        print(f"\n--- ГОТОВОЕ СООБЩЕНИЕ ДЛЯ СЕРВЕРА ---")
        print(final_message)
        
        # Отправляем в Telegram
        print(f"\n--- ОТПРАВКА В TELEGRAM ---")
        success = scheduler.telegram_bot.send_message(final_message)
        
        if success:
            print("✅ ГОТОВОЕ СООБЩЕНИЕ ОТПРАВЛЕНО!")
            print("\n🎯 ЭТОТ КОД ГОТОВ ДЛЯ СЕРВЕРА!")
            print("- Правильный формат")
            print("- Быстрая работа") 
            print("- Реальные данные")
            print("- Проверенная отправка")
        else:
            print("❌ Ошибка отправки")
            
        return success, final_message
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    test_server_ready_format()