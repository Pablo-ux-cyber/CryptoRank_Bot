#!/usr/bin/env python3
# Test script to verify functionality when no data for today is available

import os
import sys
from datetime import datetime, date
import logging
import unittest
from unittest.mock import patch, MagicMock

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to system path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules
from scraper import SensorTowerScraper
from scheduler import SensorTowerScheduler

class MockDate(date):
    """Mock date class to simulate a specific date"""
    @classmethod
    def today(cls):
        return cls(2025, 5, 10)  # Return tomorrow's date to simulate no data for today

class TestNoTodayData(unittest.TestCase):
    """Test cases for when no data for today is available"""
    
    @patch('scraper.date', MockDate)
    def test_scraper_no_today_data(self):
        """Test that scraper returns no messages when no data for today"""
        scraper = SensorTowerScraper()
        messages = scraper._get_messages_from_telegram()
        
        # Check that no messages from today are found (since we're mocking today as tomorrow)
        self.assertEqual(messages, [])
        
        # Test that scrape_category_rankings returns None
        rankings_data = scraper.scrape_category_rankings()
        self.assertIsNone(rankings_data)
    
    @patch('scraper.date', MockDate)
    @patch('scheduler.date', MockDate)
    def test_scheduler_message_on_missing_data(self):
        """Test that scheduler sends proper message when no data for today"""
        scheduler = SensorTowerScheduler()
        
        # Create mock objects
        mock_telegram_bot = MagicMock()
        mock_fear_greed_tracker = MagicMock()
        mock_altcoin_index = MagicMock()
        
        # Configure mock objects
        mock_telegram_bot.test_connection.return_value = True
        mock_telegram_bot.send_message.return_value = True
        
        mock_fear_greed_tracker.get_fear_greed_index.return_value = {
            'value': 65,
            'classification': 'Greed'
        }
        mock_fear_greed_tracker.format_fear_greed_message.return_value = "Fear & Greed: 😏 Greed: 65/100"
        
        mock_altcoin_index.get_altseason_index.return_value = {
            'signal': '🟡',
            'status': 'Moderate Altseason',
            'index': 0.55
        }
        mock_altcoin_index.format_altseason_message.return_value = "Altcoin Season Index: 🪙 Altcoin Season"
        
        # Inject mock objects
        scheduler.telegram_bot = mock_telegram_bot
        scheduler.fear_greed_tracker = mock_fear_greed_tracker
        scheduler.altcoin_season_index = mock_altcoin_index
        
        # Run scraping job with force_refresh=True (as in 11:10 scheduled check)
        scheduler.run_scraping_job(force_refresh=True)
        
        # Check that mock_telegram_bot.send_message was called
        mock_telegram_bot.send_message.assert_called()
        
        # Get the message that was sent
        sent_message = mock_telegram_bot.send_message.call_args[0][0]
        logger.info(f"Message that would be sent: {sent_message}")
        
        # Check that the message contains notification about missing data
        self.assertIn("No data from Coinbase AppStore ranking for today", sent_message)
        self.assertIn("Fear & Greed", sent_message)
        self.assertIn("Altcoin Season", sent_message)

if __name__ == "__main__":
    unittest.main()