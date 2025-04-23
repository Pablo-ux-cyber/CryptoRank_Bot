import asyncio
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from logger import logger

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.channel_id = TELEGRAM_CHANNEL_ID
        self.bot = None
        
        # Check if token and chat ID (channel or group) are provided
        if not self.token:
            logger.error("Telegram bot token not provided. Please set TELEGRAM_BOT_TOKEN environment variable.")
        
        if not self.channel_id:
            logger.error("Telegram chat ID not provided. Please set TELEGRAM_CHANNEL_ID environment variable.")
            logger.info("Note: TELEGRAM_CHANNEL_ID can be a channel (@channel_name) or a group chat ID (-1001234567890)")
        
        # Initialize bot without async test
        self.bot = Bot(token=self.token)
        logger.info("Telegram bot initialized successfully")
    
    def _escape_markdown_v2(self, text):
        """
        Escape special characters for MarkdownV2 format
        
        Args:
            text (str): Text to escape
            
        Returns:
            str: Escaped text
        """
        # List of special characters that need to be escaped in MarkdownV2
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        # Escape each special character
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
            
        return text
    
    def send_message(self, message):
        """
        Send a message to the designated Telegram channel or group
        
        Args:
            message (str): The message to send
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        async def _send_async():
            if not self.bot:
                logger.error("Telegram bot not initialized")
                return False
                
            try:
                chat_id = self.channel_id
                
                # Determine if the target is a channel or group
                chat_type = "channel" if chat_id.startswith('@') else "group"
                
                try:
                    # Try to send with MarkdownV2 formatting
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="MarkdownV2"
                    )
                    logger.info(f"Message sent to Telegram {chat_type} successfully")
                    return True
                    
                except Exception as chat_error:
                    # If sending to chat fails, try again without formatting
                    logger.error(f"Failed to send to {chat_type} with MarkdownV2: {str(chat_error)}")
                    logger.info("Attempting to send message without formatting")
                    
                    try:
                        # Send plain text without formatting
                        # Remove all Markdown formatting symbols
                        clean_text = message.replace('\\', '')  # Remove escaping
                        clean_text = clean_text.replace('*', '')  # Remove asterisks
                        clean_text = clean_text.replace('||', '')  # Remove spoiler tags
                        clean_text = clean_text.replace('#', '')  # Remove hashtags
                        clean_text = clean_text.replace('_', '')  # Remove underscores
                        
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=clean_text,
                            parse_mode=None
                        )
                        logger.info(f"Message sent to Telegram {chat_type} successfully (without formatting)")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to send plain text: {str(e)}")
                        # If this also fails, log the error
                        logger.info(f"Message that would be sent: {message}")
                        return False
                    
            except Exception as e:
                logger.error(f"Failed to send message to Telegram chat: {str(e)}")
                # Log the message
                logger.info(f"Message that would be sent: {message}")
                return False

        # Run the async function
        try:
            return asyncio.run(_send_async())
        except Exception as e:
            logger.error(f"Error in async execution: {str(e)}")
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
        
        async def _test_async():
            try:
                me = await self.bot.get_me()
                username = getattr(me, 'username', 'unknown')
                logger.info(f"Connected to Telegram as {username}")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to Telegram: {str(e)}")
                return False
        
        try:
            return asyncio.run(_test_async())
        except Exception as e:
            logger.error(f"Error in async execution: {str(e)}")
            return False