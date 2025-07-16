import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Optional, Callable
import concurrent.futures
import threading
import os

class CryptoAnalyzer:
    """
    Анализатор криптовалютного рынка для расчета индикатора ширины рынка
    Использует CryptoCompare API
    """
    
    def __init__(self, cache=None):
        self.cryptocompare_url = "https://min-api.cryptocompare.com/data"
        self.cache = cache
        self.request_delay = 0.2  # 200ms между запросами для скорости
        self.api_key = os.environ.get('CRYPTOCOMPARE_API_KEY')
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Список топ криптовалют (символы) - обновленный список из 50 монет по вашему файлу (убираем дубликат NEAR в строке 40)
        self.top_cryptos = [
            'BTC', 'ETH', 'BNB', 'XRP', 'SOL', 'ADA', 'DOGE', 'DOT', 'MATIC', 'LTC',
            'LINK', 'BCH', 'XLM', 'ALGO', 'AVAX', 'ATOM', 'TRX', 'FIL', 'ICP', 'NEAR',
            'VET', 'TON', 'EOS', 'XMR', 'APT', 'AXS', 'FTM', 'SUI', 'THETA', 'XTZ',
            'HBAR', 'FLOW', 'CRO', 'OP', 'STX', 'EGLD', 'KLAY', 'CHZ', 'APE', 'AR',
            'GRT', 'ZEC', 'MKR', 'ENJ', 'XDC', 'RPL', 'BTT', 'SAND', 'MANA'
        ]
    
    def _make_request(self, url: str, params: dict = None) -> Optional[dict]:
        """
        Выполнение HTTP запроса с обработкой ошибок и соблюдением лимитов
        """
        try:
            time.sleep(self.request_delay)
            
            # Добавляем API ключ если доступен
            if params is None:
                params = {}
            if self.api_key:
                params['api_key'] = self.api_key
                self.logger.info(f"Использую API ключ для запроса к {url}")
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 429:
                self.logger.warning("Превышен лимит запросов, ожидание 30 секунд...")
                time.sleep(30)
                return self._make_request(url, params)
            
            response.raise_for_status()
            data = response.json()
            
            # Проверка на ошибки CryptoCompare API
            if data.get('Response') == 'Error':
                error_msg = data.get('Message', 'Unknown error')
                self.logger.error(f"CryptoCompare API Error: {error_msg}")
                
                # Если превышен лимит, ждем дольше
                if "rate limit" in error_msg.lower() or "upgrade your account" in error_msg.lower():
                    self.logger.warning("Превышен лимит API, ждем 60 секунд...")
                    time.sleep(60)
                    return self._make_request(url, params)
                    
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка запроса к {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка: {e}")
            return None
    
    def get_top_coins(self, limit: int = 49) -> List[Dict]:
        """
        Получение списка топ криптовалют (используем полный список из 49 монет)
        """
        # Используем предопределенный список топ монет - всегда все 49 монет
        coins = []
        for i, symbol in enumerate(self.top_cryptos):
            coins.append({
                'symbol': symbol,
                'name': symbol,  # Для упрощения
                'market_cap_rank': i + 1
            })
        
        self.logger.info(f"Получено {len(coins)} топ монет из предопределенного списка")
        return coins
    
    def get_coin_history(self, coin_symbol: str, days: int) -> Optional[pd.DataFrame]:
        """
        Получение исторических данных для одной монеты через CryptoCompare API
        Всегда загружает свежие данные, кеширование отключено
        """
        
        # Используем CryptoCompare API для исторических данных
        url = f"{self.cryptocompare_url}/v2/histoday"
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
        if len(prices_data) < days * 0.3:  # Снижаем требование до 30% для загрузки всех монет
            self.logger.warning(f"Недостаточно данных для {coin_symbol}: {len(prices_data)} дней")
            return None
        
        df_data = []
        for item in prices_data:
            if item['close'] > 0:  # Фильтруем нулевые цены
                df_data.append({
                    'date': datetime.fromtimestamp(item['time']).date(),
                    'price': item['close']
                })
        
        if len(df_data) < days * 0.3:  # Снижаем требование до 30% для загрузки всех монет
            self.logger.warning(f"Недостаточно валидных данных для {coin_symbol}")
            return None
        
        df = pd.DataFrame(df_data)
        df = df.sort_values('date').reset_index(drop=True)
        df = df.drop_duplicates(subset=['date']).reset_index(drop=True)
        
        self.logger.info(f"Загружены свежие данные для {coin_symbol}: {len(df)} записей")
        return df
    
    def _load_single_coin_data(self, coin: Dict, days: int) -> tuple:
        """
        Загрузка данных для одной монеты (для параллельной обработки)
        """
        coin_symbol = coin['symbol']
        try:
            df = self.get_coin_history(coin_symbol, days)
            if df is not None and len(df) >= days * 0.3:  # Снижаем требование до 30% для загрузки всех монет
                return coin_symbol, df, True
            else:
                return coin_symbol, None, False
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке данных для {coin_symbol}: {str(e)}")
            return coin_symbol, None, False

    def load_historical_data(self, coins: List[Dict], days: int, 
                           progress_callback: Optional[Callable] = None) -> Dict[str, pd.DataFrame]:
        """
        Параллельная загрузка исторических данных для всех монет
        Всегда загружает свежие данные, кеширование отключено
        """
        historical_data = {}
        total_coins = len(coins)
        successful_loads = 0
        failed_loads = 0
        
        self.logger.info(f"Начинаем пачечную загрузку свежих данных для {total_coins} монет (пачки по 7)...")
        
        # Пачечная загрузка по 7 монет с паузами между пачками
        batch_size = 7
        for batch_start in range(0, total_coins, batch_size):
            batch_end = min(batch_start + batch_size, total_coins)
            batch_coins = coins[batch_start:batch_end]
            
            self.logger.info(f"Загружаем пачку {batch_start//batch_size + 1} ({batch_start + 1}-{batch_end} из {total_coins})")
            
            # Параллельная загрузка внутри пачки
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_coin = {
                    executor.submit(self._load_single_coin_data, coin, days): coin 
                    for coin in batch_coins
                }
                
                for future in concurrent.futures.as_completed(future_to_coin):
                    coin_symbol, df, success = future.result()
                    completed = successful_loads + failed_loads + 1
                    
                    # Обновление прогресса
                    if progress_callback:
                        progress = (completed / total_coins) * 100
                        progress_callback(progress)
                    
                    if success and df is not None:
                        historical_data[coin_symbol] = df
                        successful_loads += 1
                        self.logger.info(f"✅ {coin_symbol} ({completed}/{total_coins})")
                    else:
                        failed_loads += 1
                        self.logger.warning(f"❌ {coin_symbol} - недостаточно данных ({completed}/{total_coins})")
            
            # Пауза между пачками (но не после последней)
            if batch_end < total_coins:
                time.sleep(1.0)  # Пауза 1 секунда между пачками
                self.logger.info("Пауза между пачками...")
        
        self.logger.info(f"Пачечная загрузка завершена: {successful_loads} успешно, {failed_loads} неудачно из {total_coins} монет")
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
                df_indexed = df[['date', 'above_ma']].set_index('date')
                coin_data[coin_symbol] = df_indexed
        
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
            # Устанавливаем дату как индекс для правильной работы с временными рядами
            result_df = result_df.set_index('date')
        
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