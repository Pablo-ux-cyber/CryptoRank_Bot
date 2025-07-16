#!/usr/bin/env python3
"""
Тест полного потока сообщений - как в реальном планировщике
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_full_message_flow():
    """Тестируем полный поток сообщения как в планировщике"""
    
    print("=== ТЕСТ ПОЛНОГО ПОТОКА СООБЩЕНИЙ ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from scheduler import SensorTowerScheduler
        scheduler = SensorTowerScheduler()
        print("✅ Планировщик создан")
        
        # Имитируем run_scraping_job() без реальной отправки
        print("\n--- Тестируем сбор данных ---")
        
        # 1. Получение рейтинга
        from json_rank_reader import get_rank_from_json
        current_rank = get_rank_from_json()
        print(f"✅ Рейтинг получен: {current_rank}")
        
        # 2. Fear & Greed Index
        fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
        print(f"✅ Fear & Greed: {fear_greed_data['value'] if fear_greed_data else 'Ошибка'}")
        
        # 3. Altcoin Season Index
        altseason_data = scheduler.altcoin_season_index.get_altseason_index()
        altcoin_result = f"{altseason_data['index']:.1%}" if altseason_data else "Ошибка"
        print(f"✅ Altcoin Season: {altcoin_result}")
        
        # 4. Формирование сообщения
        print("\n--- Формируем сообщение ---")
        
        # Используем логику из scheduler.py
        message_parts = []
        
        # Рейтинг
        message_parts.append(f"📱 Coinbase: #{current_rank}")
        
        # Fear & Greed
        if fear_greed_data:
            fear_greed_message = scheduler.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
            if fear_greed_message:
                message_parts.append(fear_greed_message)
        
        # Altcoin Season
        if altseason_data:
            altseason_message = scheduler.altcoin_season_index.format_altseason_message(altseason_data)
            if altseason_message:
                message_parts.append(altseason_message)
        
        final_message = "\n\n".join(message_parts)
        print(f"Сформированное сообщение:\n{final_message}")
        
        # 5. Тест отправки
        print("\n--- Тестируем отправку ---")
        success = scheduler.telegram_bot.send_message(final_message)
        
        if success:
            print("✅ ПОЛНЫЙ ПОТОК РАБОТАЕТ! Сообщение отправлено в Telegram")
            return True
        else:
            print("❌ ОШИБКА В ОТПРАВКЕ")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в потоке: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_full_message_flow()