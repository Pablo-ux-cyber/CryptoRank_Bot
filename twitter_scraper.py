#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
import logging
import requests
from datetime import datetime, timedelta
from logger import setup_logger

# Setup logger
logger = setup_logger()

class TwitterScraper:
    def __init__(self, username="COINAppRankBot"):
        """
        Initialize the Twitter scraper for a specific username
        
        Args:
            username (str): Twitter username to scrape (without @)
        """
        self.username = username
        self.base_url = f"https://x.com/{username}"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        self.last_scrape_data = None
        
    def scrape_latest_rankings(self):
        """
        Scrape the latest rankings from the Twitter account
        
        Returns:
            dict: A dictionary containing the scraped rankings data or None if failed
        """
        try:
            logger.info(f"Scraping latest rankings from Twitter: {self.base_url}")
            
            # Send a request to the Twitter profile
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
            
            response = requests.get(self.base_url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to access Twitter profile. Status code: {response.status_code}")
                return None
                
            # Find the tweets containing rankings data
            html_content = response.text
            
            # Initialize the rankings data
            rankings_data = {
                "app_name": "Coinbase",
                "app_id": "886427730",
                "date": time.strftime("%Y-%m-%d"),
                "categories": [],
                "source": "Twitter/@COINAppRankBot"
            }
            
            # Look for ranking tweets (typically they have a format like "iPhone - Free - Finance: #19")
            # The pattern below looks for common category names followed by a rank number
            categories_needed = ["iPhone - Free - Finance", "iPhone - Free - Apps", "iPhone - Free - Overall"]
            patterns = [
                r'(iPhone\s*-\s*Free\s*-\s*(Finance|Apps|Overall)).*?[#]?(\d+)',
                r'(Finance|Apps|Overall)[^#\d]*[#]?(\d+)',
                r'(iPhone\s*-\s*(Finance|Apps|Overall))[^#\d]*[#]?(\d+)'
            ]
            
            # Keep track of found categories to avoid duplicates
            categories_found = []
            
            # Try each pattern
            for pattern in patterns:
                matches = re.finditer(pattern, html_content, re.IGNORECASE)
                
                for match in matches:
                    # Determine the category
                    if 'Finance' in match.group(0) or 'finance' in match.group(0).lower():
                        category = "iPhone - Free - Finance"
                    elif 'Apps' in match.group(0) or 'apps' in match.group(0).lower():
                        category = "iPhone - Free - Apps"
                    elif 'Overall' in match.group(0) or 'overall' in match.group(0).lower():
                        category = "iPhone - Free - Overall"
                    else:
                        continue
                    
                    # Extract rank - get the last group that contains digits
                    rank = None
                    for group_idx in range(len(match.groups()), 0, -1):
                        group = match.group(group_idx)
                        if group and re.search(r'\d', group):
                            rank = ''.join(re.findall(r'\d+', group))
                            break
                            
                    if rank and category not in categories_found:
                        categories_found.append(category)
                        rankings_data["categories"].append({"category": category, "rank": rank})
                        logger.info(f"Found Twitter ranking for {category}: #{rank}")
            
            # Look for date information
            date_patterns = [
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
                r'(\w{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{2,4})'  # Month DD, YYYY
            ]
            
            for pattern in date_patterns:
                date_matches = re.finditer(pattern, html_content)
                for match in date_matches:
                    try:
                        # Parse the date based on the pattern
                        if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', match.group(0)):
                            # Handle MM/DD/YYYY or DD/MM/YYYY
                            parts = re.split(r'[/-]', match.group(0))
                            if len(parts[2]) == 2:  # Two-digit year
                                year = int("20" + parts[2])
                            else:
                                year = int(parts[2])
                                
                            # Assuming MM/DD/YYYY format for simplicity
                            month = int(parts[0])
                            day = int(parts[1])
                            
                            tweet_date = datetime(year, month, day).strftime("%Y-%m-%d")
                        else:
                            # Handle "Month DD, YYYY" format
                            month_str = match.group(1)
                            day = int(match.group(2))
                            year = int(match.group(3))
                            
                            month_map = {
                                "january": 1, "february": 2, "march": 3, "april": 4,
                                "may": 5, "june": 6, "july": 7, "august": 8,
                                "september": 9, "october": 10, "november": 11, "december": 12,
                                "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
                                "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
                            }
                            
                            month = month_map.get(month_str.lower(), 1)
                            tweet_date = datetime(year, month, day).strftime("%Y-%m-%d")
                            
                        # Only use the date if it's recent (last 7 days)
                        current_date = datetime.now().date()
                        tweet_date_obj = datetime.strptime(tweet_date, "%Y-%m-%d").date()
                        
                        delta = current_date - tweet_date_obj
                        if delta.days < 7:  # Only use dates from last 7 days
                            rankings_data["date"] = tweet_date
                            logger.info(f"Found tweet date: {tweet_date}")
                            break
                    except Exception as e:
                        logger.warning(f"Error parsing date: {str(e)}")
                        continue
            
            # Check if we found any categories
            if not rankings_data["categories"]:
                logger.error("Failed to extract any category rankings from Twitter")
                return None
                
            logger.info(f"Successfully extracted {len(rankings_data['categories'])} categories from Twitter")
            self.last_scrape_data = rankings_data
            return rankings_data
            
        except Exception as e:
            logger.error(f"Error while scraping Twitter: {str(e)}")
            return None
            
    def format_rankings_message(self, rankings_data):
        """
        Format the rankings data into a readable message
        
        Args:
            rankings_data (dict): The scraped rankings data
            
        Returns:
            str: Formatted message for display/messaging
        """
        if not rankings_data:
            return "❌ Failed to retrieve rankings data from Twitter."
            
        if "categories" not in rankings_data or not rankings_data["categories"]:
            return "❌ No ranking categories found in Twitter data."
        
        app_name = rankings_data.get("app_name", "Coinbase")
        date = rankings_data.get("date", time.strftime("%Y-%m-%d"))
        source = rankings_data.get("source", "Twitter")
        
        # Format the message
        message = f"📊 {app_name} App Rankings (from {source})\n"
        message += f"📅 Date: {date}\n\n"
        
        if not rankings_data["categories"]:
            message += "No ranking data available."
        else:
            for category in rankings_data["categories"]:
                cat_name = category.get("category", "Unknown Category")
                rank = category.get("rank", "N/A")
                message += f"🔹 {cat_name}: #{rank}\n"
        
        return message

# For testing
if __name__ == "__main__":
    scraper = TwitterScraper()
    rankings = scraper.scrape_latest_rankings()
    
    if rankings:
        message = scraper.format_rankings_message(rankings)
        print(message)
    else:
        print("Failed to scrape rankings data from Twitter")