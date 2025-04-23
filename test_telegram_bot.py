import asyncio
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from logger import setup_logger

# Setup logger
logger = setup_logger()

async def test_telegram_api():
    """Test connection to Telegram API and send a test message"""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        me = await bot.get_me()
        logger.info(f"Connected to Telegram as {me.username}")
        
        # Send a test message
        message = "🧪 Test message from test_telegram_bot.py script"
        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=message,
            parse_mode=None
        )
        logger.info(f"Test message sent to {TELEGRAM_CHANNEL_ID}")
        return True
    except Exception as e:
        logger.error(f"Error in Telegram API test: {e}")
        return False

if __name__ == "__main__":
    print("Testing Telegram API connection...")
    result = asyncio.run(test_telegram_api())
    if result:
        print("✅ Test successful! Check your Telegram channel for the test message.")
    else:
        print("❌ Test failed. Check the logs for details.")