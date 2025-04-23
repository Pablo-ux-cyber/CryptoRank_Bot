import asyncio
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

async def main():
    """Test connection to Telegram API and send a test message"""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Get bot info
        bot_info = await bot.get_me()
        print(f"Connected to Telegram as @{bot_info.username}")
        
        # Send a test message
        message = "🧪 Test message from test_telegram_v13.py script"
        result = await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=message,
            parse_mode=None
        )
        print(f"Message sent successfully to {TELEGRAM_CHANNEL_ID}")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Telegram API connection...")
    
    # Create an event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run the async function
    success = loop.run_until_complete(main())
    
    # Close the event loop
    loop.close()
    
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")