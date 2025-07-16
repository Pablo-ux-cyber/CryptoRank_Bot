#!/usr/bin/env python3
"""
Тест реальной отправки в Telegram
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_telegram_sending():
    """Тестируем реальную отправку в Telegram"""
    
    print("=== ТЕСТ РЕАЛЬНОЙ ОТПРАВКИ В TELEGRAM ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
        print(f"Токен бота: {'✅ ЕСТЬ' if TELEGRAM_BOT_TOKEN else '❌ НЕТ'}")
        print(f"ID канала: {'✅ ЕСТЬ' if TELEGRAM_CHANNEL_ID else '❌ НЕТ'}")
        
        # Тестируем синхронный Telegram Bot
        from telegram_bot_sync import TelegramBotSync
        bot = TelegramBotSync(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID)
        print("✅ TelegramBotSync создан")
        
        # Попробуем отправить тестовое сообщение
        test_message = "🧪 ТЕСТ: Проверка работы планировщика"
        print(f"Отправляем тестовое сообщение: {test_message}")
        
        success = bot.send_message(test_message)
        if success:
            print("✅ СООБЩЕНИЕ ОТПРАВЛЕНО УСПЕШНО!")
        else:
            print("❌ ОШИБКА ОТПРАВКИ СООБЩЕНИЯ")
            
        return success
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_telegram_sending()