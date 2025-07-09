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
    Использует CryptoCompare API
    """
    
    def __init__(self, cache=None):
        self.cryptocompare_url = "https://min-api.cryptocompare.com/data"
        self.cache = cache
        self.request_delay = 0.05  # Уменьшаем задержку для быстрого тестирования
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Список топ криптовалют (символы) - исключены стейблкоины USDT, USDC, DAI
        self.top_cryptos = [
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'TON', 'ADA', 'SHIB', 'AVAX',
            'TRX', 'DOT', 'LINK', 'BCH', 'NEAR', 'MATIC', 'ICP', 'UNI', 'LTC', 'ETC',
            'APT', 'STX', 'CRO', 'ATOM', 'OKB', 'FIL', 'ARB', 'IMX', 'VET', 'HBAR',
            'MNT', 'OP', 'RNDR', 'GRT', 'ALGO', 'FLOW', 'MANA', 'SAND', 'XMR', 'THETA',
            'EGLD', 'AXS', 'AAVE', 'FTM', 'XTZ', 'RUNE', 'KAVA', 'INJ', 'PEPE', 'WIF'
        ]
    
    def _make_request(self, url: str, params: dict = None) -> Optional[dict]:
        """
        Выполнение HTTP запроса с обработкой ошибок и соблюдением лимитов
        """
        try:
            time.sleep(self.request_delay)
            
            response = requests.get(url, params=params or {}, timeout=30)
            
            if response.status_code == 429:
                self.logger.warning("Превышен лимит запросов, ожидание...")
                time.sleep(10)
                return self._make_request(url, params)
            
            response.raise_for_status()
            data = response.json()
            
            # Проверка на ошибки CryptoCompare API
            if data.get('Response') == 'Error':
                self.logger.error(f"CryptoCompare API Error: {data.get('Message', 'Unknown error')}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка запроса к {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка: {e}")
            return None
    
    def get_top_coins(self, limit: int = 50) -> List[Dict]:
        """
        Получение списка топ криптовалют
        """
        # Используем предопределенный список топ монет
        coins = []
        for i, symbol in enumerate(self.top_cryptos[:limit]):
            coins.append({
                'symbol': symbol,
                'name': symbol,  # Для упрощения
                'market_cap_rank': i + 1
            })
        
        self.logger.info(f"Получено {len(coins)} топ монет")
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
        if len(prices_data) < days * 0.6:  # Снижаем требование до 60%
            self.logger.warning(f"Недостаточно данных для {coin_symbol}: {len(prices_data)} дней")
            return None
        
        df_data = []
        for item in prices_data:
            if item['close'] > 0:  # Фильтруем нулевые цены
                df_data.append({
                    'date': datetime.fromtimestamp(item['time']).date(),
                    'price': item['close']
                })
        
        if len(df_data) < days * 0.6:
            self.logger.warning(f"Недостаточно валидных данных для {coin_symbol}")
            return None
        
        df = pd.DataFrame(df_data)
        df = df.sort_values('date').reset_index(drop=True)
        df = df.drop_duplicates(subset=['date']).reset_index(drop=True)
        
        self.logger.info(f"Загружены свежие данные для {coin_symbol}: {len(df)} записей")
        return df
    
    def load_historical_data(self, coins: List[Dict], days: int, 
                           progress_callback: Optional[Callable] = None) -> Dict[str, pd.DataFrame]:
        """
        Загрузка исторических данных для всех монет с пакетной обработкой
        Всегда загружает свежие данные, кеширование отключено
        """
        historical_data = {}
        total_coins = len(coins)
        successful_loads = 0
        failed_loads = 0
        
        self.logger.info(f"Начинаем пакетную загрузку свежих данных для {total_coins} монет...")
        
        # Пакетная обработка по 20 монет за раз для ускорения
        batch_size = 20
        for batch_start in range(0, total_coins, batch_size):
            batch_end = min(batch_start + batch_size, total_coins)
            batch_coins = coins[batch_start:batch_end]
            
            self.logger.info(f"Обрабатываем пакет {batch_start//batch_size + 1} ({batch_start+1}-{batch_end} из {total_coins})")
            
            for i, coin in enumerate(batch_coins):
                coin_symbol = coin['symbol']
                global_index = batch_start + i
                
                # Обновление прогресса
                if progress_callback:
                    progress = (global_index / total_coins) * 100
                    progress_callback(progress)
                
                self.logger.info(f"Загрузка данных для {coin['name']} ({coin_symbol}) ({global_index+1}/{total_coins})")
                
                try:
                    df = self.get_coin_history(coin_symbol, days)
                    if df is not None and len(df) >= days * 0.6:
                        historical_data[coin_symbol] = df
                        successful_loads += 1
                    else:
                        self.logger.warning(f"Пропуск {coin['name']} - недостаточно данных")
                        failed_loads += 1
                        
                except Exception as e:
                    self.logger.error(f"Ошибка при загрузке данных для {coin_symbol}: {str(e)}")
                    failed_loads += 1
                    
                # Небольшая пауза между запросами для стабильности
                time.sleep(self.request_delay)
            
            # Короткая пауза между пакетами
            if batch_end < total_coins:
                self.logger.info(f"Пауза между пакетами...")
                time.sleep(0.1)
        
        self.logger.info(f"Пакетная загрузка завершена: {successful_loads} успешно, {failed_loads} неудачно из {total_coins} монет")
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