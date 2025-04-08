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
            
            # Part 1: Get app ranking data
            rankings_data = self.scraper.scrape_category_rankings()
            
            if not rankings_data:
                error_message = "❌ Failed to scrape SensorTower data."
                logger.error(error_message)
                self.telegram_bot.send_message(error_message)
                return False
            
            # Part 2: Get Fear & Greed Index data
            fear_greed_data = None
            try:
                fear_greed_data = self.fear_greed_tracker.get_fear_greed_index()
                
                if not fear_greed_data:
                    logger.error("Failed to get Fear & Greed Index data")
            except Exception as e:
                logger.error(f"Error processing Fear & Greed Index: {str(e)}")
                # Continue execution even with Fear & Greed Index error
            
            # Create a single message with one common date and collapsible blocks
            # Get current date
            current_date = rankings_data.get("date", time.strftime("%Y-%m-%d"))
            
            # Format header with common date for the entire message
            combined_message = f"📊 *Crypto Market Report*\n"
            combined_message += f"📅 *Date:* {current_date}\n\n"
            
            # Add Coinbase ranking data (without separate date)
            app_name = rankings_data.get("app_name", "Coinbase").replace("-", "\\-").replace(".", "\\.").replace("!", "\\!")
            
            # Status and visible part
            if rankings_data.get("categories") and len(rankings_data["categories"]) > 0:
                category = rankings_data["categories"][0]
                rank = category.get("rank", "N/A")
                
                # Add emoji based on ranking
                if int(rank) <= 10:
                    rank_icon = "🥇"  # Gold for top-10
                elif int(rank) <= 50:
                    rank_icon = "🥈"  # Silver for top-50
                elif int(rank) <= 100:
                    rank_icon = "🥉"  # Bronze for top-100
                elif int(rank) <= 200:
                    rank_icon = "📊"  # Charts for top-200
                else:
                    rank_icon = "📉"  # Downward charts for position below 200
                
                # Key information (always visible)
                combined_message += f"{rank_icon} *{app_name}*: *{rank}*\n"
                
                # Detailed information (hidden in spoiler)
                details = f"*{app_name} App Store Ranking*\n"
                
                # Add all categories to details
                for category in rankings_data["categories"]:
                    cat_name = category.get("category", "Unknown Category")
                    # Escape special characters
                    cat_name = cat_name.replace("-", "\\-").replace(".", "\\.").replace("!", "\\!")
                    rank = category.get("rank", "N/A")
                    
                    details += f"• {cat_name}: *{rank}*\n"
                
                # Wrap details in spoiler
                # Spoiler symbols for MarkdownV2 - || at the beginning and end of text
                combined_message += f"||{details}||\n"
            else:
                combined_message += f"❌ *{app_name}*: Ranking data unavailable\\.\n"
            
            # Then add Fear & Greed Index data if available
            if fear_greed_data:
                # Add separator between messages
                combined_message += "\n" + "➖➖➖➖➖➖➖➖➖➖➖➖" + "\n\n"
                
                # Add only index data without separate date
                value = fear_greed_data.get("value", "N/A")
                label = fear_greed_data.get("value_classification", "Unknown")
                
                # Key information about FGI (always visible)
                # Escape hyphen in string
                label = label.replace("-", "\\-")
                combined_message += f"🧠 *Fear & Greed Index*: {value} \\- {label}\n"
                
                # Progress bar and additional information (hidden in spoiler)
                details = ""
                
                # Add progress bar to details
                if "value" in fear_greed_data:
                    progress_bar = self.fear_greed_tracker._generate_progress_bar(int(value), 100, 10)
                    details += f"{progress_bar}\n"
                
                # Add descriptions of index values
                details += "Index values:\\n"
                details += "0\\\\\\-25: Extreme Fear\\n"
                details += "26\\\\\\-45: Fear\\n"
                details += "46\\\\\\-55: Neutral\\n"
                details += "56\\\\\\-75: Greed\\n"
                details += "76\\\\\\-100: Extreme Greed"
                
                # Wrap details in spoiler
                combined_message += f"||{details}||"
            
            # Send the combined message
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
