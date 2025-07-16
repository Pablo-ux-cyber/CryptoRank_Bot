#!/usr/bin/env python3
"""
Финальный тест - отправляем сообщение точно как планировщик
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def final_telegram_test():
    """Финальный тест отправки"""
    
    print("=== ФИНАЛЬНЫЙ ТЕСТ ОТПРАВКИ В TELEGRAM ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from scheduler import SensorTowerScheduler
        import os
        
        # Показываем какой канал используется
        channel_id = os.environ.get('TELEGRAM_CHANNEL_ID', '@telegrm_hub')
        test_channel_id = os.environ.get('TELEGRAM_TEST_CHANNEL_ID', '@telegrm_hub')
        
        print(f"📺 Основной канал: {channel_id}")
        print(f"🧪 Тестовый канал: {test_channel_id}")
        
        scheduler = SensorTowerScheduler()
        
        print(f"📡 Бот отправляет в: {scheduler.telegram_bot.channel_id}")
        print(f"🤖 Имя бота: @baserank_bot")
        
        # Отправляем точно как планировщик
        print("\n📤 Отправляем сообщение как планировщик...")
        
        # Получаем данные как планировщик
        rankings_data = scheduler.scraper.scrape_category_rankings()
        fear_greed_data = scheduler.fear_greed_tracker.get_fear_greed_index()
        
        # Отправляем полное сообщение
        success = scheduler._send_combined_message(
            rankings_data=rankings_data,
            fear_greed_data=fear_greed_data,
            market_breadth_data=None,  # Без Market Breadth для быстроты
            chart_data=None
        )
        
        if success:
            print("🎯 ✅ СООБЩЕНИЕ ОТПРАВЛЕНО УСПЕШНО!")
            print(f"📱 Проверьте канал: {scheduler.telegram_bot.channel_id}")
            print("🔍 Если не видите сообщение:")
            print("   1. Убедитесь что подписаны на канал")
            print("   2. Проверьте настройки уведомлений")
            print("   3. Обновите Telegram")
        else:
            print("❌ ОШИБКА ОТПРАВКИ")
            
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    final_telegram_test()