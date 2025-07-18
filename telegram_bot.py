import asyncio
import io
import base64
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
        # Эмодзи, которые нужно сохранить без изменений
        emojis = ["🔼", "🔽", "🟢", "🟡", "⚪", "🔴", "🔵"]
        
        # Временно заменяем эмодзи на маркеры
        for i, emoji in enumerate(emojis):
            text = text.replace(emoji, f"__EMOJI_{i}__")
        
        # Экранируем специальные символы
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        
        # Возвращаем эмодзи на место
        for i, emoji in enumerate(emojis):
            text = text.replace(f"__EMOJI_{i}__", emoji)
            
        return text
    
    def _get_event_loop(self):
        """
        Получить существующий event loop или создать новый для многопоточности
        
        Returns:
            asyncio.AbstractEventLoop: Активный event loop
        """
        try:
            # ИСПРАВЛЕНИЕ: Для планировщика в отдельном потоке - всегда новый loop
            import threading
            current_thread = threading.current_thread()
            logger.info(f"ИСПРАВЛЕНИЕ: Создаём event loop для потока {current_thread.name}")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
        except Exception as e:
            logger.error(f"ИСПРАВЛЕНИЕ: Ошибка создания event loop: {str(e)}")
            return None
    
    def send_message(self, message, parse_mode=None):
        """
        Отправить сообщение в указанный канал/группу Telegram
        
        Args:
            message (str): Текст сообщения
            parse_mode (str): Режим парсинга ('Markdown', 'HTML', None)
            
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
                    # Отправляем с указанным форматированием
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    )
                    logger.info(f"Сообщение отправлено в Telegram {chat_type}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения: {str(e)}")
                    
                    try:
                        # Очистить текст от любых возможных форматирующих символов, но сохранить эмодзи
                        clean_text = message.replace('\\', '')
                        clean_text = clean_text.replace('*', '')
                        clean_text = clean_text.replace('||', '')
                        clean_text = clean_text.replace('#', '')
                        clean_text = clean_text.replace('_', '')
                        
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=clean_text,
                            parse_mode=None,
                            disable_web_page_preview=True
                        )
                        logger.info(f"Сообщение отправлено в Telegram {chat_type} (очищенный текст)")
                        return True
                        
                    except Exception as e:
                        logger.error(f"Ошибка отправки без форматирования: {str(e)}")
                        logger.info(f"Сообщение, которое должно было быть отправлено: {message}")
                        return False
                
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения в Telegram: {str(e)}")
                logger.info(f"Сообщение, которое должно было быть отправлено: {message}")
                return False

        # Создаем новый event loop для threading безопасности
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(_send_async())
                return result
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {str(e)}")
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
        
        # Создаем новый event loop для threading безопасности
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(_test_async())
                return result
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error in async execution: {str(e)}")
            return False
    
    def send_photo(self, image_data, caption=None):
        """
        Отправить изображение в указанный канал/группу Telegram
        
        Args:
            image_data (bytes): Данные изображения в формате bytes
            caption (str, optional): Подпись к изображению
            
        Returns:
            bool: True если изображение отправлено успешно, иначе False
        """
        async def _send_photo_async():
            if not self.bot:
                logger.error("Telegram bot not initialized")
                return False
                
            try:
                chat_id = self.channel_id
                
                # Создаем объект файла из байтов
                photo_file = io.BytesIO(image_data)
                photo_file.name = 'market_chart.png'
                
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode=None
                )
                logger.info(f"Изображение отправлено в Telegram")
                return True
                    
            except Exception as e:
                logger.error(f"Ошибка отправки изображения в Telegram: {str(e)}")
                return False

        # Запустить асинхронную функцию в существующем или новом event loop
        loop = self._get_event_loop()
        if not loop:
            logger.error("Не удалось получить event loop для отправки изображения")
            return False
            
        try:
            return loop.run_until_complete(_send_photo_async())
        except Exception as e:
            logger.error(f"Ошибка в асинхронном выполнении отправки изображения: {str(e)}")
            return False

    def send_photo_url(self, photo_url, caption=None):
        """
        Отправить изображение по URL в указанный канал/группу Telegram
        
        Args:
            photo_url (str): URL изображения
            caption (str, optional): Подпись к изображению
            
        Returns:
            bool: True если изображение отправлено успешно, иначе False
        """
        async def _send_photo_url_async():
            if not self.bot:
                logger.error("Telegram bot not initialized")
                return False
                
            try:
                chat_id = self.channel_id
                
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_url,
                    caption=caption,
                    parse_mode=None
                )
                logger.info(f"Изображение по URL отправлено в Telegram")
                return True
                    
            except Exception as e:
                logger.error(f"Ошибка отправки изображения по URL в Telegram: {str(e)}")
                return False

        # Запустить асинхронную функцию в существующем или новом event loop
        loop = self._get_event_loop()
        if not loop:
            logger.error("Не удалось получить event loop для отправки изображения по URL")
            return False
            
        try:
            return loop.run_until_complete(_send_photo_url_async())
        except Exception as e:
            logger.error(f"Ошибка в асинхронном выполнении отправки изображения по URL: {str(e)}")
            return False