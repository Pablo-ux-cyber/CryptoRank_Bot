import requests
import pandas as pd
import numpy as np
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)

class MarketBreadthIndicator:
    """
    Индикатор ширины криптовалютного рынка - процент топ-50 криптовалют,
    торгующихся выше 200-дневной скользящей средней (MA200).
    """
    
    def __init__(self):
        """
        Инициализация индикатора ширины рынка
        """
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.cryptocompare_base_url = "https://min-api.cryptocompare.com/data"
        self.top_coins_count = 50
        self.ma_period = 200
        self.analysis_days = 250  # Достаточно для расчета MA200 + запас
        
        logger.info("Initialized Market Breadth Indicator module")
        logger.info(f"Parameters: Top {self.top_coins_count} coins, MA{self.ma_period} period")
    
    def get_top_coins(self, limit: int = 50) -> List[Dict]:
        """
        Получение топ-50 криптовалют по рыночной капитализации через CoinGecko API
        
        Args:
            limit (int): Количество монет для получения
            
        Returns:
            List[Dict]: Список словарей с данными о монетах
        """
        try:
            url = f"{self.coingecko_base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            coins = response.json()
            logger.info(f"Successfully fetched {len(coins)} top coins from CoinGecko")
            
            return coins
            
        except Exception as e:
            logger.error(f"Error fetching top coins from CoinGecko: {str(e)}")
            return []
    
    def get_coin_history(self, coin_symbol: str, days: int) -> Optional[pd.DataFrame]:
        """
        Получение исторических данных монеты через CryptoCompare API
        
        Args:
            coin_symbol (str): Символ монеты (например, BTC, ETH)
            days (int): Количество дней для получения данных
            
        Returns:
            Optional[pd.DataFrame]: DataFrame с историческими данными или None
        """
        try:
            url = f"{self.cryptocompare_base_url}/v2/histoday"
            params = {
                'fsym': coin_symbol.upper(),
                'tsym': 'USD',
                'limit': days,
                'toTs': int(time.time())
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('Response') == 'Error':
                logger.warning(f"CryptoCompare API error for {coin_symbol}: {data.get('Message', 'Unknown error')}")
                return None
            
            # Извлекаем данные из ответа
            historical_data = data.get('Data', {}).get('Data', [])
            
            if not historical_data:
                logger.warning(f"No historical data found for {coin_symbol}")
                return None
            
            # Создаем DataFrame
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['time'], unit='s')
            df['close'] = df['close'].astype(float)
            
            # Сортируем по дате
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.debug(f"Successfully fetched {len(df)} days of data for {coin_symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching history for {coin_symbol}: {str(e)}")
            return None
    
    def calculate_ma200(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Расчет 200-дневной скользящей средней
        
        Args:
            df (pd.DataFrame): DataFrame с историческими данными
            
        Returns:
            pd.DataFrame: DataFrame с добавленной колонкой MA200
        """
        if len(df) < self.ma_period:
            logger.warning(f"Not enough data for MA{self.ma_period} calculation: {len(df)} days")
            return df
        
        df = df.copy()
        df['ma200'] = df['close'].rolling(window=self.ma_period).mean()
        df['above_ma200'] = df['close'] > df['ma200']
        
        return df
    
    def calculate_market_breadth(self) -> Optional[Dict]:
        """
        Расчет индикатора ширины рынка
        
        Returns:
            Optional[Dict]: Словарь с результатами анализа или None при ошибке
        """
        try:
            logger.info("Starting market breadth calculation...")
            
            # Получаем список топ-50 монет
            top_coins = self.get_top_coins(self.top_coins_count)
            
            if not top_coins:
                logger.error("Failed to get top coins list")
                return None
            
            # Анализируем каждую монету
            results = []
            successful_analyses = 0
            
            for i, coin in enumerate(top_coins, 1):
                coin_symbol = coin.get('symbol', '').upper()
                coin_name = coin.get('name', 'Unknown')
                
                logger.info(f"Analyzing {i}/{len(top_coins)}: {coin_name} ({coin_symbol})")
                
                # Получаем исторические данные
                historical_data = self.get_coin_history(coin_symbol, self.analysis_days)
                
                if historical_data is None:
                    logger.warning(f"Skipping {coin_symbol} due to data unavailability")
                    continue
                
                # Рассчитываем MA200
                data_with_ma = self.calculate_ma200(historical_data)
                
                # Проверяем последнее значение
                if len(data_with_ma) > 0:
                    latest_data = data_with_ma.iloc[-1]
                    
                    if pd.notna(latest_data.get('ma200')):
                        is_above_ma200 = latest_data['above_ma200']
                        current_price = latest_data['close']
                        ma200_value = latest_data['ma200']
                        
                        results.append({
                            'symbol': coin_symbol,
                            'name': coin_name,
                            'current_price': current_price,
                            'ma200': ma200_value,
                            'above_ma200': is_above_ma200,
                            'distance_from_ma': ((current_price - ma200_value) / ma200_value) * 100
                        })
                        
                        successful_analyses += 1
                        logger.debug(f"{coin_symbol}: {'Above' if is_above_ma200 else 'Below'} MA200")
                    else:
                        logger.warning(f"Could not calculate MA200 for {coin_symbol}")
                
                # Небольшая задержка между запросами
                time.sleep(0.1)
            
            if successful_analyses == 0:
                logger.error("No successful analyses completed")
                return None
            
            # Рассчитываем итоговый индикатор
            above_ma200_count = sum(1 for r in results if r['above_ma200'])
            total_analyzed = len(results)
            breadth_percentage = (above_ma200_count / total_analyzed) * 100
            
            # Определяем состояние рынка
            market_condition = self._interpret_market_condition(breadth_percentage)
            
            logger.info(f"Market breadth calculation completed successfully")
            logger.info(f"Result: {breadth_percentage:.1f}% ({above_ma200_count}/{total_analyzed}) - {market_condition}")
            
            return {
                'timestamp': datetime.now(),
                'breadth_percentage': breadth_percentage,
                'above_ma200_count': above_ma200_count,
                'total_analyzed': total_analyzed,
                'market_condition': market_condition,
                'detailed_results': results
            }
            
        except Exception as e:
            logger.error(f"Error in market breadth calculation: {str(e)}")
            return None
    
    def _interpret_market_condition(self, percentage: float) -> str:
        """
        Интерпретация состояния рынка на основе процента
        
        Args:
            percentage (float): Процент монет выше MA200
            
        Returns:
            str: Описание состояния рынка
        """
        if percentage >= 80:
            return "Strong Bull Market"
        elif percentage >= 60:
            return "Bull Market"
        elif percentage >= 40:
            return "Neutral Market"
        elif percentage >= 20:
            return "Bear Market"
        else:
            return "Strong Bear Market"
    
    def get_market_breadth_indicator(self) -> Optional[Dict]:
        """
        Получение индикатора ширины рынка
        
        Returns:
            Optional[Dict]: Словарь с данными индикатора или None при ошибке
        """
        try:
            logger.info("Getting market breadth indicator...")
            result = self.calculate_market_breadth()
            
            if result is None:
                logger.error("Failed to calculate market breadth")
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting market breadth indicator: {str(e)}")
            return None
    
    def format_market_breadth_message(self, breadth_data: Optional[Dict] = None) -> Optional[str]:
        """
        Форматирует данные индикатора ширины рынка в сообщение для Telegram
        
        Args:
            breadth_data (Optional[Dict]): Данные индикатора или None для получения новых данных
            
        Returns:
            Optional[str]: Форматированное сообщение или None если данные недоступны
        """
        try:
            if breadth_data is None:
                breadth_data = self.get_market_breadth_indicator()
            
            if breadth_data is None:
                logger.warning("No market breadth data available for formatting")
                return None
            
            # Определяем emoji для состояния рынка
            percentage = breadth_data['breadth_percentage']
            if percentage >= 80:
                status_emoji = "🟢"
            elif percentage >= 60:
                status_emoji = "🟢"
            elif percentage >= 40:
                status_emoji = "🟡"
            elif percentage >= 20:
                status_emoji = "🔴"
            else:
                status_emoji = "🔴"
            
            # Создаем прогресс-бар
            progress_bar = self._generate_progress_bar(percentage, 100, 20)
            
            # Форматируем сообщение
            message = f"""
📊 **Market Breadth Indicator**

{status_emoji} **{breadth_data['breadth_percentage']:.1f}%** of top-{breadth_data['total_analyzed']} coins above MA200

📈 **Market Status**: {breadth_data['market_condition']}

{progress_bar}

💹 **Details**:
• Above MA200: {breadth_data['above_ma200_count']} coins
• Below MA200: {breadth_data['total_analyzed'] - breadth_data['above_ma200_count']} coins
• Analysis Period: {self.ma_period} days moving average

🗓 **Updated**: {breadth_data['timestamp'].strftime('%Y-%m-%d %H:%M UTC')}
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting market breadth message: {str(e)}")
            return None
    
    def _generate_progress_bar(self, value: float, max_value: float, length: int, 
                              filled_char: str = "█", empty_char: str = "░") -> str:
        """
        Генерирует графический прогресс-бар
        
        Args:
            value (float): Текущее значение
            max_value (float): Максимальное значение
            length (int): Длина прогресс-бара
            filled_char (str): Символ для заполненной части
            empty_char (str): Символ для пустой части
            
        Returns:
            str: Строка прогресс-бара
        """
        try:
            percentage = min(value / max_value, 1.0)
            filled_length = int(length * percentage)
            empty_length = length - filled_length
            
            progress_bar = filled_char * filled_length + empty_char * empty_length
            return f"{progress_bar} {value:.1f}%"
            
        except Exception as e:
            logger.error(f"Error generating progress bar: {str(e)}")
            return f"{value:.1f}%"