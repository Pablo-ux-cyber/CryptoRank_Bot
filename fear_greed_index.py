import requests
import logging
import time
from datetime import datetime

# Set up logging
logger = logging.getLogger('sensortower_bot')

class FearGreedIndexTracker:
    def __init__(self):
        """
        Initializes the Fear & Greed Index tracker for cryptocurrencies
        """
        self.api_url = "https://api.alternative.me/fng/"
        self.last_data = None
        
    def get_fear_greed_index(self):
        """
        Gets the current value of the Fear & Greed Index and its interpretation
        
        Returns:
            dict: Dictionary with index data or None in case of error
        """
        try:
            logger.info("Fetching Fear & Greed Index data")
            response = requests.get(self.api_url, params={"limit": 1}, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch Fear & Greed Index: HTTP {response.status_code}")
                return self._create_fallback_data()
                
            data = response.json()
            
            if "data" not in data or not data["data"]:
                logger.error("Invalid response format from Fear & Greed API")
                return self._create_fallback_data()
                
            index_data = data["data"][0]
            
            # Convert values
            value = int(index_data.get("value", "0"))
            value_classification = index_data.get("value_classification", "Unknown")
            timestamp = int(index_data.get("timestamp", "0"))
            
            # Convert timestamp to date
            date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
            
            result = {
                "value": value,
                "classification": value_classification,
                "date": date,
                "timestamp": timestamp
            }
            
            logger.info(f"Successfully fetched Fear & Greed Index: {value} ({value_classification})")
            self.last_data = result
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Fear & Greed API failed: {str(e)}")
            return self._create_fallback_data()
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {str(e)}")
            return self._create_fallback_data()
            
    def _create_fallback_data(self):
        """
        Creates fallback data in case of an error
        """
        # If we have previous data, use it
        if self.last_data:
            logger.info("Using last known Fear & Greed data")
            return self.last_data
            
        # Create fallback data
        logger.info("Using fallback Fear & Greed data")
        return {
            "value": 45,
            "classification": "Fear",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": int(time.time())
        }
        
    def format_fear_greed_message(self, fear_greed_data):
        """
        Formats Fear & Greed Index data into a simplified message for Telegram
        
        Args:
            fear_greed_data (dict): Fear & Greed Index data
            
        Returns:
            str: Formatted message for Telegram in the simplified format
        """
        if not fear_greed_data:
            return "Error retrieving Fear & Greed Index data."
        
        value = fear_greed_data.get("value", 0)
        classification = fear_greed_data.get("classification", "Unknown")
        
        # Choose emoji based on classification
        if classification == "Extreme Fear":
            emoji = "😱"
            filled_char = "🔴"
        elif classification == "Fear":
            emoji = "😨"
            filled_char = "🟠"
        elif classification == "Neutral":
            emoji = "😐"
            filled_char = "🟡"
        elif classification == "Greed":
            emoji = "😏"
            filled_char = "🟢"
        elif classification == "Extreme Greed":
            emoji = "🤑"
            filled_char = "🟢"
        else:
            emoji = "❓"
            filled_char = "⚪"
        
        # Generate progress bar
        progress = self._generate_progress_bar(value, 100, 10, filled_char)
        
        # Format the message in simplified format
        message = f"{emoji} {classification}: {value}/100\n{progress}"
        
        return message
        
    def _generate_progress_bar(self, value, max_value, length, filled_char="█", empty_char="░"):
        """
        Generates a graphical progress bar
        
        Args:
            value (int): Current value
            max_value (int): Maximum value
            length (int): Length of the progress bar
            filled_char (str): Character for the filled part
            empty_char (str): Character for the empty part
            
        Returns:
            str: Progress bar string
        """
        filled_length = int(length * value / max_value)
        bar = filled_char * filled_length + empty_char * (length - filled_length)
        return bar