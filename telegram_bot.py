import telegram
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from logger import logger

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.channel_id = TELEGRAM_CHANNEL_ID
        self.bot = None
        
        # Проверяем, есть ли токен и ID чата (канал или группа)
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
            # Сначала попробуем получить обновления, чтобы найти ID администратора
            updates = self.bot.get_updates()
            admin_id = None
            
            # Ищем первый private чат в обновлениях
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
                # В качестве запасного варианта логируем сообщение
                logger.info(f"Message that would be sent: {message}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send message to admin: {str(e)}")
            # В качестве запасного варианта логируем сообщение
            logger.info(f"Message that would be sent: {message}")
            return False
    
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
            # Если чат не указан, попробуем отправить сообщение администратору бота
            logger.info("Attempting to send message to bot admin instead")
            return self.send_message_to_bot_admin(message)
            
        # Для отладки вывести сообщение в лог
        logger.info(f"Message content to send: {message[:100]}...") # First 100 chars
            
        try:
            # Проверяем, что чат существует
            chat_id = self.channel_id
            # Проверяем формат ID чата
            if not (chat_id.startswith('@') or chat_id.startswith('-') or chat_id.isdigit()):
                chat_id = '@' + chat_id
            
            # Определяем тип чата по ID
            chat_type = "group" if chat_id.startswith('-') else "channel"
            logger.info(f"Attempting to send message to Telegram {chat_type}: {chat_id}")
            
            try:
                # Сначала попробуем отправить обычный текст без форматирования
                self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=None
                )
                logger.info(f"Message sent to Telegram {chat_type} successfully")
                return True
            except Exception as chat_error:
                # Если отправка в чат не удалась, попробуем отправить администратору
                logger.error(f"Failed to send to {chat_type}: {str(chat_error)}")
                logger.info("Attempting to send message to bot admin instead")
                return self.send_message_to_bot_admin(message)
                
        except Exception as e:
            logger.error(f"Failed to send message to Telegram chat: {str(e)}")
            # В случае ошибки попробуем отправить сообщение администратору
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
