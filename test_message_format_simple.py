#!/usr/bin/env python3
"""
Простой тест формата сообщения без загрузки Market Breadth
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_message_format():
    """Тестируем ТОЧНЫЙ формат сообщения как требует пользователь"""
    
    print("=== ТЕСТ ФОРМАТА СООБЩЕНИЯ ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from scheduler import SensorTowerScheduler
        scheduler = SensorTowerScheduler()
        
        # 1. Рейтинг
        from json_rank_reader import get_rank_from_json
        current_rank = get_rank_from_json()
        print(f"Рейтинг: {current_rank}")
        
        # 2. Fear & Greed
        fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
        print(f"Fear & Greed: {fear_greed_data['value'] if fear_greed_data else 'Ошибка'}")
        
        # 3. Имитируем Market Breadth данные
        market_breadth_data = {
            'signal': '🟡',
            'condition': 'Neutral',
            'percentage': 36.4
        }
        
        print("\n--- ТОЧНЫЙ ФОРМАТ КАК ТРЕБУЕТ ПОЛЬЗОВАТЕЛЬ ---")
        
        # Собираем сообщение в ТОЧНОМ формате пользователя
        message_parts = []
        
        # 1. Coinbase Appstore Rank (ТОЧНО как в примере)
        message_parts.append(f"🔼 Coinbase Appstore Rank: {current_rank}")
        
        # 2. Fear & Greed (ТОЧНО как в примере)
        if fear_greed_data:
            fear_greed_message = scheduler.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
            if fear_greed_message:
                message_parts.append(fear_greed_message)
        
        # 3. Market by 200MA (ТОЧНО как в примере пользователя)
        # ФОРМАТ: Market by 200MA: 🟡 Neutral: 36.4%
        # И вся строка должна быть ссылкой на график
        fake_chart_url = "https://files.catbox.moe/example.png"
        market_message = f"[Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['percentage']}%]({fake_chart_url})"
        message_parts.append(market_message)
        
        # Собираем финальное сообщение
        final_message = "\n\n".join(message_parts)
        
        print(f"\n--- ФИНАЛЬНОЕ СООБЩЕНИЕ В ПРАВИЛЬНОМ ФОРМАТЕ ---")
        print(final_message)
        print(f"\n--- КАК ДОЛЖНО ВЫГЛЯДЕТЬ В TELEGRAM ---")
        print("🔼 Coinbase Appstore Rank: 139")
        print("")
        print("Fear & Greed: 😏 Greed: 70/100")
        print("🟢🟢🟢🟢🟢🟢🟢░░░")
        print("")
        print("Market by 200MA: 🟡 Neutral: 36.4%  <- ВСЯ СТРОКА КЛИКАБЕЛЬНАЯ")
        
        # Отправляем в Telegram для тестирования
        print(f"\n--- ОТПРАВКА В TELEGRAM ---")
        success = scheduler.telegram_bot.send_message(final_message)
        
        if success:
            print("✅ СООБЩЕНИЕ ОТПРАВЛЕНО В ПРАВИЛЬНОМ ФОРМАТЕ!")
        else:
            print("❌ Ошибка отправки")
            
        return success, final_message
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    test_message_format()