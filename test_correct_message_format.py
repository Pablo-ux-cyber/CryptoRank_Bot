#!/usr/bin/env python3
"""
Тест правильного формата сообщения как в оригинале
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_correct_message():
    """Тестируем правильный формат сообщения"""
    
    print("=== ТЕСТ ПРАВИЛЬНОГО ФОРМАТА СООБЩЕНИЯ ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from scheduler import SensorTowerScheduler
        scheduler = SensorTowerScheduler()
        
        print("--- Собираем данные ---")
        
        # 1. Рейтинг
        from json_rank_reader import get_rank_from_json
        current_rank = get_rank_from_json()
        print(f"Рейтинг: {current_rank}")
        
        # 2. Fear & Greed
        fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
        print(f"Fear & Greed: {fear_greed_data['value'] if fear_greed_data else 'Ошибка'}")
        
        # 3. Market Breadth (используем функцию из main.py)
        market_breadth_data = None
        try:
            from main import get_market_breadth_data_no_cache
            result = get_market_breadth_data_no_cache()
            if result and result.get('status') == 'success':
                market_breadth_data = result['data']
                print(f"Market Breadth: {market_breadth_data['signal']} {market_breadth_data['condition']} {market_breadth_data['percentage']}%")
            else:
                print("Market Breadth: недоступен")
        except Exception as e:
            print(f"Market Breadth: ошибка - {str(e)}")
            market_breadth_data = None
        
        print("\n--- Формируем ПРАВИЛЬНОЕ сообщение ---")
        
        # ПРАВИЛЬНЫЙ ФОРМАТ как в оригинале
        message_parts = []
        
        # 1. Coinbase App Rank (ТОЧНО как в примере пользователя)
        message_parts.append(f"🔼 Coinbase Appstore Rank: {current_rank}")
        
        # 2. Fear & Greed (точно как в примере)
        if fear_greed_data:
            fear_greed_message = scheduler.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
            if fear_greed_message:
                message_parts.append(fear_greed_message)
        
        # 3. Market by 200MA (точно как в примере со ссылкой)
        if market_breadth_data:
            # Создаем график и получаем ссылку
            try:
                from main import create_quick_chart
                from image_uploader import image_uploader
                
                png_data = create_quick_chart()
                if png_data:
                    external_url = image_uploader.upload_chart(png_data)
                    if external_url:
                        # ТОЧНЫЙ ФОРМАТ как в примере пользователя - строка кликабельная полностью
                        market_message = f"[Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['percentage']}%]({external_url})"
                        message_parts.append(market_message)
                        print(f"График загружен: {external_url}")
                    else:
                        # Без ссылки
                        market_message = f"Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['percentage']}%"
                        message_parts.append(market_message)
                else:
                    market_message = f"Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['percentage']}%"
                    message_parts.append(market_message)
            except Exception as e:
                print(f"Ошибка создания графика: {str(e)}")
                market_message = f"Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['percentage']}%"
                message_parts.append(market_message)
        
        # Собираем финальное сообщение
        final_message = "\n\n".join(message_parts)
        
        print(f"\n--- ФИНАЛЬНОЕ СООБЩЕНИЕ ---")
        print(final_message)
        
        # Отправляем в Telegram
        print(f"\n--- ОТПРАВКА В TELEGRAM ---")
        success = scheduler.telegram_bot.send_message(final_message)
        
        if success:
            print("✅ СООБЩЕНИЕ ОТПРАВЛЕНО В ПРАВИЛЬНОМ ФОРМАТЕ!")
        else:
            print("❌ Ошибка отправки")
            
        return success
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_correct_message()