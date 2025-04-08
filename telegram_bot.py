import telegram
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from logger import logger

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.channel_id = TELEGRAM_CHANNEL_ID
        self.bot = None
        
        self.initialize_bot()
    
    def initialize_bot(self):
        """Initialize the Telegram bot"""
        try:
            self.bot = telegram.Bot(token=self.token)
            logger.info("Telegram bot initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {str(e)}")
            return False
    
    def send_message(self, message):
        """
        Send a message to the designated Telegram channel
        
        Args:
            message (str): The message to send
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        try:
            self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info("Message sent to Telegram channel successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to Telegram channel: {str(e)}")
            return False

    def test_connection(self):
        """
        Test the connection to the Telegram API
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        try:
            me = self.bot.get_me()
            logger.info(f"Connected to Telegram as {me.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {str(e)}")
            return False
