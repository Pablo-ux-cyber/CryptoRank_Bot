#!/usr/bin/env python3
"""
Проверяем реальную отправку в телеграм - используем ту же логику что в /test-message
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def test_real_telegram():
    """Проверяем реальную отправку как в /test-message"""
    
    print("=== ТЕСТ РЕАЛЬНОЙ ОТПРАВКИ В ТЕЛЕГРАМ ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        from scheduler import SensorTowerScheduler
        scheduler = SensorTowerScheduler()
        
        print(f"📡 Telegram канал: {scheduler.telegram_bot.channel_id}")
        
        # Тестируем соединение
        connection_ok = scheduler.telegram_bot.test_connection()
        print(f"🔗 Соединение с Telegram: {'✅ OK' if connection_ok else '❌ ОШИБКА'}")
        
        if not connection_ok:
            print("❌ НЕТ СОЕДИНЕНИЯ С TELEGRAM - проверьте токен и канал")
            return False
        
        # Простое тестовое сообщение
        test_message = "🔼 Coinbase Appstore Rank: 139\n\nFear & Greed: 😏 Greed: 70/100\n🟢🟢🟢🟢🟢🟢🟢░░░"
        
        print(f"📤 Отправляем сообщение:\n{test_message}")
        
        # Отправляем через TelegramBotSync (как в планировщике)
        sent = scheduler.telegram_bot.send_message(test_message)
        
        if sent:
            print("🎯 ✅ СООБЩЕНИЕ УСПЕШНО ОТПРАВЛЕНО В ТЕЛЕГРАМ!")
            print("📱 Проверьте канал @telegrm_hub")
        else:
            print("❌ ОШИБКА ОТПРАВКИ В ТЕЛЕГРАМ")
            
        return sent
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_real_telegram()