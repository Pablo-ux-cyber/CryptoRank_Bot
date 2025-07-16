#!/usr/bin/env python3
"""
Отладка конфигурации Telegram
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

def debug_telegram_config():
    """Проверяем конфигурацию Telegram"""
    
    print("=== ОТЛАДКА КОНФИГУРАЦИИ TELEGRAM ===")
    
    try:
        from load_dotenv import load_dotenv
        load_dotenv()
        
        import os
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, TELEGRAM_TEST_CHANNEL_ID
        
        print(f"🔑 TELEGRAM_BOT_TOKEN: {'✅ ЕСТЬ' if TELEGRAM_BOT_TOKEN else '❌ НЕТ'}")
        print(f"📺 TELEGRAM_CHANNEL_ID: {TELEGRAM_CHANNEL_ID}")
        print(f"🧪 TELEGRAM_TEST_CHANNEL_ID: {TELEGRAM_TEST_CHANNEL_ID}")
        
        # Проверим переменные окружения напрямую
        print(f"\n🌍 Переменные окружения:")
        print(f"TELEGRAM_BOT_TOKEN: {'✅ ЕСТЬ' if os.environ.get('TELEGRAM_BOT_TOKEN') else '❌ НЕТ'}")
        print(f"TELEGRAM_CHANNEL_ID: {os.environ.get('TELEGRAM_CHANNEL_ID', 'НЕТ')}")
        print(f"TELEGRAM_TEST_CHANNEL_ID: {os.environ.get('TELEGRAM_TEST_CHANNEL_ID', 'НЕТ')}")
        
        if TELEGRAM_BOT_TOKEN:
            print(f"\n🔑 Токен начинается с: {TELEGRAM_BOT_TOKEN[:10]}...")
            
            # Проверим API напрямую
            import requests
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        bot_info = data.get('result', {})
                        print(f"✅ Бот работает: @{bot_info.get('username', 'неизвестно')}")
                        print(f"📝 Имя: {bot_info.get('first_name', 'неизвестно')}")
                    else:
                        print(f"❌ Ошибка API: {data.get('description', 'неизвестно')}")
                else:
                    print(f"❌ HTTP ошибка: {response.status_code}")
            except Exception as e:
                print(f"❌ Ошибка соединения: {str(e)}")
        
        # Проверим отправку в канал @telegrm_hub
        test_channel = "@telegrm_hub"
        print(f"\n📤 Тестируем отправку в {test_channel}")
        
        if TELEGRAM_BOT_TOKEN:
            import requests
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': test_channel,
                'text': '🧪 Тест отправки сообщения',
                'parse_mode': 'Markdown'
            }
            
            try:
                response = requests.post(url, data=data, timeout=10)
                result = response.json()
                
                if result.get('ok'):
                    print("✅ Сообщение отправлено успешно!")
                    message_id = result.get('result', {}).get('message_id')
                    print(f"📨 ID сообщения: {message_id}")
                else:
                    error_desc = result.get('description', 'неизвестно')
                    print(f"❌ Ошибка отправки: {error_desc}")
                    
                    if 'chat not found' in error_desc.lower():
                        print("💡 Возможно канал @telegrm_hub не существует или бот не добавлен")
                    elif 'not enough rights' in error_desc.lower():
                        print("💡 Бот не имеет прав для отправки в канал")
                        
            except Exception as e:
                print(f"❌ Ошибка запроса: {str(e)}")
                
    except Exception as e:
        print(f"❌ Общая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_telegram_config()