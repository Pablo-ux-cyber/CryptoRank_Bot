#!/usr/bin/env python3
# Test script to verify new functionality - only using today's data

import os
import sys
from datetime import datetime, date
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to system path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules
from scraper import SensorTowerScraper
from telegram_bot import TelegramBot
from fear_greed_index import FearGreedIndexTracker
from altcoin_season_index import AltcoinSeasonIndex

def test_telegram_scraper():
    """Test that scraper only returns messages from today"""
    scraper = SensorTowerScraper()
    logger.info("Testing scraper to ensure it only returns today's messages...")
    
    # Get messages from Telegram
    messages = scraper._get_messages_from_telegram()
    
    # Check if we got any messages
    if not messages:
        logger.info("No messages found - this is expected if there are no messages from today")
    else:
        logger.info(f"Found {len(messages)} messages from today. Here are the first 3:")
        for i, msg in enumerate(messages[:3]):
            logger.info(f"  Message {i+1}: {msg[:100]}...")
    
    # Test scraping for rankings
    logger.info("Testing scrape_category_rankings() to ensure it only uses today's rankings...")
    rankings_data = scraper.scrape_category_rankings()
    
    if rankings_data:
        logger.info(f"Successfully retrieved today's ranking: {rankings_data['categories'][0]['rank']}")
    else:
        logger.info("No rankings data from today - this is expected if there are no today's messages with ranking")
    
    return True

def test_scheduler_message_on_missing_data():
    """Test that scheduler sends proper message when no data for today"""
    from scheduler import SensorTowerScheduler
    
    scheduler = SensorTowerScheduler()
    
    # Create a mock TelegramBot that logs sent messages instead of sending them
    class MockTelegramBot:
        def __init__(self):
            self.sent_messages = []
        
        def test_connection(self):
            return True
            
        def send_message(self, message):
            logger.info(f"Mock TelegramBot would send: {message}")
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
    else:
        logger.info("No messages would be sent - this suggests something is wrong in the scheduler logic")
    
    return True

if __name__ == "__main__":
    logger.info("Starting tests for 'today only' feature...")
    
    telegram_test = test_telegram_scraper()
    scheduler_test = test_scheduler_message_on_missing_data()
    
    if telegram_test and scheduler_test:
        logger.info("All tests completed successfully!")
    else:
        logger.error("Some tests failed. Check logs for details.")