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
            
        self.initialize_bot()
    
    def initialize_bot(self):
        """Initialize the Telegram bot"""
        try:
            self.bot = Bot(token=self.token)
            # Run a quick test to ensure the bot is working
            asyncio.run(self._test_bot_async())
            logger.info("Telegram bot initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {str(e)}")
            return False
    
    async def _test_bot_async(self):
        """Test the bot connection asynchronously"""
        await self.bot.get_me()
    
    async def _send_message_to_bot_admin_async(self, message):
        """
        Send a message to the bot administrator's private chat asynchronously
        This is useful for testing without a proper channel
        
        Args:
            message (str): The message to send
        
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False
            
        try:
            # First try to get updates to find the admin ID
            updates = await self.bot.get_updates()
            admin_id = None
            
            # Look for the first private chat in updates
            for update in updates:
                if update.message and update.message.chat.type == 'private':
                    admin_id = update.message.chat.id
                    break
                    
            if admin_id:
                logger.info(f"Sending message to admin ID: {admin_id}")
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode=None
                )
                logger.info("Message sent to admin successfully")
                return True
            else:
                logger.error("Could not find admin ID. Send a message to the bot first.")
                # Log the message as a fallback
                logger.info(f"Message that would be sent: {message}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send message to admin: {str(e)}")
            # Log the message as a fallback
            logger.info(f"Message that would be sent: {message}")
            return False
            
    def send_message_to_bot_admin(self, message):
        """Synchronous wrapper for _send_message_to_bot_admin_async"""
        return asyncio.run(self._send_message_to_bot_admin_async(message))
    
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
    
    async def _send_message_async(self, message):
        """
        Send a message to the designated Telegram channel or group asynchronously
        
        Args:
            message (str): The message to send
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
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
                    # If this also fails, send to admin
                    logger.info("Attempting to send message to bot admin instead")
                    return await self._send_message_to_bot_admin_async(message)
                
        except Exception as e:
            logger.error(f"Failed to send message to Telegram chat: {str(e)}")
            # In case of error, try to send message to admin
            return await self._send_message_to_bot_admin_async(message)
    
    def send_message(self, message):
        """Synchronous wrapper for _send_message_async"""
        return asyncio.run(self._send_message_async(message))
        
    async def _test_connection_async(self):
        """
        Test the connection to the Telegram API asynchronously
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        try:
            me = await self.bot.get_me()
            logger.info(f"Connected to Telegram as {me.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {str(e)}")
            return False
            
    def test_connection(self):
        """Synchronous wrapper for _test_connection_async"""
        return asyncio.run(self._test_connection_async())