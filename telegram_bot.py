import asyncio
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from logger import logger

class TelegramBot:
    """
    Класс для работы с Telegram Bot API (версия 20.x)
    
    Эта версия использует асинхронное API и обертки для совместимости
    с существующим кодом, который ожидает синхронные методы.
    """
    
    def __init__(self):
        """Инициализировать бота с токеном из конфигурации"""
        self.token = TELEGRAM_BOT_TOKEN
        self.channel_id = TELEGRAM_CHANNEL_ID
        self.bot = None
        
        # Проверить наличие токена и ID канала
        if not self.token:
            logger.error("Не указан токен Telegram бота. Установите TELEGRAM_BOT_TOKEN.")
        
        if not self.channel_id:
            logger.error("Не указан ID канала/группы. Установите TELEGRAM_CHANNEL_ID.")
            logger.info("Примечание: TELEGRAM_CHANNEL_ID может быть @channel_name или ID группы")
        
        # Инициализировать бота
        self.bot = Bot(token=self.token)
        logger.info("Telegram bot initialized successfully")
    
    def _escape_markdown_v2(self, text):
        """
        Экранировать специальные символы для формата MarkdownV2
        
        Args:
            text (str): Текст для экранирования
            
        Returns:
            str: Экранированный текст
        """
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
            
        return text
    
    def send_message(self, message):
        """
        Отправить сообщение в указанный канал/группу Telegram
        
        Args:
            message (str): Текст сообщения
            
        Returns:
            bool: True если сообщение отправлено успешно, иначе False
        """
        async def _send_async():
            if not self.bot:
                logger.error("Telegram bot not initialized")
                return False
                
            try:
                chat_id = self.channel_id
                
                # Определить тип чата: канал или группа
                chat_type = "канал" if chat_id.startswith('@') else "группа"
                
                try:
                    # Попытка отправить с форматированием MarkdownV2
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="MarkdownV2"
                    )
                    logger.info(f"Сообщение отправлено в Telegram {chat_type}")
                    return True
                    
                except Exception as format_error:
                    # Если отправка с форматированием не удалась, отправляем без форматирования
                    logger.error(f"Ошибка отправки с MarkdownV2: {str(format_error)}")
                    logger.info("Попытка отправить сообщение без форматирования")
                    
                    try:
                        # Очистить текст от символов форматирования
                        clean_text = message.replace('\\', '')
                        clean_text = clean_text.replace('*', '')
                        clean_text = clean_text.replace('||', '')
                        clean_text = clean_text.replace('#', '')
                        clean_text = clean_text.replace('_', '')
                        
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=clean_text,
                            parse_mode=None
                        )
                        logger.info(f"Сообщение отправлено в Telegram {chat_type} (без форматирования)")
                        return True
                        
                    except Exception as e:
                        logger.error(f"Ошибка отправки без форматирования: {str(e)}")
                        logger.info(f"Сообщение, которое должно было быть отправлено: {message}")
                        return False
                
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения в Telegram: {str(e)}")
                logger.info(f"Сообщение, которое должно было быть отправлено: {message}")
                return False

        # Запустить асинхронную функцию
        try:
            return asyncio.run(_send_async())
        except Exception as e:
            logger.error(f"Ошибка в асинхронном выполнении: {str(e)}")
            return False
    
    def test_connection(self):
        """
        Тестирование соединения с Telegram API
        
        Returns:
            bool: True если соединение успешно, иначе False
        """
        async def _test_async():
            try:
                if not self.bot:
                    logger.error("Telegram bot not initialized")
                    return False
                
                me = await self.bot.get_me()
                logger.info(f"Connected to Telegram as @{me.username}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to Telegram: {str(e)}")
                return False
        
        try:
            return asyncio.run(_test_async())
        except Exception as e:
            logger.error(f"Error in async execution: {str(e)}")
            return False