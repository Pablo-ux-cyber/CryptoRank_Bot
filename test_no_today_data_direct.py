#!/usr/bin/env python3
# Test script to directly verify functionality when no data for today is available

import os
import sys
import logging
from unittest.mock import patch, MagicMock

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to system path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules
from scraper import SensorTowerScraper
from scheduler import SensorTowerScheduler

def test_scheduler_no_today_data():
    """
    Test that scheduler sends proper message when no data for today is available.
    This test directly modifies the scraper to simulate no messages for today.
    """
    # Create scheduler
    scheduler = SensorTowerScheduler()
    
    # Create a custom SensorTowerScraper that simulates no messages for today
    class NoTodayDataScraper(SensorTowerScraper):
        def _get_messages_from_telegram(self):
            logger.info("Mock: No messages for today")
            return []
            
        def get_current_rank(self):
            logger.info("Mock: No current rank available")
            return None
    
    # Replace the scraper with our custom version
    scheduler.scraper = NoTodayDataScraper()
    
    # Create a mock TelegramBot that logs sent messages instead of sending them
    class MockTelegramBot:
        def __init__(self):
            self.sent_messages = []
        
        def test_connection(self):
            logger.info("Mock: Telegram connection test successful")
            return True
            
        def send_message(self, message):
            logger.info(f"Mock: Sending message: {message}")
            self.sent_messages.append(message)
            return True
    
    # Replace the real TelegramBot with our mock
    scheduler.telegram_bot = MockTelegramBot()
    
    # Test running the scraping job with force_refresh=True (as in 11:10 scheduled check)
    logger.info("Testing run_scraping_job with force_refresh=True to simulate 11:10 check...")
    scheduler.run_scraping_job(force_refresh=True)
    
    # Check what messages would be sent
    if scheduler.telegram_bot.sent_messages:
        logger.info("Messages that would be sent:")
        for i, msg in enumerate(scheduler.telegram_bot.sent_messages):
            logger.info(f"  Message {i+1}: {msg}")
            
        # Verify that the message contains notification about missing data
        first_message = scheduler.telegram_bot.sent_messages[0]
        if "No data from Coinbase AppStore ranking for today" in first_message:
            logger.info("SUCCESS: Message contains notification about missing data")
            return True
        else:
            logger.error("FAILURE: Message does not contain notification about missing data")
            return False
    else:
        logger.error("FAILURE: No messages would be sent - this suggests something is wrong in the scheduler logic")
        return False

if __name__ == "__main__":
    logger.info("Starting test for behavior when no data for today is available...")
    result = test_scheduler_no_today_data()
    
    if result:
        logger.info("Test completed successfully!")
    else:
        logger.error("Test failed. Check logs for details.")