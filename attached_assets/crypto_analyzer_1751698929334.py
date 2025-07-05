import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Optional, Callable

class CryptoAnalyzer:
    """
    Анализатор криптовалютного рынка для расчета индикатора ширины рынка
    """
    
    def __init__(self, cache=None):
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        self.cryptocompare_url = "https://min-api.cryptocompare.com/data/v2"
        self.cache = cache
        self.request_delay = 1.0  # Задержка между запросами (секунды)
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, url: str, params: dict = None) -> Optional[dict]:
        """
        Выполнение HTTP запроса с обработкой ошибок и соблюдением лимитов
        """
        try:
            time.sleep(self.request_delay)  # Соблюдение лимитов API
            
            response = requests.get(url, params=params or {}, timeout=30)
            
            if response.status_code == 429:  # Too Many Requests
                self.logger.warning("Превышен лимит запросов, ожидание...")
                time.sleep(60)  # Ждем минуту
                return self._make_request(url, params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка запроса к {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка: {e}")
            return None
    
    def get_top_coins(self, limit: int = 50) -> List[Dict]:
        """
        Получение списка топ криптовалют по капитализации
        """
        url = f"{self.coingecko_url}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': limit,
            'page': 1,
            'sparkline': False
        }
        
        data = self._make_request(url, params)
        if not data:
            return []
        
        coins = []
        for coin in data:
            coins.append({
                'id': coin['id'],
                'symbol': coin['symbol'].upper(),
                'name': coin['name'],
                'market_cap_rank': coin['market_cap_rank']
            })
        
        self.logger.info(f"Получено {len(coins)} топ монет")
        return coins
    
    def get_coin_history(self, coin_symbol: str, days: int) -> Optional[pd.DataFrame]:
        """
        Получение исторических данных для одной монеты через CryptoCompare API
        """
        # Проверка кеша
        if self.cache:
            cached_data = self.cache.get_coin_data(coin_symbol, days)
            if cached_data is not None:
                return cached_data
        
        # Используем CryptoCompare API для исторических данных
        url = f"{self.cryptocompare_url}/histoday"
        params = {
            'fsym': coin_symbol,
            'tsym': 'USD',
            'limit': days,
            'aggregate': 1
        }
        
        data = self._make_request(url, params)
        if not data or 'Data' not in data or 'Data' not in data['Data']:
            self.logger.warning(f"Не удалось получить данные для {coin_symbol}")
            return None
        
        # Обработка данных
        prices_data = data['Data']['Data']
        if len(prices_data) < days * 0.8:  # Если данных меньше 80% от запрошенного
            self.logger.warning(f"Недостаточно данных для {coin_symbol}: {len(prices_data)} дней")
            return None
        
        df_data = []
        for item in prices_data:
            df_data.append({
                'date': datetime.fromtimestamp(item['time']).date(),
                'price': item['close']
            })
        
        df = pd.DataFrame(df_data)
        df = df.sort_values('date').reset_index(drop=True)
        
        # Сохранение в кеш
        if self.cache:
            self.cache.save_coin_data(coin_symbol, df, days)
        
        return df
    
    def load_historical_data(self, coins: List[Dict], days: int, 
                           progress_callback: Optional[Callable] = None) -> Dict[str, pd.DataFrame]:
        """
        Загрузка исторических данных для всех монет
        """
        historical_data = {}
        total_coins = len(coins)
        
        for i, coin in enumerate(coins):
            coin_symbol = coin['symbol']
            
            # Обновление прогресса
            if progress_callback:
                progress = (i / total_coins) * 100
                progress_callback(progress)
            
            self.logger.info(f"Загрузка данных для {coin['name']} ({coin_symbol}) ({i+1}/{total_coins})")
            
            df = self.get_coin_history(coin_symbol, days)
            if df is not None and len(df) >= days * 0.8:
                historical_data[coin_symbol] = df
            else:
                self.logger.warning(f"Пропуск {coin['name']} - недостаточно данных")
        
        self.logger.info(f"Загружены данные для {len(historical_data)} из {total_coins} монет")
        return historical_data
    
    def calculate_moving_average(self, prices: pd.Series, window: int) -> pd.Series:
        """
        Расчет скользящей средней
        """
        return prices.rolling(window=window, min_periods=window).mean()
    
    def calculate_market_breadth(self, historical_data: Dict[str, pd.DataFrame], 
                               ma_period: int = 200, analysis_days: int = 365) -> pd.DataFrame:
        """
        Расчет индикатора ширины рынка
        """
        if not historical_data:
            return pd.DataFrame()
        
        # Определение периода анализа
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=analysis_days)
        
        # Подготовка данных для анализа
        coin_data = {}
        for coin_symbol, df in historical_data.items():
            df = df.copy()
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Расчет MA
            df['ma'] = self.calculate_moving_average(df['price'], ma_period)
            df['above_ma'] = df['price'] > df['ma']
            
            # Фильтрация по датам
            df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]
            
            if len(df) > 0:
                coin_data[coin_symbol] = df[['date', 'above_ma']].set_index('date')
        
        if not coin_data:
            return pd.DataFrame()
        
        # Объединение данных по датам
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        result = []
        
        for date in all_dates:
            above_ma_count = 0
            total_count = 0
            
            for coin_symbol, df in coin_data.items():
                if date in df.index and not pd.isna(df.loc[date, 'above_ma']):
                    total_count += 1
                    if df.loc[date, 'above_ma']:
                        above_ma_count += 1
            
            if total_count > 0:
                percentage = (above_ma_count / total_count) * 100
                result.append({
                    'date': date,
                    'percentage': percentage,
                    'above_ma_count': above_ma_count,
                    'total_count': total_count
                })
        
        result_df = pd.DataFrame(result)
        if not result_df.empty:
            result_df = result_df.sort_values('date')
        
        self.logger.info(f"Рассчитан индикатор для {len(result_df)} дней")
        return result_df
    
    def get_market_summary(self, indicator_data: pd.DataFrame) -> Dict:
        """
        Получение сводной информации о рынке
        """
        if indicator_data.empty:
            return {}
        
        current_value = indicator_data['percentage'].iloc[-1]
        avg_value = indicator_data['percentage'].mean()
        std_value = indicator_data['percentage'].std()
        
        # Определение текущего состояния рынка
        if current_value >= 80:
            market_condition = "Перекупленность"
        elif current_value <= 10:
            market_condition = "Перепроданность"
        else:
            market_condition = "Нейтральная зона"
        
        # Подсчет экстремальных значений
        overbought_days = (indicator_data['percentage'] >= 80).sum()
        oversold_days = (indicator_data['percentage'] <= 10).sum()
        
        return {
            'current_value': current_value,
            'average_value': avg_value,
            'volatility': std_value,
            'market_condition': market_condition,
            'overbought_days': overbought_days,
            'oversold_days': oversold_days,
            'total_days': len(indicator_data),
            'max_value': indicator_data['percentage'].max(),
            'min_value': indicator_data['percentage'].min()
        }
