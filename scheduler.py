import threading
import time
from datetime import datetime, timedelta

from logger import logger
from scraper import SensorTowerScraper
from telegram_bot import TelegramBot
from fear_greed_index import FearGreedIndexTracker

class SensorTowerScheduler:
    def __init__(self):
        # Instead of using APScheduler, create a simple threading-based scheduler
        self.running = False
        self.thread = None
        self.scraper = SensorTowerScraper()
        self.telegram_bot = TelegramBot()
        self.fear_greed_tracker = FearGreedIndexTracker()
    
    def _scheduler_loop(self):
        """
        The main scheduler loop that runs in a background thread.
        Sleeps for 24 hours between executions.
        """
        while self.running:
            # Sleep for 24 hours (in seconds)
            time.sleep(86400)
            if self.running:  # Check if still running after sleep
                self.run_scraping_job()
    
    def start(self):
        """Start the scheduler"""
        try:
            if self.running:
                logger.warning("Scheduler is already running")
                return True
                
            self.running = True
            self.thread = threading.Thread(target=self._scheduler_loop)
            self.thread.daemon = True
            self.thread.start()
            
            next_run = datetime.now() + timedelta(hours=24)
            logger.info(f"Scheduler started. Next run at: {next_run}")
            
            # Uncomment to run immediately for testing
            # self.run_scraping_job()
            
            return True
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            return False
    
    def stop(self):
        """Stop the scheduler"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=1)
            logger.info("Scheduler stopped")
    
    def run_scraping_job(self):
        """
        Run the scraping job: scrape SensorTower data and post to Telegram
        """
        logger.info(f"Running scheduled scraping job at {datetime.now()}")
        
        try:
            # Test Telegram connection first
            if not self.telegram_bot.test_connection():
                logger.error("Telegram connection test failed. Job aborted.")
                return False
            
            # Часть 1: Получение данных о рейтинге приложения
            rankings_data = self.scraper.scrape_category_rankings()
            
            if not rankings_data:
                error_message = "❌ Failed to scrape SensorTower data."
                logger.error(error_message)
                self.telegram_bot.send_message(error_message)
                return False
            
            # Часть 2: Получение данных индекса страха и жадности
            fear_greed_data = None
            try:
                fear_greed_data = self.fear_greed_tracker.get_fear_greed_index()
                
                if not fear_greed_data:
                    logger.error("Failed to get Fear & Greed Index data")
            except Exception as e:
                logger.error(f"Error processing Fear & Greed Index: {str(e)}")
                # Продолжаем выполнение даже при ошибке с индексом страха и жадности
            
            # Создаем единое сообщение с одной общей датой и скрываемыми блоками
            # Получаем текущую дату
            current_date = rankings_data.get("date", time.strftime("%Y-%m-%d"))
            
            # Формируем заголовок с общей датой для всего сообщения
            combined_message = f"📊 *Crypto Market Report*\n"
            combined_message += f"📅 *Дата:* {current_date}\n\n"
            
            # Добавляем данные о рейтинге Coinbase (без отдельной даты)
            app_name = rankings_data.get("app_name", "Coinbase").replace("-", "\\-").replace(".", "\\.").replace("!", "\\!")
            
            # Статус и видимая часть
            if rankings_data.get("categories") and len(rankings_data["categories"]) > 0:
                category = rankings_data["categories"][0]
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
                
                # Основная информация (всегда видима)
                combined_message += f"{rank_icon} *{app_name}*: \\#{rank}\n"
                
                # Детальная информация (скрыта в спойлере)
                details = f"*{app_name} Рейтинг в App Store*\n"
                
                # Добавляем все категории в детали
                for category in rankings_data["categories"]:
                    cat_name = category.get("category", "Unknown Category")
                    # Экранируем специальные символы
                    cat_name = cat_name.replace("-", "\\-").replace(".", "\\.").replace("!", "\\!")
                    rank = category.get("rank", "N/A")
                    
                    details += f"• {cat_name}: \\#{rank}\n"
                
                # Оборачиваем детали в спойлер
                # Символы спойлера для MarkdownV2 - || в начале и конце текста
                combined_message += f"||{details}||\n"
            else:
                combined_message += f"❌ *{app_name}*: Данные о рейтинге недоступны\\.\n"
            
            # Затем добавляем данные об индексе страха и жадности, если они доступны
            if fear_greed_data:
                # Добавляем разделитель между сообщениями
                combined_message += "\n" + "➖➖➖➖➖➖➖➖➖➖➖➖" + "\n\n"
                
                # Добавляем только данные индекса без отдельной даты
                value = fear_greed_data.get("value", "N/A")
                label = fear_greed_data.get("value_classification", "Unknown")
                
                # Основная информация о FGI (всегда видима)
                # Экранируем дефис в строке
                label = label.replace("-", "\\-")
                combined_message += f"🧠 *Индекс страха и жадности*: {value} \\- {label}\n"
                
                # Прогресс-бар и дополнительная информация (скрыта в спойлере)
                details = ""
                
                # Добавляем прогресс-бар в детали
                if "value" in fear_greed_data:
                    progress_bar = self.fear_greed_tracker._generate_progress_bar(int(value), 100, 10)
                    details += f"{progress_bar}\n"
                
                # Добавляем описание значений индекса
                details += "Значения индекса:\\n"
                details += "0\\-25: Экстремальный страх\\n"
                details += "26\\-45: Страх\\n"
                details += "46\\-55: Нейтрально\\n"
                details += "56\\-75: Жадность\\n"
                details += "76\\-100: Экстремальная жадность"
                
                # Оборачиваем детали в спойлер
                combined_message += f"||{details}||"
            
            # Отправляем объединенное сообщение
            if not self.telegram_bot.send_message(combined_message):
                logger.error("Failed to send combined message to Telegram.")
                return False
            
            logger.info("Combined message sent successfully")
            logger.info("Scraping job completed successfully")
            return True
            
        except Exception as e:
            error_message = f"❌ An error occurred during the scraping job: {str(e)}"
            logger.error(error_message)
            try:
                self.telegram_bot.send_message(error_message)
            except:
                pass
            return False
            
    def get_current_fear_greed_index(self):
        """
        Get current Fear & Greed Index data for testing/manual triggering
        
        Returns:
            dict: Fear & Greed Index data or None in case of error
        """
        try:
            return self.fear_greed_tracker.get_fear_greed_index()
        except Exception as e:
            logger.error(f"Error getting Fear & Greed Index: {str(e)}")
            return None
