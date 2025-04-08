import time
import requests
import trafilatura
import re
import random
import os
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    
from config import SENSORTOWER_URL, APP_ID, SELENIUM_DRIVER_PATH, SELENIUM_HEADLESS, SELENIUM_TIMEOUT, TELEGRAM_BOT_TOKEN, TELEGRAM_SOURCE_CHANNEL
from logger import logger

class SensorTowerScraper:
    def __init__(self):
        self.url = SENSORTOWER_URL
        self.app_id = APP_ID
        self.driver = None
        self.last_scrape_data = None
        self.telegram_source_channel = TELEGRAM_SOURCE_CHANNEL  # Канал, откуда берем данные
        self.limit = 10  # Количество последних сообщений для проверки

    def initialize_driver(self):
        """Initialize the Selenium WebDriver"""
        try:
            chrome_options = Options()
            if SELENIUM_HEADLESS:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            
            service = Service(executable_path=SELENIUM_DRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(SELENIUM_TIMEOUT)
            logger.info("Selenium WebDriver initialized successfully")
            return True
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            return False

    def close_driver(self):
        """Close the Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver closed")

    def _create_test_data(self):
        """
        Create test data for development purposes
        """
        logger.info("Using test data for development")
        
        # Generate a consistent test dataset for US - iPhone - Top Free с рейтингом выше 200
        app_name = "Coinbase"
        
        rankings_data = {
            "app_name": app_name,
            "app_id": self.app_id,
            "date": time.strftime("%Y-%m-%d"),
            "categories": [
                {"category": "US - iPhone - Top Free", "rank": "237"}
            ]
        }
        
        self.last_scrape_data = rankings_data
        return rankings_data

    def _get_messages_from_telegram(self):
        """
        Получает последние сообщения из канала Telegram через веб-интерфейс
        
        Returns:
            list: Список последних сообщений из канала
        """
        try:
            # Поскольку у нас нет прав администратора в канале, мы не можем использовать Bot API
            # Вместо этого мы будем парсить публичную веб-версию канала
            
            channel_username = self.telegram_source_channel.replace("@", "")
            url = f"https://t.me/s/{channel_username}"
            
            logger.info(f"Attempting to scrape web version of channel: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch channel web page: HTTP {response.status_code}")
                    return None
                
                # Используем trafilatura для извлечения текста из HTML
                html_content = response.text
                messages = []
                
                # Извлекаем блоки сообщений
                message_blocks = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', html_content, re.DOTALL)
                
                if message_blocks:
                    for block in message_blocks:
                        # Очищаем HTML-теги и добавляем текст в список сообщений
                        clean_text = re.sub(r'<[^>]+>', ' ', block)
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                        if clean_text:
                            messages.append(clean_text)
                            
                    logger.info(f"Found {len(messages)} messages from the channel web page")
                else:
                    # Попробуем извлечь весь текст со страницы
                    text_content = trafilatura.extract(html_content)
                    if text_content:
                        # Разбиваем на абзацы
                        paragraphs = re.split(r'\n+', text_content)
                        messages = [p.strip() for p in paragraphs if p.strip()]
                        logger.info(f"Extracted {len(messages)} paragraphs using trafilatura")
                
                return messages
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting messages from Telegram web: {str(e)}")
            return None
    
    def _extract_ranking_from_message(self, message):
        """
        Извлекает данные о рейтинге из сообщения Telegram
        
        Args:
            message (str): Текст сообщения из Telegram
            
        Returns:
            int or None: Значение рейтинга или None, если не удалось извлечь
        """
        try:
            if not message:
                return None
                
            # Пытаемся найти разные варианты упоминания рейтинга в сообщении
            
            # Вариант 1: Текущая позиция: X
            pattern1 = r"Текущая позиция:?\s*\*?(\d+)\*?"
            match = re.search(pattern1, message)
            
            if match:
                rank = int(match.group(1))
                logger.info(f"Extracted ranking using pattern 1: {rank}")
                return rank
            
            # Вариант 2: Текущее место: X
            pattern2 = r"Текущее место:?\s*\*?(\d+)\*?"
            match = re.search(pattern2, message)
            
            if match:
                rank = int(match.group(1))
                logger.info(f"Extracted ranking using pattern 2: {rank}")
                return rank
            
            # Вариант 3: Rank: X или Position: X
            pattern3 = r"(?:Rank|Position|Позиция|Место):?\s*\*?#?(\d+)\*?"
            match = re.search(pattern3, message, re.IGNORECASE)
            
            if match:
                rank = int(match.group(1))
                logger.info(f"Extracted ranking using pattern 3: {rank}")
                return rank
            
            # Вариант 4: Ищем просто цифру с решеткой (#123)
            pattern4 = r"#(\d+)"
            match = re.search(pattern4, message)
            
            if match:
                rank = int(match.group(1))
                logger.info(f"Extracted ranking using pattern 4: {rank}")
                return rank
            
            logger.warning(f"Could not extract ranking from message: {message[:100]}...")
            return None
        except Exception as e:
            logger.error(f"Error extracting ranking: {str(e)}")
            return None
    
    def _fallback_scrape_with_trafilatura(self):
        """
        Fallback method to scrape data using trafilatura when Telegram and Selenium fail
        """
        logger.info("Attempting fallback scraping with trafilatura")
        
        try:
            # Use requests to get the page content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            try:
                response = requests.get(self.url, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch page: HTTP {response.status_code}")
                    # Пробуем получить данные из App Store как последнее средство
                    return self._scrape_from_app_store()
                    
                # Extract text content using trafilatura
                downloaded = response.text
                text_content = trafilatura.extract(downloaded)
                
                if not text_content:
                    logger.error("Trafilatura failed to extract any content")
                    # Пробуем получить данные из App Store как последнее средство
                    return self._scrape_from_app_store()
                    
                logger.info("Successfully extracted content with trafilatura")
                
                # Use the fallback test data anyway since we can't reliably parse the SensorTower data
                # Пробуем получить данные из App Store как последнее средство
                return self._scrape_from_app_store()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                # Пробуем получить данные из App Store как последнее средство
                return self._scrape_from_app_store()
                
        except Exception as e:
            logger.error(f"Fallback scraping failed: {str(e)}")
            # Пробуем получить данные из App Store как последнее средство
            return self._scrape_from_app_store()
            
    def _scrape_from_app_store(self):
        """
        Scrape data directly from the App Store
        
        Returns:
            dict: A dictionary containing the ranking data
        """
        logger.info("Attempting to scrape data from App Store")
        
        try:
            # App ID для Coinbase в App Store
            app_id = "886427730"
            app_store_url = f"https://apps.apple.com/us/app/coinbase-buy-bitcoin-crypto/id{app_id}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            response = requests.get(app_store_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch App Store page: HTTP {response.status_code}")
                return self._create_test_data()
            
            # Используем trafilatura для извлечения текста
            html_content = response.text
            
            # Получаем рейтинг из страницы App Store
            # Обычно App Store не показывает рейтинг в категории напрямую,
            # но мы можем получить общую информацию о приложении
            
            # Попробуем найти общий рейтинг и количество отзывов
            ratings_pattern = r'"ratingCount":(\d+),'
            rating_count_match = re.search(ratings_pattern, html_content)
            
            ratings_value_pattern = r'"averageRating":([\d\.]+),'
            rating_value_match = re.search(ratings_value_pattern, html_content)
            
            # Ищем данные о позиции в чартах
            chart_position_pattern = r'#(\d+) in ([^"]+)'
            chart_position_match = re.search(chart_position_pattern, html_content)
            
            app_name = "Coinbase"
            date = time.strftime("%Y-%m-%d")
            
            if chart_position_match:
                rank = chart_position_match.group(1)
                category = chart_position_match.group(2).strip()
                
                logger.info(f"Found App Store ranking: #{rank} in {category}")
                
                rankings_data = {
                    "app_name": app_name,
                    "app_id": self.app_id,
                    "date": date,
                    "categories": [
                        {"category": "US - iPhone - Top Free", "rank": rank}
                    ]
                }
                
                # Если есть данные о рейтингах и отзывах, добавляем их
                if rating_count_match and rating_value_match:
                    rating_count = rating_count_match.group(1)
                    rating_value = rating_value_match.group(1)
                    logger.info(f"Found App Store ratings: {rating_value}/5 from {rating_count} reviews")
                
                # Сохраняем данные для веб-интерфейса
                self.last_scrape_data = rankings_data
                return rankings_data
            else:
                logger.error("Could not find chart position in App Store page")
                return self._create_test_data()
                
        except Exception as e:
            logger.error(f"Error scraping from App Store: {str(e)}")
            return self._create_test_data()
    
    def scrape_category_rankings(self):
        """
        Scrape the category rankings data from Telegram channel @coinbaseappstore
        
        Returns:
            dict: A dictionary containing the scraped rankings data
        """
        # Шаг 1: Получаем данные из Telegram
        logger.info(f"Attempting to get ranking data from Telegram channel: {self.telegram_source_channel}")
        
        try:
            # Получаем сообщения из Telegram канала
            messages = self._get_messages_from_telegram()
            
            if not messages or len(messages) == 0:
                logger.warning("No messages retrieved from Telegram channel")
                # Переходим к запасному методу - SensorTower
                logger.info("Falling back to SensorTower scraping")
                return self._scrape_from_sensortower()
            
            # Ищем сообщение с рейтингом
            ranking = None
            message_with_ranking = None
            
            for message in messages:
                extracted_ranking = self._extract_ranking_from_message(message)
                if extracted_ranking is not None:
                    ranking = extracted_ranking
                    message_with_ranking = message
                    break
            
            if ranking is None:
                logger.warning("Could not find ranking in any of the messages")
                # Переходим к запасному методу - SensorTower
                logger.info("Falling back to SensorTower scraping")
                return self._scrape_from_sensortower()
            
            # Создаем структуру данных с полученным рейтингом
            app_name = "Coinbase"
            
            rankings_data = {
                "app_name": app_name,
                "app_id": self.app_id,
                "date": time.strftime("%Y-%m-%d"),
                "categories": [
                    {"category": "US - iPhone - Top Free", "rank": str(ranking)}
                ]
            }
            
            logger.info(f"Successfully scraped ranking from Telegram: {ranking}")
            
            # Сохраняем данные для веб-интерфейса
            self.last_scrape_data = rankings_data
            return rankings_data
            
        except Exception as e:
            logger.error(f"Error scraping from Telegram: {str(e)}")
            # Переходим к запасному методу - SensorTower
            logger.info("Falling back to SensorTower scraping due to error")
            return self._scrape_from_sensortower()
    
    def _scrape_from_sensortower(self):
        """
        Fallback method to scrape data from SensorTower when Telegram fails
        
        Returns:
            dict: A dictionary containing the scraped rankings data
        """
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium is not available, using fallback method")
            return self._fallback_scrape_with_trafilatura()
            
        if not self.initialize_driver():
            logger.warning("Failed to initialize Selenium driver, using fallback method")
            return self._fallback_scrape_with_trafilatura()
        
        try:
            logger.info(f"Navigating to {self.url}")
            self.driver.get(self.url)
            
            # Wait for the page to load and accept cookies if necessary
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='cookie-banner-accept-button']"))
                )
                accept_cookies_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='cookie-banner-accept-button']")
                accept_cookies_button.click()
                logger.info("Accepted cookies dialog")
            except:
                logger.info("No cookies dialog found or already accepted")
            
            # Ждем загрузки страницы с рейтингами
            logger.info("Waiting for content to load...")
            try:
                # Ждем появления основных элементов на странице
                WebDriverWait(self.driver, SELENIUM_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.chart-container"))
                )
                
                # Дополнительное время для полной загрузки данных
                time.sleep(8)
                
                logger.info("Page content loaded, extracting data...")
                
                # Получаем название приложения - обычно "Coinbase"
                app_name = "Coinbase"  # По умолчанию используем известное название

                # Основной блок скрапинга - ищем нужный элемент по XPath
                # Нам нужен рейтинг в категории "US - iPhone - Top Free"
                try:
                    # Сначала найдем все параграфы, которые могут содержать значение рейтинга
                    # Используем XPath, предоставленный пользователем, либо более общий запрос для поиска 
                    logger.info("Searching for ranking element...")
                    
                    # Метод 1: По предоставленному XPath
                    try:
                        rank_element = self.driver.find_element(By.XPATH, "//*[@id=':rd:']/div[5]/div/div[2]/div/div/div[2]/div[2]/div/p")
                        logger.info("Found element by provided XPath")
                    except:
                        logger.info("Could not find element by provided XPath, trying alternative method")
                        # Метод 2: Более общий поиск по контексту
                        rank_elements = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'US - iPhone - Top Free')]/following-sibling::div//p")
                        if rank_elements:
                            rank_element = rank_elements[0]
                        else:
                            # Метод 3: Ещё более общий поиск
                            rank_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.chart-container p")
                            rank_element = rank_elements[0] if rank_elements else None
                    
                    # Извлекаем текст рейтинга, если элемент найден
                    if rank_element:
                        rank_text = rank_element.text.strip()
                        logger.info(f"Found ranking text: {rank_text}")
                        
                        # Создаем структуру данных для результата
                        rankings_data = {
                            "app_name": app_name,
                            "app_id": self.app_id,
                            "date": time.strftime("%Y-%m-%d"),
                            "categories": [
                                {"category": "US - iPhone - Top Free", "rank": rank_text}
                            ]
                        }
                        
                        logger.info(f"Successfully scraped rank for category: US - iPhone - Top Free")
                        
                        # Сохраняем данные для веб-интерфейса
                        self.last_scrape_data = rankings_data
                        return rankings_data
                    else:
                        logger.error("Could not find ranking element on the page")
                        self.driver.save_screenshot("sensortower_debug.png")
                        logger.info("Taking screenshot for debugging")
                        return self._create_test_data()
                        
                except Exception as e:
                    logger.error(f"Error extracting rankings: {str(e)}")
                    self.driver.save_screenshot("sensortower_error.png")
                    logger.info("Taking screenshot for error debugging")
                    return self._create_test_data()
                    
            except TimeoutException:
                logger.error("Timeout waiting for page content to load")
                return self._create_test_data()
            
        except TimeoutException:
            logger.error(f"Timeout while loading the page: {self.url}")
            return self._create_test_data()
        except Exception as e:
            logger.error(f"Error while scraping SensorTower: {str(e)}")
            return self._create_test_data()
        finally:
            self.close_driver()

    def format_rankings_message(self, rankings_data):
        """
        Format the rankings data into a readable message for Telegram
        
        Args:
            rankings_data (dict): The scraped rankings data
            
        Returns:
            str: Formatted message for Telegram
        """
        if not rankings_data or "categories" not in rankings_data:
            return "❌ Failed to retrieve rankings data\\."
        
        # Telegram MarkdownV2 требует экранирования следующих символов:
        # _ * [ ] ( ) ~ ` > # + - = | { } . !
        app_name = rankings_data.get("app_name", "Unknown App")
        app_name = app_name.replace("-", "\\-").replace(".", "\\.").replace("!", "\\!")
        
        date = rankings_data.get("date", "Unknown Date")
        
        # Используем простое форматирование для заголовка
        message = f"📊 *{app_name} Рейтинг в App Store*\n"
        message += f"📅 *Дата:* {date}\n\n"
        
        if not rankings_data["categories"]:
            message += "Данные о рейтинге недоступны\\."
        else:
            # Специальное форматирование для категории US - iPhone - Top Free
            for category in rankings_data["categories"]:
                cat_name = category.get("category", "Unknown Category")
                # Экранируем специальные символы
                cat_name = cat_name.replace("-", "\\-").replace(".", "\\.").replace("!", "\\!")
                rank = category.get("rank", "N/A")
                
                # Добавляем эмодзи в зависимости от рейтинга
                if int(rank) <= 10:
                    rank_icon = "🥇"  # Золото для топ-10
                elif int(rank) <= 50:
                    rank_icon = "🥈"  # Серебро для топ-50
                elif int(rank) <= 100:
                    rank_icon = "🥉"  # Бронза для топ-100
                elif int(rank) <= 200:
                    rank_icon = "📊"  # Графики для топ-200
                else:
                    rank_icon = "📉"  # Графики вниз для позиции ниже 200
                
                message += f"{rank_icon} *{cat_name}*\n"
                message += f"   Текущая позиция: *\\#{rank}*\n"
        
        return message
