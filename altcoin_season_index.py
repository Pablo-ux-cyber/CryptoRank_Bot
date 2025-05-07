import os
import requests
import logging
import time
from datetime import datetime
from logger import logger

class AltcoinSeasonIndex:
    def __init__(self):
        """
        Initialization of Altcoin Season Index module
        
        The system uses the following signals to describe market conditions:
        - 🔴 No altseason (<25%): Bitcoin strongly dominates returns
        - 🟠 Weak altseason (25%-50%): Some altcoins outperform Bitcoin
        - 🟡 Moderate altseason (50%-75%): Many altcoins outperform Bitcoin
        - 🟢 Strong altseason (>75%): Most altcoins outperform Bitcoin
        """
        self.logger = logger
        
        # Import configuration from config.py
        try:
            from config import ASI_VS_CURRENCY, ASI_TOP_N, ASI_PERIOD, ASI_THRESHOLD_STRONG, ASI_THRESHOLD_MODERATE, ASI_THRESHOLD_WEAK
            self.vs_currency = ASI_VS_CURRENCY
            self.top_n = ASI_TOP_N
            self.period = ASI_PERIOD
            self.thresholds = {
                'strong': ASI_THRESHOLD_STRONG,
                'moderate': ASI_THRESHOLD_MODERATE,
                'weak': ASI_THRESHOLD_WEAK,
            }
        except ImportError:
            # Fallback to environment variables if config.py import fails
            self.vs_currency = os.getenv('ASI_VS_CURRENCY', 'usd')
            self.top_n = int(os.getenv('ASI_TOP_N', '50'))
            self.period = os.getenv('ASI_PERIOD', '30d')
            self.thresholds = {
                'strong': float(os.getenv('ASI_THRESHOLD_STRONG', '0.75')),
                'moderate': float(os.getenv('ASI_THRESHOLD_MODERATE', '0.50')),
                'weak': float(os.getenv('ASI_THRESHOLD_WEAK', '0.25')),
            }
        
        self.logger.info(f"Initialized Altcoin Season Index module with top {self.top_n} coins, {self.period} period")
        self.logger.info(f"Thresholds: Strong={self.thresholds['strong']}, Moderate={self.thresholds['moderate']}, Weak={self.thresholds['weak']}")

    def fetch_market_data(self):
        """
        Fetches market data for top N coins from CoinGecko API
        
        Returns:
            list: List of coin data dictionaries or None if error
        """
        url = 'https://api.coingecko.com/api/v3/coins/markets'
        params = {
            'vs_currency': self.vs_currency,
            'order': 'market_cap_desc',
            'per_page': self.top_n,
            'page': 1,
            'price_change_percentage': '30d'  # Hardcoded 30d to match expected API format
        }
        
        try:
            self.logger.info(f"Fetching market data for top {self.top_n} coins from CoinGecko")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Error fetching market data from CoinGecko: {str(e)}")
            return None

    def calculate_altseason_index(self, data):
        """
        Calculates the Altcoin Season Index based on market data
        
        Args:
            data (list): List of coin data dictionaries from CoinGecko API
            
        Returns:
            tuple: (index_value, btc_performance) or (None, None) if error
        """
        if not data:
            return None, None
        
        # Find BTC performance
        btc = next((c for c in data if c['symbol'] == 'btc'), None)
        if not btc:
            self.logger.error("BTC not found in market data")
            return None, None
        
        # Get BTC performance for the period
        period_key = 'price_change_percentage_30d_in_currency'  # Hardcoded to match API response
        btc_perf = btc.get(period_key, 0)
        if btc_perf is None:
            btc_perf = 0
        
        # Count how many coins outperformed BTC
        ahead = 0
        total_with_data = 0
        
        for coin in data:
            perf = coin.get(period_key)
            if perf is not None:
                total_with_data += 1
                if perf > btc_perf:
                    ahead += 1
        
        if total_with_data == 0:
            self.logger.error("No coins with performance data found")
            return None, None
        
        # Calculate the index
        index = ahead / total_with_data
        
        self.logger.info(f"Altcoin Season Index: {index:.2f}, BTC performance: {btc_perf:.2f}%")
        return index, btc_perf

    def get_altseason_index(self):
        """
        Gets the current Altcoin Season Index
        
        Returns:
            dict: Dictionary with index data or None in case of error
        """
        try:
            # Fetch market data
            market_data = self.fetch_market_data()
            if not market_data:
                self.logger.error("Failed to fetch market data")
                return None
            
            # Calculate the index
            index, btc_perf = self.calculate_altseason_index(market_data)
            if index is None:
                self.logger.error("Failed to calculate Altcoin Season Index")
                return None
            
            # Determine market signal based on the index
            signal, status, description = self._determine_market_signal(index)
            
            # Create result object
            result = {
                'index': float(round(float(index), 2)) if index is not None else 0.0,
                'btc_performance': float(round(float(btc_perf), 2)) if btc_perf is not None else 0.0,
                'signal': signal,
                'status': status,
                'description': description,
                'timestamp': int(time.time()),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'period': self.period,
                'coins_analyzed': self.top_n
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting Altcoin Season Index: {str(e)}")
            return None

    def _determine_market_signal(self, index):
        """
        Determines market signal based on the Altcoin Season Index value
        
        Args:
            index (float): Altcoin Season Index value [0.0, 1.0]
            
        Returns:
            tuple: (emoji_signal, text_status, text_description)
        """
        if index >= self.thresholds['strong']:
            return "🟢", "Strong Altseason", "Most altcoins outperform Bitcoin"
        elif index >= self.thresholds['moderate']:
            return "🟡", "Moderate Altseason", "Many altcoins outperform Bitcoin"
        elif index >= self.thresholds['weak']:
            return "🟠", "Weak Altseason", "Some altcoins outperform Bitcoin"
        else:
            return "🔴", "No Altseason", "Bitcoin dominates returns"

    def format_altseason_message(self, altseason_data=None):
        """
        Formats Altcoin Season Index data into a simplified message for Telegram
        
        Args:
            altseason_data (dict, optional): Altcoin Season Index data or None to fetch new data
            
        Returns:
            str: Formatted message or None if error
        """
        if not altseason_data:
            altseason_data = self.get_altseason_index()
            
        if not altseason_data:
            return None
        
        # Более компактный формат сообщения
        # Эмодзи + короткое название индикатора + процент + BTC performance
        index_percent = f"{altseason_data['index']*100:.0f}"
        btc_perf = f"{altseason_data['btc_performance']:+.1f}"
        
        # Формируем компактное сообщение с основными данными
        message = f"{altseason_data['signal']} {altseason_data['status']} ({index_percent}%, BTC: {btc_perf}%)"
            
        return message