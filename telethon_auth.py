import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Берем API ID, API Hash и BOT Token из переменных окружения
api_id = int(os.environ.get('TELEGRAM_API_ID'))
api_hash = os.environ.get('TELEGRAM_API_HASH')
bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')

print(f"API ID: {api_id}")
print(f"API Hash exists: {'Yes' if api_hash else 'No'}")
print(f"Bot Token exists: {'Yes' if bot_token else 'No'}")

async def main():
    # Создаем клиент и подключаемся с использованием бот-токена
    client = TelegramClient('sensortower_session', api_id, api_hash)
    
    # Используем бот-токен вместо номера телефона
    await client.start(bot_token=bot_token)
    
    # Проверяем, что мы авторизованы
    if await client.is_user_authorized():
        print("Successfully authenticated with Telegram using bot token!")
        
        # Получаем информацию о текущем боте
        me = await client.get_me()
        print(f"Logged in as bot: {me.first_name} (ID: {me.id})")
        print(f"Username: @{me.username}")
        
        # Пробуем получить доступ к каналу @coinbaseappstore
        try:
            channel = await client.get_entity("coinbaseappstore")
            print(f"Successfully got channel: {channel.title}")
            
            # Получаем последние 5 сообщений
            messages = await client.get_messages(channel, limit=5)
            print(f"Got {len(messages)} messages from channel")
            
            for msg in messages:
                print(f"Message ID: {msg.id}, Date: {msg.date}")
                print(f"Text: {msg.text[:50]}..." if msg.text else "No text")
                print("-" * 30)
                
        except Exception as e:
            print(f"Error accessing channel: {str(e)}")
            print("This might be because bots cannot access channels where they are not admins.")
            print("Let's try accessing the bot admin's chat instead:")
            
            try:
                # Получаем список всех диалогов бота
                dialogs = await client.get_dialogs()
                print(f"Bot has access to {len(dialogs)} dialogs/chats")
                
                for dialog in dialogs[:5]:  # показываем только первые 5
                    print(f"Dialog: {dialog.name} (ID: {dialog.id})")
            except Exception as e2:
                print(f"Error accessing dialogs: {str(e2)}")
    else:
        print("Failed to authenticate with Telegram")
    
    # Отключаемся
    await client.disconnect()
    print("Disconnected from Telegram")

# Запускаем асинхронную функцию
asyncio.run(main())