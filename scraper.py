import time
import requests
import trafilatura
import re
import os
from datetime import datetime

from config import APP_ID, TELEGRAM_SOURCE_CHANNEL
from logger import logger

class SensorTowerScraper:
    def __init__(self):
        self.app_id = APP_ID
        self.last_scrape_data = None
        self.telegram_source_channel = TELEGRAM_SOURCE_CHANNEL  # Channel where we get data from
        self.limit = 10  # Number of recent messages to check
        self.previous_rank = None  # Will be initialized with first value obtained
        self.session = requests.Session()  # Используем сессию для сохранения cookies между запросами
        
        # Задаем постоянные заголовки для всех запросов
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })
        
        # Нагружаем историю из правильного места, указанного в параметрах бота
        try:
            # Определяем директорию бота по текущему файлу (используем абсолютный путь)
            bot_dir = os.path.dirname(os.path.abspath(__file__))
            history_file = os.path.join(bot_dir, "rank_history.txt")
            
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    saved_rank = f.read().strip()
                    if saved_rank and saved_rank.isdigit():
                        self.previous_rank = int(saved_rank)
                        logger.info(f"Загружен предыдущий рейтинг из файла истории: {self.previous_rank}")
            else:
                logger.warning(f"Файл истории рейтинга не найден по пути: {history_file}")
        except Exception as e:
            logger.error(f"Ошибка при чтении файла истории рейтинга в scraper: {str(e)}")

    def _get_messages_from_telegram(self):
        """
        Gets the latest messages from Telegram channel via web interface
        
        Returns:
            list: List of recent messages from the channel
        """
        try:
            channel_username = self.telegram_source_channel.replace("@", "")
            url = f"https://t.me/s/{channel_username}"
            
            logger.info(f"Attempting to scrape web version of channel: {url}")
            
            try:
                # Добавляем случайный параметр для обхода кеширования
                timestamp = int(time.time())
                url_with_nocache = f"{url}?_={timestamp}"
                
                # Делаем три попытки запроса с увеличивающимся таймаутом
                response = None
                max_attempts = 3
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        timeout = 5 * attempt  # 5, 10, 15 секунд
                        logger.info(f"Request attempt {attempt}/{max_attempts} with timeout {timeout}s")
                        response = self.session.get(url_with_nocache, timeout=timeout)
                        
                        if response.status_code == 200:
                            break
                        else:
                            logger.warning(f"Attempt {attempt}: HTTP {response.status_code}, trying again...")
                            time.sleep(1)  # Пауза между попытками
                    except requests.exceptions.Timeout:
                        logger.warning(f"Attempt {attempt}: Timeout, trying again...")
                        continue
                
                if response is None or response.status_code != 200:
                    status_code = response.status_code if response else "No response"
                    logger.error(f"Failed to fetch channel web page after {max_attempts} attempts: HTTP {status_code}")
                    return None
                
                html_content = response.text
                
                # Для отладки ищем конкретные сообщения
                rank_keywords = ["Coinbase Rank:", "Rank:", "coinbaseappstore"]
                for keyword in rank_keywords:
                    if keyword in html_content:
                        logger.debug(f"Found keyword '{keyword}' in HTML")
                
                # Улучшенный регулярный поиск для определения сообщений
                # Ищем все блоки сообщений
                messages = []
                
                # Используем более точный регулярный паттерн для фильтрации блоков сообщений
                message_pattern = r'<div class="tgme_widget_message[^"]*"[^>]*?data-post="coinbaseappstore/(\d+)".*?>(.*?)<div class="tgme_widget_message_footer'
                blocks = re.findall(message_pattern, html_content, re.DOTALL)
                
                if blocks:
                    logger.info(f"Found {len(blocks)} message blocks")
                    
                    # Создаем словарь сообщений
                    messages_dict = {}
                    
                    for msg_id, block_html in blocks:
                        # Извлекаем текст сообщения
                        text_match = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', block_html, re.DOTALL)
                        
                        if text_match:
                            text_html = text_match.group(1)
                            # Очищаем HTML теги
                            clean_text = re.sub(r'<[^>]+>', ' ', text_html)
                            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                            
                            if clean_text:
                                # Сохраняем сообщение
                                messages_dict[int(msg_id)] = f"[ID: {msg_id}] {clean_text}"
                    
                    if messages_dict:
                        # Сортируем сообщения по ID в порядке убывания (от новых к старым)
                        sorted_ids = sorted(messages_dict.keys(), reverse=True)
                        messages = [messages_dict[msg_id] for msg_id in sorted_ids]
                        
                        logger.info(f"Found {len(messages)} messages with IDs")
                        
                        # Показываем первые несколько сообщений для отладки
                        max_display = min(3, len(messages))
                        for i, msg in enumerate(messages[:max_display]):
                            logger.info(f"Message {i+1}: {msg[:50]}...")
                        
                        # Фильтруем сообщения, содержащие информацию о рейтинге
                        filtered_messages = [msg for msg in messages if "Coinbase Rank" in msg]
                        
                        if filtered_messages:
                            logger.info(f"After filtering for 'Coinbase Rank', found {len(filtered_messages)} relevant messages")
                            return filtered_messages
                        else:
                            # Ищем другие шаблоны поиска рейтинга, если прямого упоминания "Coinbase Rank" нет
                            rank_patterns = [r"Rank\s*:", r"Position\s*:", r"#\d+"]
                            
                            for pattern in rank_patterns:
                                filtered = [msg for msg in messages if re.search(pattern, msg, re.IGNORECASE)]
                                if filtered:
                                    logger.info(f"Found {len(filtered)} messages using pattern '{pattern}'")
                                    return filtered
                            
                            # Если специфичные фильтры не нашли, возвращаем все сообщения
                            logger.warning("No messages with specific ranking info found, using all messages")
                            return messages
                else:
                    logger.error("No message blocks found in HTML")
                
                # Если ничего не нашли, используем trafilatura
                logger.info("Using trafilatura as fallback...")
                text_content = trafilatura.extract(html_content)
                
                if text_content:
                    # Разбиваем на абзацы
                    paragraphs = re.split(r'\n+', text_content)
                    messages = [p.strip() for p in paragraphs if p.strip()]
                    logger.info(f"Extracted {len(messages)} paragraphs using trafilatura")
                    return messages
                
                # Последняя попытка - просто ищем любые текстовые блоки
                if not messages:
                    all_texts = re.findall(r'<div[^>]*>(.*?)</div>', html_content, re.DOTALL)
                    filtered_texts = []
                    
                    for text in all_texts:
                        clean_text = re.sub(r'<[^>]+>', ' ', text)
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                        
                        # Добавляем только если текст содержит цифры (потенциальный рейтинг)
                        if clean_text and re.search(r'\d+', clean_text):
                            filtered_texts.append(clean_text)
                    
                    if filtered_texts:
                        logger.info(f"Found {len(filtered_texts)} text blocks containing numbers")
                        return filtered_texts
                
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
                
            # Список паттернов для извлечения рейтинга
            patterns = [
                # Основной паттерн для @coinbaseappstore
                (r"Coinbase\s+Rank:?\s*(\d+)", "Coinbase Rank"),
                # Другие варианты упоминания рейтинга
                (r"(?:Current\s+)?(?:position|place):?\s*\*?(\d+)\*?", "Position/Place"),
                (r"(?:Rank|Position):?\s*\*?#?(\d+)\*?", "Rank/Position"),
                (r"#(\d+)", "Hashtag"),
                # Если сообщение короткое, ищем просто число
                (r"(\d+)", "Simple number")
            ]
            
            # Проверяем по порядку все паттерны
            for i, (pattern, pattern_name) in enumerate(patterns):
                # Для последнего паттерна (простое число) добавляем дополнительную проверку
                if i == len(patterns) - 1 and len(message.strip().split()) > 3:
                    continue  # Пропускаем последний паттерн для длинных сообщений
                    
                match = re.search(pattern, message, re.IGNORECASE)
                
                if match:
                    rank = int(match.group(1))
                    
                    # Дополнительная проверка для больших чисел 
                    # (вряд ли рейтинг превысит 10,000 для крупного приложения)
                    if rank > 10000 and i == len(patterns) - 1:
                        continue  # Это скорее дата или другое большое число, пропускаем
                        
                    logger.info(f"Extracted ranking using pattern {i} ({pattern_name}): {rank}")
                    return rank
            
            logger.warning(f"Could not extract ranking from message: {message[:100]}...")
            return None
        except Exception as e:
            logger.error(f"Error extracting ranking: {str(e)}")
            return None
    
    def scrape_category_rankings(self):
        """
        Scrape the category rankings data from Telegram channel @coinbaseappstore
        
        Returns:
            dict: A dictionary containing the scraped rankings data
        """
        logger.info(f"Attempting to get ranking data from Telegram channel: {self.telegram_source_channel}")
        
        try:
            # Получаем сообщения из канала Telegram
            messages = self._get_messages_from_telegram()
            
            if not messages or len(messages) == 0:
                logger.warning("No messages retrieved from Telegram channel")
                logger.error("Cannot get reliable data - returning None")
                return None
            else:
                # Проверяем сначала самое свежее сообщение
                ranking = None
                message_with_ranking = None
                
                # Пытаемся найти рейтинг в самом последнем сообщении
                if messages:
                    logger.info(f"Checking most recent message for ranking...")
                    first_message = messages[0]
                    ranking = self._extract_ranking_from_message(first_message)
                    
                    if ranking:
                        logger.info(f"Found ranking in the most recent message: {ranking}")
                        message_with_ranking = first_message
                    else:
                        # Если в первом сообщении нет рейтинга, перебираем все сообщения
                        for i, message in enumerate(messages):
                            ranking = self._extract_ranking_from_message(message)
                            if ranking:
                                logger.info(f"Found ranking in message {i+1}: {ranking}")
                                message_with_ranking = message
                                break
                
                if ranking is None:
                    logger.error("Could not find ranking in any message")
                    logger.error("Cannot get reliable data - returning None")
                    return None
                
                # Создаем структурированный формат данных
                data = {
                    "app_name": "Coinbase",
                    "app_id": self.app_id,
                    "date": time.strftime("%Y-%m-%d"),
                    "categories": [
                        {"category": "US - iPhone - Top Free", "rank": str(ranking)}
                    ]
                }
                
                # Журналируем рейтинг, который извлекли
                logger.info(f"Successfully scraped ranking from Telegram: {ranking}")
                
                # Определяем направление тренда
                current_rank_int = ranking
                
                # Для первого запуска, когда нет предыдущего значения
                if self.previous_rank is None:
                    logger.info(f"First run, no previous value. Current rank: {current_rank_int}")
                    self.previous_rank = current_rank_int
                    data["trend"] = {"direction": "same", "previous": current_rank_int}
                else:
                    # Логируем изменение рейтинга для отладки
                    logger.info(f"Rank trend: {self.previous_rank} → {current_rank_int} ({self.previous_rank == current_rank_int and 'same' or (self.previous_rank > current_rank_int and 'up' or 'down')})")
                    
                    # Определяем направление тренда
                    if current_rank_int < self.previous_rank:
                        # Рейтинг улучшился (меньшее число лучше)
                        logger.info(f"Улучшение рейтинга: {self.previous_rank} → {current_rank_int}")
                        data["trend"] = {"direction": "up", "previous": self.previous_rank}
                    elif current_rank_int > self.previous_rank:
                        # Рейтинг ухудшился (большее число хуже)
                        logger.info(f"Ухудшение рейтинга: {self.previous_rank} → {current_rank_int}")
                        data["trend"] = {"direction": "down", "previous": self.previous_rank}
                    else:
                        # Рейтинг не изменился
                        data["trend"] = {"direction": "same", "previous": self.previous_rank}
                
                # Сохраняем данные последнего скрапинга
                self.last_scrape_data = data
                
                return data
                
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return None
    
    def format_rankings_message(self, rankings_data):
        """
        Format the rankings data into a readable message for Telegram
        
        Args:
            rankings_data (dict): The scraped rankings data
            
        Returns:
            str: Formatted message for Telegram
        """
        if not rankings_data or "categories" not in rankings_data or not rankings_data["categories"]:
            return "❌ Error: No ranking data available"
            
        category_data = rankings_data["categories"][0]
        rank = category_data["rank"]
        app_name = rankings_data.get("app_name", "Coinbase")
        
        # Определяем индикатор тренда (если доступен)
        trend_indicator = ""
        trend_text = ""
        
        if "trend" in rankings_data:
            trend = rankings_data["trend"]
            direction = trend.get("direction", "unknown")
            previous = trend.get("previous", None)
            
            if direction == "up":
                trend_indicator = "🔼"
                if previous:
                    trend_text = f" (improved from {previous})"
            elif direction == "down":
                trend_indicator = "🔽"
                if previous:
                    trend_text = f" (dropped from {previous})"
                    
        # Добавляем предупреждение, если это резервные данные
        fallback_warning = ""
        if rankings_data.get("is_fallback_data", False):
            fallback_warning = "\n⚠️ Using previously saved data due to connection issues"
            
        # Формируем сообщение
        message = f"{trend_indicator} {app_name} Appstore Rank: {rank}{trend_text}{fallback_warning}"
        
        return message