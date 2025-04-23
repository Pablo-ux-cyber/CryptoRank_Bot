import os
import re
import logging
from datetime import datetime

from telethon import TelegramClient, sync
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import Channel, Message
from logger import logger

class SensorTowerScraper:
    def __init__(self):
        # Используем API ID и API Hash для Telegram
        # Их можно получить на https://my.telegram.org/
        # Для реального использования нужно использовать свои креденшиалы
        self.api_id = int(os.environ.get('TELEGRAM_API_ID', 0))
        self.api_hash = os.environ.get('TELEGRAM_API_HASH', '')
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        
        self.channel_name = "@coinbaseappstore"  # Имя канала без @
        self.last_scrape_data = None
        
        # Инициализация Telethon клиента
        self.client = None
        
    async def _init_telethon_client(self):
        """
        Инициализирует клиент Telethon, если он еще не инициализирован
        
        Returns:
            bool: True если клиент был успешно инициализирован, False в противном случае
        """
        if self.client is not None and self.client.is_connected():
            return True
        
        if self.api_id == 0 or not self.api_hash:
            logger.error("Missing Telegram API credentials. Cannot initialize Telethon client.")
            return False
        
        try:
            # Используем сессию 'sensortower' для хранения данных аутентификации
            self.client = TelegramClient('sensortower_session', self.api_id, self.api_hash)
            await self.client.start()
            
            if not self.client.is_connected():
                logger.error("Failed to connect to Telegram with Telethon.")
                return False
                
            logger.info("Successfully connected to Telegram with Telethon")
            return True
        except Exception as e:
            logger.error(f"Error initializing Telethon client: {str(e)}")
            return False
            
    async def _get_messages_from_telegram(self):
        """
        Получает последние сообщения из Telegram канала через API
        
        Returns:
            list: Список недавних сообщений из канала
        """
        if not await self._init_telethon_client():
            logger.error("Telethon client not initialized. Cannot get messages.")
            return []
            
        try:
            # Получаем объект канала
            channel = await self.client.get_entity(self.channel_name)
            
            if not isinstance(channel, Channel):
                logger.error(f"{self.channel_name} is not a valid channel.")
                return []
                
            logger.info(f"Successfully connected to channel: {self.channel_name}")
            
            # Получаем последние 20 сообщений
            messages = await self.client.get_messages(channel, limit=20)
            
            if not messages:
                logger.warning(f"No messages found in channel {self.channel_name}")
                return []
                
            return messages
        except Exception as e:
            logger.error(f"Error getting messages from Telegram: {str(e)}")
            return []
            
    def _extract_ranking_from_message(self, message):
        """
        Извлекает данные о рейтинге из сообщения Telegram
        
        Args:
            message (Message): Объект сообщения Telethon
            
        Returns:
            int or None: Значение рейтинга или None если извлечение не удалось
        """
        if not message or not message.text:
            return None
            
        # Список паттернов для извлечения рейтинга
        patterns = [
            r"Coinbase Rank:\s*(\d+)",  # Coinbase Rank: 123
            r"Rank:\s*(\d+)",           # Rank: 123
            r"#(\d+)"                   # #123
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, message.text, re.IGNORECASE)
            if match:
                rank = match.group(1)
                logger.info(f"Extracted ranking using pattern {i}: {rank}")
                return int(rank)
                
        return None
        
    def _create_test_data(self):
        """
        Создает базовую структуру данных с фиксированным значением рейтинга,
        когда не удается получить реальные данные из Telegram
        
        Returns:
            dict: Словарь с данными
        """
        logger.warning("Creating fallback test data because real data could not be fetched")
        return {
            "timestamp": datetime.now().isoformat(),
            "categories": [
                {
                    "category": "Finance",
                    "rank": 350,  # Fallback value
                    "trend": "unknown"
                }
            ],
            "app_info": {
                "name": "Coinbase",
                "developer": "Coinbase, Inc.",
                "apple_id": "886427730"
            },
            "is_fallback_data": True
        }
        
    async def scrape_category_rankings(self):
        """
        Скрапит данные о рейтинге категорий из Telegram канала @coinbaseappstore
        
        Returns:
            dict: Словарь, содержащий данные о рейтинге
        """
        logger.info(f"Attempting to get ranking data from Telegram channel: {self.channel_name}")
        
        try:
            messages = await self._get_messages_from_telegram()
            
            if not messages:
                logger.error("Failed to get messages from Telegram. Using fallback data.")
                self.last_scrape_data = self._create_test_data()
                return self.last_scrape_data
                
            # Фильтруем сообщения, содержащие информацию о рейтинге
            coinbase_rank_messages = []
            for msg in messages:
                if msg.text and ("Coinbase Rank" in msg.text or "Rank:" in msg.text):
                    coinbase_rank_messages.append(msg)
                    logger.info(f"Message {len(coinbase_rank_messages)}: [ID: {msg.id}] {msg.text[:30]}...")
                    
            logger.info(f"After filtering for 'Coinbase Rank', found {len(coinbase_rank_messages)} relevant messages")
            
            if not coinbase_rank_messages:
                logger.error("No messages with ranking information found. Using fallback data.")
                self.last_scrape_data = self._create_test_data()
                return self.last_scrape_data
                
            # Получаем самое свежее сообщение с рейтингом
            latest_msg = coinbase_rank_messages[0]  # Сообщения уже отсортированы от новых к старым
            logger.info(f"Checking most recent message for ranking...")
            
            rank = self._extract_ranking_from_message(latest_msg)
            
            if rank:
                logger.info(f"Found ranking in the most recent message: {rank}")
                
                # Формируем структуру данных
                self.last_scrape_data = {
                    "timestamp": latest_msg.date.isoformat() if hasattr(latest_msg, 'date') else datetime.now().isoformat(),
                    "categories": [
                        {
                            "category": "Finance",
                            "rank": rank,
                            "trend": "unknown"  # Будет определено внешним кодом
                        }
                    ],
                    "app_info": {
                        "name": "Coinbase",
                        "developer": "Coinbase, Inc.",
                        "apple_id": "886427730"
                    },
                    "is_fallback_data": False
                }
                
                logger.info(f"Successfully scraped ranking from Telegram: {rank}")
                return self.last_scrape_data
            else:
                logger.error("Failed to extract ranking from messages. Using fallback data.")
                self.last_scrape_data = self._create_test_data()
                return self.last_scrape_data
                
        except Exception as e:
            logger.error(f"Error during Telegram scraping: {str(e)}")
            self.last_scrape_data = self._create_test_data()
            return self.last_scrape_data
            
    def format_rankings_message(self, rankings_data):
        """
        Форматирует данные о рейтинге в читаемое сообщение для Telegram
        
        Args:
            rankings_data (dict): Данные о рейтинге
            
        Returns:
            str: Отформатированное сообщение для Telegram
        """
        if not rankings_data or "categories" not in rankings_data or not rankings_data["categories"]:
            return "❌ Error: No ranking data available."
            
        # Получаем базовую информацию
        rank = rankings_data["categories"][0]["rank"]
        
        # Создаем базовое сообщение
        message = f"Coinbase Appstore Rank: {rank}"
        
        # Если доступна информация о тренде, добавляем ее
        if "trend" in rankings_data:
            prev_rank = rankings_data["trend"].get("previous", "N/A")
            trend_dir = rankings_data["trend"].get("direction", "unknown")
            
            if trend_dir == "up":
                message = f"🔼 {message}\n(Improved from {prev_rank})"
            elif trend_dir == "down":
                message = f"🔽 {message}\n(Dropped from {prev_rank})"
                
        # Если это резервные данные, указываем это
        if rankings_data.get("is_fallback_data", False):
            message += "\n⚠️ Note: This is fallback data, actual ranking might differ."
            
        return message
            
    async def close(self):
        """
        Закрывает соединение с Telegram
        """
        if self.client and self.client.is_connected():
            await self.client.disconnect()
            logger.info("Telethon client disconnected.")