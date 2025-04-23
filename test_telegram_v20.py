import asyncio
import logging
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

# Setup basic logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Test the latest version of python-telegram-bot (v20.x)"""
    print(f"Testing connection to Telegram using token: {TELEGRAM_BOT_TOKEN[:6]}...")
    print(f"Target channel/group: {TELEGRAM_CHANNEL_ID}")
    
    try:
        # Create bot
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Get bot info
        bot_info = await bot.get_me()
        print(f"✓ Bot connected: @{bot_info.username}")
        
        # Send a test message
        message = (
            "🧪 Test message from v20 API\n\n"
            "Testing the latest python-telegram-bot library (v20.7)"
        )
        
        sent_message = await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=message,
            disable_notification=False
        )
        
        print(f"✓ Message sent successfully (message_id: {sent_message.message_id})")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("====== Telegram API Test (v20.x) ======")
    result = asyncio.run(main())
    
    if result:
        print("✓ Test completed successfully!")
    else:
        print("❌ Test failed!")
    print("=======================================")