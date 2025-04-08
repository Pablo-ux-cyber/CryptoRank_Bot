import threading
import time
import csv
import os
from datetime import datetime, timedelta

from logger import logger
from scraper import SensorTowerScraper
from telegram_bot import TelegramBot
from visualize_data import generate_rankings_chart, generate_summary_analysis

class SensorTowerScheduler:
    def __init__(self):
        # Instead of using APScheduler, create a simple threading-based scheduler
        self.running = False
        self.thread = None
        self.scraper = SensorTowerScraper()
        self.telegram_bot = TelegramBot()
    
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
            
            # Run immediately upon start
            self.run_scraping_job()
            
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
            
            # Scrape the data
            rankings_data = self.scraper.scrape_category_rankings()
            
            if not rankings_data:
                error_message = "❌ Failed to scrape SensorTower data."
                logger.error(error_message)
                self.telegram_bot.send_message(error_message)
                return False
            
            # Format the data into a message
            message = self.scraper.format_rankings_message(rankings_data)
            
            # Add source information if available 
            if 'source' in rankings_data:
                logger.info(f"Data source: {rankings_data['source']}")
                message = message.replace("📊 *Coinbase App Rankings*\n", f"📊 *Coinbase App Rankings* (via {rankings_data['source']})\n")
            
            # Send the message to Telegram
            if not self.telegram_bot.send_message(message):
                logger.error("Failed to send message to Telegram.")
                return False
            
            # Process the rankings data - remove '#' symbols if present
            for cat in rankings_data.get('categories', []):
                if 'rank' in cat and isinstance(cat['rank'], str) and '#' in cat['rank']:
                    cat['rank'] = cat['rank'].replace('#', '').strip()
            
            # Save the data to the historical data CSV file
            self._save_to_historical_data(rankings_data)
            
            # Generate the chart and analysis
            generate_rankings_chart()
            generate_summary_analysis()
            
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
            
    def _save_to_historical_data(self, rankings_data):
        """
        Save the scraped rankings data to a CSV file for historical tracking
        
        Args:
            rankings_data (dict): The scraped rankings data
        """
        try:
            # Define the CSV file path
            csv_file = 'historical_data.csv'
            
            # Prepare the data for the CSV
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Extract rankings for each category
            finance_rank = None
            apps_rank = None
            overall_rank = None
            
            for category in rankings_data.get('categories', []):
                # Keys can be either 'name' or 'category' depending on where data came from
                category_name = category.get('name', category.get('category', ''))
                rank = category.get('rank')
                
                if category_name == 'iPhone - Free - Finance':
                    finance_rank = rank
                elif category_name == 'iPhone - Free - Apps':
                    apps_rank = rank
                elif category_name == 'iPhone - Free - Overall':
                    overall_rank = rank
            
            # We need at least two valid categories to consider saving
            valid_categories = [rank for rank in [finance_rank, apps_rank, overall_rank] if rank]
            
            # Skip only if we have 0 or 1 valid rankings
            if len(valid_categories) < 2:
                logger.warning("Insufficient ranking data (need at least 2 categories), not saving to historical data")
                return
                
            # Log what categories we have
            logger.info(f"Saving to historical data with {len(valid_categories)} categories: Finance: {finance_rank}, Apps: {apps_rank}, Overall: {overall_rank}")
            
            # Create file with headers if it doesn't exist
            file_exists = os.path.isfile(csv_file)
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                
                # Write headers if the file doesn't exist
                if not file_exists:
                    writer.writerow(['date', 'iPhone - Free - Finance', 'iPhone - Free - Apps', 'iPhone - Free - Overall'])
                
                # Write the data row
                writer.writerow([today, finance_rank, apps_rank, overall_rank])
                
            logger.info(f"Rankings data saved to historical data file for {today}")
            
            # Limit to 30 days of data by removing older entries if necessary
            self._limit_historical_data_to_30_days(csv_file)
            
        except Exception as e:
            logger.error(f"Error saving to historical data: {str(e)}")
    
    def _limit_historical_data_to_30_days(self, csv_file):
        """
        Ensure the historical data file contains only the last 30 days of data
        
        Args:
            csv_file (str): Path to the CSV file
        """
        try:
            # Read the entire CSV file
            rows = []
            with open(csv_file, 'r', newline='') as f:
                reader = csv.reader(f)
                header = next(reader)  # Save the header
                rows = list(reader)
            
            # If we have more than 30 days of data, keep only the most recent 30
            if len(rows) > 30:
                # Sort by date (first column) in descending order
                rows.sort(key=lambda x: x[0], reverse=True)
                rows = rows[:30]
                
                # Sort back by date in ascending order for writing
                rows.sort(key=lambda x: x[0])
                
                # Write back to the file
                with open(csv_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(rows)
                    
                logger.info(f"Historical data limited to the most recent 30 days")
                
        except Exception as e:
            logger.error(f"Error limiting historical data: {str(e)}")
