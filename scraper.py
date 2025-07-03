import time
import requests
import trafilatura
import re
import os
from datetime import datetime

from config import APP_ID, TELEGRAM_SOURCE_CHANNEL
from logger import logger
from sensortower_api import SensorTowerParser
from json_rank_reader import get_rank_from_json, get_latest_rank_date

class SensorTowerScraper:
    def __init__(self):
        self.app_id = APP_ID
        self.last_scrape_data = None
        self.telegram_source_channel = TELEGRAM_SOURCE_CHANNEL  # Channel where we get data from
        self.limit = 10  # Number of recent messages to check
        self.previous_rank = None  # Will be initialized with first value obtained
        self.sensortower_api = SensorTowerParser()  # API парсер для SensorTower
        
        # Попытка загрузить последний рейтинг из файла истории
        try:
            history_file = "/tmp/coinbasebot_rank_history.txt"
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    saved_rank = f.read().strip()
                    if saved_rank and saved_rank.isdigit():
                        self.previous_rank = int(saved_rank)
                        logger.info(f"Загружен предыдущий рейтинг из файла истории: {self.previous_rank}")
        except Exception as e:
            logger.error(f"Ошибка при чтении файла истории рейтинга в scraper: {str(e)}")

    def _get_messages_from_telegram(self):
        """
        Gets the latest messages from Telegram channel via web interface
        
        Returns:
            list: List of recent messages from the channel
        """
        try:
            # Since we don't have admin rights in the channel, we can't use Bot API
            # Instead, we'll parse the public web version of the channel
            
            channel_username = self.telegram_source_channel.replace("@", "")
            url = f"https://t.me/s/{channel_username}"
            
            logger.info(f"Attempting to scrape web version of channel: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            }
            
            try:
                # New request with additional headers to prevent caching
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch channel web page: HTTP {response.status_code}")
                    return None
                
                html_content = response.text
                
                # For debugging, let's search specifically for a message with ranking 240
                if "240" in html_content and "Coinbase Rank: 240" in html_content:
                    logger.info("Found string 'Coinbase Rank: 240' in the raw HTML!")
                
                # Check for the presence of message with ID 510 (which contains ranking 240)
                if "coinbaseappstore/510" in html_content:
                    logger.info("Found message with ID 510 (should contain rank 240)")
                
                # First, try to find the message through the unique identifier we saw in curl
                # <div ... data-post="coinbaseappstore/510" ... >
                messages = []
                
                # New approach: extract all message blocks completely and search for ranking text in them
                # Find all message blocks
                blocks = re.findall(r'<div class="tgme_widget_message[^"]*"[^>]*?data-post="coinbaseappstore/(\d+)".*?>(.*?)<div class="tgme_widget_message_footer', html_content, re.DOTALL)
                
                # Create a dictionary where key is message ID, value is message text
                messages_dict = {}
                
                for msg_id, block_html in blocks:
                    # Extract message text
                    text_match = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', block_html, re.DOTALL)
                    
                    if text_match:
                        text_html = text_match.group(1)
                        # Clean HTML tags
                        clean_text = re.sub(r'<[^>]+>', ' ', text_html)
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                        
                        if clean_text:
                            # Save message to dictionary with ID as key
                            messages_dict[int(msg_id)] = f"[ID: {msg_id}] {clean_text}"
                            
                            # Log for debugging if we find message with ID 510
                            if msg_id == "510":
                                logger.info(f"Content of message 510: {clean_text}")
                
                if messages_dict:
                    # Sort messages by ID in descending order (newest to oldest)
                    sorted_ids = sorted(messages_dict.keys(), reverse=True)
                    messages = [messages_dict[msg_id] for msg_id in sorted_ids]
                    
                    logger.info(f"Found {len(messages)} messages with IDs")
                    
                    # For debugging, print the first 3 messages
                    for i, msg in enumerate(messages[:3]):
                        logger.info(f"Message {i+1}: {msg[:50]}...")
                    
                    # Filter only messages containing "Coinbase Rank"
                    # This protects against ads and other irrelevant messages in the channel
                    filtered_messages = [msg for msg in messages if "Coinbase Rank" in msg]
                    
                    if filtered_messages:
                        logger.info(f"After filtering for 'Coinbase Rank', found {len(filtered_messages)} relevant messages")
                        return filtered_messages
                    else:
                        # If no messages with Coinbase Rank, return all messages as fallback
                        logger.warning("No messages containing 'Coinbase Rank' found, using all messages")
                        return messages
                
                # If direct search didn't work, use fallback method
                if not messages:
                    logger.info("Using fallback method to extract messages...")
                    # Simply search for all message texts
                    all_texts = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', html_content, re.DOTALL)
                    
                    for text_html in all_texts:
                        clean_text = re.sub(r'<[^>]+>', ' ', text_html)
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                        if clean_text:
                            messages.append(clean_text)
                    
                    if messages:
                        logger.info(f"Found {len(messages)} message texts using fallback method")
                        return messages
                
                # If all methods failed, try using trafilatura
                if not messages:
                    text_content = trafilatura.extract(html_content)
                    if text_content:
                        # Split into paragraphs
                        paragraphs = re.split(r'\n+', text_content)
                        messages = [p.strip() for p in paragraphs if p.strip()]
                        logger.info(f"Extracted {len(messages)} paragraphs using trafilatura")
                        return messages
                
                return []
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting messages from Telegram web: {str(e)}")
            return None
    
    def _extract_ranking_from_message(self, message):
        """
        Extracts ranking data from a Telegram message
        
        Args:
            message (str): Message text from Telegram
            
        Returns:
            int or None: Ranking value or None if extraction failed
        """
        try:
            if not message:
                return None
                
            # Try to find different patterns of ranking mentions in the message
            
            # Pattern 0 (main): "Coinbase Rank: X" (channel @coinbaseappstore)
            pattern0 = r"Coinbase Rank:?\s*(\d+)"
            match = re.search(pattern0, message, re.IGNORECASE)
            
            if match:
                rank = int(match.group(1))
                logger.info(f"Extracted ranking using pattern 0 (Coinbase Rank): {rank}")
                return rank
            
            # Pattern 1: Current position: X (English)
            pattern1 = r"Current position:?\s*\*?(\d+)\*?"
            match = re.search(pattern1, message)
            
            if match:
                rank = int(match.group(1))
                logger.info(f"Extracted ranking using pattern 1: {rank}")
                return rank
            
            # Pattern 2: Current place: X (English)
            pattern2 = r"Current place:?\s*\*?(\d+)\*?"
            match = re.search(pattern2, message)
            
            if match:
                rank = int(match.group(1))
                logger.info(f"Extracted ranking using pattern 2: {rank}")
                return rank
            
            # Pattern 3: Rank: X or Position: X (English only)
            pattern3 = r"(?:Rank|Position):?\s*\*?#?(\d+)\*?"
            match = re.search(pattern3, message, re.IGNORECASE)
            
            if match:
                rank = int(match.group(1))
                logger.info(f"Extracted ranking using pattern 3: {rank}")
                return rank
            
            # Pattern 4: Looking for a number with a hashtag (#123)
            pattern4 = r"#(\d+)"
            match = re.search(pattern4, message)
            
            if match:
                rank = int(match.group(1))
                logger.info(f"Extracted ranking using pattern 4: {rank}")
                return rank
            
            # Pattern 5: Just a number in a short message (if nothing else exists)
            if len(message.strip().split()) <= 3:
                pattern5 = r"(\d+)"
                match = re.search(pattern5, message)
                
                if match:
                    rank = int(match.group(1))
                    logger.info(f"Extracted ranking using pattern 5 (simple number): {rank}")
                    return rank
            
            logger.warning(f"Could not extract ranking from message: {message[:100]}...")
            return None
        except Exception as e:
            logger.error(f"Error extracting ranking: {str(e)}")
            return None
    
    def _create_test_data(self):
        """
        Creates a basic data structure with a fixed ranking value
        when unable to get real data from Telegram
        
        Returns:
            dict: Dictionary with data
        """
        app_name = "Coinbase"
        rank = "350"  # Fixed value
        date = time.strftime("%Y-%m-%d")
        
        logger.info(f"Creating data structure with fixed ranking value: {rank}")
        
        rankings_data = {
            "app_name": app_name,
            "app_id": self.app_id,
            "date": date,
            "categories": [
                {"category": "US - iPhone - Top Free", "rank": rank}
            ]
        }
        
        return rankings_data
    
    def scrape_category_rankings(self):
        """
        Scrape the category rankings data from Telegram channel @coinbaseappstore
        
        Returns:
            dict: A dictionary containing the scraped rankings data
        """
        # Простая логика: сначала пробуем SensorTower API, если не работает - используем 300
        logger.info("Attempting to get ranking data from SensorTower API")
        
        rank = None
        
        try:
            # Проверяем ручную корректировку
            test_rank_file = "manual_rank.txt"
            if os.path.exists(test_rank_file):
                with open(test_rank_file, "r") as f:
                    manual_rank = f.read().strip()
                    if manual_rank and manual_rank.isdigit():
                        rank = int(manual_rank)
                        logger.info(f"Using manual rank from file: {rank}")
                        os.remove(test_rank_file)
            
            # Если нет ручной корректировки, пробуем JSON файл
            if rank is None:
                json_rank = get_rank_from_json()
                if json_rank is not None:
                    rank = json_rank
                    logger.info(f"Successfully got rank from JSON file: {rank}")
                else:
                    # В крайнем случае пробуем SensorTower API (для обратной совместимости)
                    logger.info("JSON file has no data, trying SensorTower API")
                    api_rank = self.sensortower_api.get_current_rank()
                    if api_rank is not None:
                        rank = api_rank
                        logger.info(f"Successfully got rank from SensorTower API: {rank}")
                    else:
                        logger.warning("All data sources returned no data - no rank available")
                        return None  # Возвращаем None если нет данных
            
            # Create data structure with obtained or fixed ranking
            app_name = "Coinbase"
            
            rankings_data = {
                "app_name": app_name,
                "app_id": self.app_id,
                "date": time.strftime("%Y-%m-%d"),
                "categories": [
                    {"category": "US - iPhone - Top Free", "rank": str(rank)}
                ]
            }
            
            # Добавить данные о тренде, сравнив с предыдущим значением
            current_rank_int = int(rank)
            
            if self.previous_rank is None:
                self.previous_rank = current_rank_int
                rankings_data["trend"] = {"direction": "same", "previous": current_rank_int}
            else:
                # Determine trend direction
                if current_rank_int < self.previous_rank:
                    # Rank improved (smaller number is better)
                    rankings_data["trend"] = {"direction": "up", "previous": self.previous_rank}
                elif current_rank_int > self.previous_rank:
                    # Rank worsened (larger number is worse)
                    rankings_data["trend"] = {"direction": "down", "previous": self.previous_rank}
                else:
                    # Rank stayed the same
                    rankings_data["trend"] = {"direction": "same", "previous": self.previous_rank}
                
                # Log the trend
                trend_direction = rankings_data["trend"]["direction"]
                logger.info(f"Rank trend: {self.previous_rank} → {current_rank_int} ({trend_direction})")
            
            # Save data for web interface
            self.last_scrape_data = rankings_data
            
            return rankings_data
            
        except Exception as e:
            logger.error(f"Error scraping from Telegram: {str(e)}")
            logger.error("Cannot get reliable data due to error - returning None")
            return None
    
    def format_rankings_message(self, rankings_data):
        """
        Format the rankings data into a readable message for Telegram
        
        Args:
            rankings_data (dict): The scraped rankings data
            
        Returns:
            str: Formatted message for Telegram in the simplified format
        """
        if not rankings_data or "categories" not in rankings_data:
            return "Coinbase Appstore Rank: Error retrieving data"
        
        if not rankings_data["categories"]:
            return "Coinbase Appstore Rank: N/A"
            
        # Get the rank from the first category (usually Finance)
        category = rankings_data["categories"][0]
        rank = category.get("rank", "N/A")
        
        # Create message with trend indicator at the beginning as per user request
        message = "Coinbase Appstore Rank: " + str(rank)
        
        # Add trend indicator at the beginning if available
        if "trend" in rankings_data:
            trend = rankings_data["trend"]
            direction = trend.get("direction")
            
            if direction and direction != "same":
                try:
                    if direction == "up":
                        # Improved ranking (lower number is better)
                        message = f"🔼 Coinbase Appstore Rank: {rank}"
                    elif direction == "down":
                        # Declined ranking
                        message = f"🔽 Coinbase Appstore Rank: {rank}"
                except (ValueError, TypeError):
                    # If any error, use default message without indicator
                    pass
        
        return message