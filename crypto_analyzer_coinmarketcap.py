import os
import requests
import pandas as pd
import numpy as np
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

class CryptoAnalyzerCMC:
    """
    Анализатор криптовалютного рынка для расчета индикатора ширины рынка
    Использует CoinMarketCap API
    """
    
    def __init__(self, cache=None):
        self.coinmarketcap_url = "https://pro-api.coinmarketcap.com/v1"
        self.cache = cache
        self.request_delay = 1.0  # 1000ms между запросами для стабильности
        self.api_key = os.environ.get('COINMARKETCAP_API_KEY')
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Список топ криптовалют (символы) - обновленный список из 49 монет
        self.top_cryptos = [
            'BTC', 'ETH', 'BNB', 'XRP', 'SOL', 'ADA', 'DOGE', 'DOT', 'MATIC', 'LTC',
            'LINK', 'BCH', 'XLM', 'ALGO', 'AVAX', 'ATOM', 'TRX', 'FIL', 'ICP', 'NEAR',
            'VET', 'TON', 'EOS', 'XMR', 'APT', 'AXS', 'FTM', 'SUI', 'THETA', 'XTZ',
            'HBAR', 'FLOW', 'CRO', 'OP', 'STX', 'EGLD', 'KLAY', 'CHZ', 'APE', 'AR',
            'GRT', 'ZEC', 'MKR', 'ENJ', 'XDC', 'RPL', 'BTT', 'SAND', 'MANA'
        ]
        
        # Маппинг символов в ID для CoinMarketCap
        self.symbol_to_id = {
            'BTC': 1, 'ETH': 1027, 'BNB': 1839, 'XRP': 52, 'SOL': 5426, 'ADA': 2010,
            'DOGE': 74, 'DOT': 6636, 'MATIC': 3890, 'LTC': 2, 'LINK': 1975, 'BCH': 1831,
            'XLM': 512, 'ALGO': 4030, 'AVAX': 5805, 'ATOM': 3794, 'TRX': 1958, 'FIL': 5718,
            'ICP': 8916, 'NEAR': 6535, 'VET': 3077, 'TON': 11419, 'EOS': 1765, 'XMR': 328,
            'APT': 21794, 'AXS': 6783, 'FTM': 3513, 'SUI': 20947, 'THETA': 2416, 'XTZ': 2011,
            'HBAR': 4642, 'FLOW': 4558, 'CRO': 3635, 'OP': 11840, 'STX': 4847, 'EGLD': 6892,
            'KLAY': 4256, 'CHZ': 4066, 'APE': 18876, 'AR': 5632, 'GRT': 6719, 'ZEC': 1437,
            'MKR': 1518, 'ENJ': 2130, 'XDC': 2634, 'RPL': 2943, 'BTT': 16086, 'SAND': 6210,
            'MANA': 1966
        }
    
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """
        Выполнение HTTP запроса с обработкой ошибок и соблюдением лимитов
        """
        try:
            time.sleep(self.request_delay)
            
            # Добавляем API ключ
            headers = {
                'X-CMC_PRO_API_KEY': self.api_key,
                'Accept': 'application/json',
                'Accept-Encoding': 'deflate, gzip'
            }
            
            if params is None:
                params = {}
            
            url = f"{self.coinmarketcap_url}/{endpoint}"
            self.logger.info(f"Запрос к CoinMarketCap API: {url}")
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 429:
                self.logger.warning("Превышен лимит запросов CoinMarketCap, ожидание 60 секунд...")
                time.sleep(60)
                return self._make_request(endpoint, params)
            
            response.raise_for_status()
            data = response.json()
            
            # Проверка на ошибки CoinMarketCap API
            if data.get('status', {}).get('error_code') != 0:
                error_msg = data.get('status', {}).get('error_message', 'Unknown error')
                self.logger.error(f"CoinMarketCap API Error: {error_msg}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка запроса к CoinMarketCap API: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка: {e}")
            return None
    
    def get_top_coins(self, limit: int = 49) -> List[Dict]:
        """
        Получение списка топ криптовалют
        """
        coins = []
        for i, symbol in enumerate(self.top_cryptos):
            coins.append({
                'symbol': symbol,
                'name': symbol,
                'market_cap_rank': i + 1,
                'id': self.symbol_to_id.get(symbol, 0)
            })
        
        self.logger.info(f"Получено {len(coins)} топ монет из предопределенного списка")
        return coins
    
    def get_coin_history(self, coin_symbol: str, days: int) -> Optional[pd.DataFrame]:
        """
        Получение исторических данных для одной монеты через CoinMarketCap API
        """
        coin_id = self.symbol_to_id.get(coin_symbol)
        if not coin_id:
            self.logger.warning(f"ID не найден для {coin_symbol}")
            return None
        
        # Используем quotes/historical endpoint
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 30)  # Берем с запасом
        
        params = {
            'id': coin_id,
            'time_start': start_date.strftime('%Y-%m-%d'),
            'time_end': end_date.strftime('%Y-%m-%d'),
            'interval': 'daily'
        }
        
        data = self._make_request('cryptocurrency/quotes/historical', params)
        
        if not data or not data.get('data'):
            self.logger.warning(f"Нет данных для {coin_symbol}")
            return None
        
        # Обработка данных
        quotes = data['data'].get('quotes', [])
        if not quotes:
            self.logger.warning(f"Нет котировок для {coin_symbol}")
            return None
        
        df_data = []
        for quote in quotes:
            try:
                price = quote['quote']['USD']['price']
                timestamp = quote['timestamp']
                date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date()
                
                if price > 0:
                    df_data.append({
                        'date': date,
                        'price': price
                    })
            except (KeyError, ValueError) as e:
                continue
        
        if len(df_data) < days * 0.3:
            self.logger.warning(f"Недостаточно валидных данных для {coin_symbol}")
            return None
        
        df = pd.DataFrame(df_data)
        df = df.sort_values('date').reset_index(drop=True)
        df = df.drop_duplicates(subset=['date']).reset_index(drop=True)
        
        self.logger.info(f"Загружены свежие данные для {coin_symbol}: {len(df)} записей")
        return df
    
    def _load_single_coin_data(self, coin: Dict, days: int) -> tuple:
        """
        Загрузка данных для одной монеты
        """
        coin_symbol = coin['symbol']
        try:
            df = self.get_coin_history(coin_symbol, days)
            if df is not None and len(df) >= days * 0.3:
                return coin_symbol, df, True
            else:
                return coin_symbol, None, False
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке данных для {coin_symbol}: {str(e)}")
            return coin_symbol, None, False

    def load_historical_data(self, coins: List[Dict], days: int, 
                           progress_callback: Optional[Callable] = None) -> Dict[str, pd.DataFrame]:
        """
        Последовательная загрузка исторических данных для всех монет
        """
        historical_data = {}
        total_coins = len(coins)
        successful_loads = 0
        failed_loads = 0
        
        self.logger.info(f"Начинаем последовательную загрузку данных CoinMarketCap для {total_coins} монет...")
        
        # Последовательная загрузка с паузами между запросами
        for i, coin in enumerate(coins):
            coin_symbol, df, success = self._load_single_coin_data(coin, days)
            completed = i + 1
            
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
            
            # Пауза между монетами
            if completed < total_coins:
                time.sleep(0.5)  # Дополнительная пауза между монетами
        
        self.logger.info(f"Загрузка CoinMarketCap завершена: {successful_loads} успешно, {failed_loads} неудачно из {total_coins} монет")
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
            
            # Фильтрация по периоду анализа
            df = df[(df['date'] >= pd.to_datetime(start_date)) & 
                   (df['date'] <= pd.to_datetime(end_date))]
            
            if len(df) < ma_period:
                self.logger.warning(f"Недостаточно данных для {coin_symbol} за период анализа")
                continue
            
            # Расчет скользящей средней
            df['ma'] = self.calculate_moving_average(df['price'], ma_period)
            df['above_ma'] = df['price'] > df['ma']
            
            coin_data[coin_symbol] = df
        
        if not coin_data:
            self.logger.error("Нет данных для расчета индикатора ширины рынка")
            return pd.DataFrame()
        
        # Создание индикатора ширины рынка
        all_dates = set()
        for df in coin_data.values():
            all_dates.update(df['date'].dt.date)
        
        all_dates = sorted(all_dates)
        
        # Расчет процента монет выше MA для каждой даты
        breadth_data = []
        for date in all_dates:
            coins_above_ma = 0
            total_coins = 0
            
            for coin_symbol, df in coin_data.items():
                day_data = df[df['date'].dt.date == date]
                if not day_data.empty and not pd.isna(day_data.iloc[0]['ma']):
                    total_coins += 1
                    if day_data.iloc[0]['above_ma']:
                        coins_above_ma += 1
            
            if total_coins > 0:
                percentage = (coins_above_ma / total_coins) * 100
                breadth_data.append({
                    'date': date,
                    'percentage': percentage,
                    'coins_above_ma': coins_above_ma,
                    'total_coins': total_coins
                })
        
        if not breadth_data:
            self.logger.error("Не удалось рассчитать данные индикатора ширины рынка")
            return pd.DataFrame()
        
        breadth_df = pd.DataFrame(breadth_data)
        breadth_df = breadth_df.sort_values('date').reset_index(drop=True)
        
        self.logger.info(f"Рассчитан индикатор для {len(breadth_df)} дней")
        return breadth_df
    
    def get_market_summary(self, indicator_data: pd.DataFrame) -> Dict:
        """
        Получение сводной информации о рынке
        """
        if indicator_data.empty:
            return {
                'current_percentage': 0,
                'status': 'Нет данных',
                'total_coins': 0,
                'coins_above_ma': 0
            }
        
        latest = indicator_data.iloc[-1]
        percentage = latest['percentage']
        
        # Определение статуса рынка
        if percentage >= 80:
            status = 'Overbought'
        elif percentage <= 20:
            status = 'Oversold'
        else:
            status = 'Neutral'
        
        return {
            'current_percentage': round(percentage, 1),
            'status': status,
            'total_coins': latest['total_coins'],
            'coins_above_ma': latest['coins_above_ma'],
            'date': latest['date']
        }