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
            
            # Шаг 1: Получение и отправка данных о рейтинге приложения
            rankings_data = self.scraper.scrape_category_rankings()
            
            if not rankings_data:
                error_message = "❌ Failed to scrape SensorTower data."
                logger.error(error_message)
                self.telegram_bot.send_message(error_message)
                return False
            
            # Format the data into a message
            message = self.scraper.format_rankings_message(rankings_data)
            
            # Send the message to Telegram
            if not self.telegram_bot.send_message(message):
                logger.error("Failed to send rankings message to Telegram.")
                return False
            
            logger.info("App rankings sent successfully")
            
            # Шаг 2: Получение и отправка данных индекса страха и жадности
            try:
                # Небольшая пауза между сообщениями
                time.sleep(2)
                
                fear_greed_data = self.fear_greed_tracker.get_fear_greed_index()
                
                if not fear_greed_data:
                    logger.error("Failed to get Fear & Greed Index data")
                else:
                    # Format message
                    fear_greed_message = self.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
                    
                    # Send to Telegram
                    if not self.telegram_bot.send_message(fear_greed_message):
                        logger.error("Failed to send Fear & Greed Index to Telegram")
                    else:
                        logger.info("Fear & Greed Index sent successfully")
            except Exception as e:
                logger.error(f"Error processing Fear & Greed Index: {str(e)}")
                # Продолжаем выполнение даже при ошибке с индексом страха и жадности
            
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
