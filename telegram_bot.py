import telegram
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
            self.bot = telegram.Bot(token=self.token)
            logger.info("Telegram bot initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {str(e)}")
            return False
    
    def send_message_to_bot_admin(self, message):
        """
        Send a message to the bot administrator's private chat
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
            updates = self.bot.get_updates()
            admin_id = None
            
            # Look for the first private chat in updates
            for update in updates:
                if update.message and update.message.chat.type == 'private':
                    admin_id = update.message.chat.id
                    break
                    
            if admin_id:
                logger.info(f"Sending message to admin ID: {admin_id}")
                self.bot.send_message(
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
            
        Note:
            This method supports sending to both channels (@channel_name) and
            groups (using group chat ID like -1001234567890). The ID should be
            provided in the TELEGRAM_CHANNEL_ID environment variable.
        """
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        # Make sure we have a chat ID (channel or group)
        if not self.channel_id:
            logger.error("Telegram chat ID not provided")
            # If chat is not specified, try to send message to the bot admin
            logger.info("Attempting to send message to bot admin instead")
            return self.send_message_to_bot_admin(message)
            
        # Log message content for debugging
        logger.info(f"Message content to send: {message[:100]}...") # First 100 chars
            
        try:
            # Verify chat exists
            chat_id = self.channel_id
            # Check chat ID format
            if not (chat_id.startswith('@') or chat_id.startswith('-') or chat_id.isdigit()):
                chat_id = '@' + chat_id
            
            # Determine chat type based on ID
            chat_type = "group" if chat_id.startswith('-') else "channel"
            logger.info(f"Attempting to send message to Telegram {chat_type}: {chat_id}")
            
            # MODIFIED: Ensure all special characters are properly escaped
            # We do this here as a final step to make sure everything is properly formatted
            escaped_message = message
            for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
                # Replace all occurrences of the character, even if already escaped
                escaped_message = escaped_message.replace(f"\\{char}", f"TEMP_ESCAPED_{char}")  # Temporarily mark already escaped chars
                escaped_message = escaped_message.replace(char, f"\\{char}")  # Escape all instances
                escaped_message = escaped_message.replace(f"TEMP_ESCAPED_{char}", f"\\{char}")  # Restore properly escaped chars
            
            try:
                # Send message with MarkdownV2 formatting with properly escaped characters
                self.bot.send_message(
                    chat_id=chat_id,
                    text=escaped_message,
                    parse_mode="MarkdownV2"
                )
                logger.info(f"Message sent to Telegram {chat_type} successfully with MarkdownV2")
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
                    
                    self.bot.send_message(
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
                    return self.send_message_to_bot_admin(message)
                
        except Exception as e:
            logger.error(f"Failed to send message to Telegram chat: {str(e)}")
            # In case of error, try to send message to admin
            return self.send_message_to_bot_admin(message)

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
