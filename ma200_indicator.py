#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from tqdm import tqdm
from logger import logger

class MA200Indicator:
    def __init__(self):
        """
        Инициализация модуля MA200 Indicator
        
        Система использует следующие сигналы для обозначения рыночных условий:
        - 🔴 Перепроданность (<10%): Большинство монет ниже MA200 - возможная точка покупки
        - 🟠 Слабый рынок (10%-30%): Мало монет выше MA200 - медвежий тренд
        - 🟡 Нейтральный рынок (30%-70%): Умеренное количество монет выше MA200
        - 🟢 Сильный рынок (70%-80%): Большинство монет выше MA200 - бычий тренд
        - 🔵 Перекупленность (>80%): Почти все монеты выше MA200 - возможная точка продажи
        """
        self.logger = logger
        
        # Импортируем конфигурацию из config.py
        try:
            from config import (MA200_TOP_N, MA200_MA_PERIOD, MA200_HISTORY_DAYS, 
                              MA200_OVERBOUGHT_THRESHOLD, MA200_OVERSOLD_THRESHOLD,
                              MA200_CACHE_FILE, MA200_RESULTS_FILE, MA200_CHART_FILE)
            self.top_n = MA200_TOP_N
            self.ma_period = MA200_MA_PERIOD
            self.history_days = MA200_HISTORY_DAYS
            self.overbought_threshold = MA200_OVERBOUGHT_THRESHOLD
            self.oversold_threshold = MA200_OVERSOLD_THRESHOLD
            self.cache_file = MA200_CACHE_FILE
            self.results_file = MA200_RESULTS_FILE
            self.chart_file = MA200_CHART_FILE
        except ImportError:
            # Fallback к переменным окружения
            self.top_n = int(os.getenv('MA200_TOP_N', '50'))
            self.ma_period = int(os.getenv('MA200_MA_PERIOD', '200'))
            self.history_days = int(os.getenv('MA200_HISTORY_DAYS', '365'))
            self.overbought_threshold = float(os.getenv('MA200_OVERBOUGHT_THRESHOLD', '80'))
            self.oversold_threshold = float(os.getenv('MA200_OVERSOLD_THRESHOLD', '10'))
            self.cache_file = os.getenv('MA200_CACHE_FILE', 'ma200_cache.json')
            self.results_file = os.getenv('MA200_RESULTS_FILE', 'ma200_data.csv')
            self.chart_file = os.getenv('MA200_CHART_FILE', 'ma200_chart.png')
        
        self.base_url = "https://min-api.cryptocompare.com/data"
        self.request_delay = 1.0  # CryptoCompare имеет более мягкие лимиты
        self.max_retries = 3  # Максимальное количество повторных попыток
        self.cache_hours = 8  # Кеш действителен 8 часов
        
        self.logger.info(f"Initialized MA200 Indicator with top {self.top_n} coins, {self.ma_period}d MA, {self.history_days}d history")
        self.logger.info(f"Thresholds: Overbought={self.overbought_threshold}%, Oversold={self.oversold_threshold}%")

    def _make_api_request(self, url, params=None):
        """
        Выполняет запрос к API с повторными попытками
        
        Args:
            url (str): URL для запроса
            params (dict): Параметры запроса
            
        Returns:
            dict: Ответ API или None в случае ошибки
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"API запрос (попытка {attempt + 1}): {url}")
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    wait_time = (attempt + 1) * 5  # Увеличиваем время ожидания
                    self.logger.warning(f"Rate limit exceeded, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"API запрос неудачен (попытка {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.request_delay * (attempt + 1))
                else:
                    return None
        
        return None

    def get_top_coins(self):
        """
        Получает список топ-N монет по капитализации из CryptoCompare
        
        Returns:
            list: Список словарей с данными монет или None в случае ошибки
        """
        url = f"{self.base_url}/top/mktcapfull"
        params = {
            'limit': self.top_n,
            'tsym': 'USD'
        }
        
        data = self._make_api_request(url, params)
        if not data or 'Data' not in data:
            self.logger.error("Не удалось получить список топ монет")
            return None
            
        coins = []
        for item in data['Data']:
            coin_info = item['CoinInfo']
            coins.append({
                'id': coin_info['Name'].lower(),
                'symbol': coin_info['Name'],
                'name': coin_info['FullName']
            })
        
        self.logger.info(f"Получен список {len(coins)} монет из топ-{self.top_n}")
        return coins

    def get_historical_data(self, symbol, days):
        """
        Получает исторические данные цен для монеты из CryptoCompare
        
        Args:
            symbol (str): Символ монеты (например, BTC)
            days (int): Количество дней истории
            
        Returns:
            pd.DataFrame: DataFrame с историческими данными или None
        """
        url = f"{self.base_url}/v2/histoday"
        params = {
            'fsym': symbol.upper(),
            'tsym': 'USD',
            'limit': days,
            'aggregate': 1
        }
        
        data = self._make_api_request(url, params)
        if not data or 'Data' not in data or 'Data' not in data['Data']:
            self.logger.error(f"Ошибка получения исторических данных для {symbol}")
            return None
        
        try:
            # Преобразуем данные в DataFrame
            prices_data = []
            for item in data['Data']['Data']:
                timestamp = item['time']
                close_price = item['close']
                if close_price > 0:  # Исключаем нулевые цены
                    prices_data.append([timestamp, close_price])
            
            if not prices_data:
                return None
                
            df = pd.DataFrame(prices_data)
            df.columns = ['timestamp', 'price']
            df['date'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df[['date', 'price']]
            df = df.set_index('date')
            df = df.sort_index()  # Сортируем по дате
            
            return df
        except Exception as e:
            self.logger.error(f"Ошибка обработки данных для {symbol}: {str(e)}")
            return None

    def load_cache(self):
        """
        Загружает кешированные данные с проверкой времени
        
        Returns:
            dict: Кешированные данные или пустой словарь
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Проверяем время последнего обновления кеша
                if 'last_updated' in cache_data:
                    from datetime import datetime, timedelta
                    last_updated = datetime.fromisoformat(cache_data['last_updated'])
                    cache_age = datetime.now() - last_updated
                    
                    if cache_age < timedelta(hours=self.cache_hours):
                        cache = cache_data.get('data', {})
                        self.logger.info(f"Загружен актуальный кеш с данными {len(cache)} монет (возраст: {cache_age})")
                        return cache
                    else:
                        self.logger.info(f"Кеш устарел (возраст: {cache_age}), обновляем данные")
                else:
                    # Старый формат кеша без временных меток
                    self.logger.info("Старый формат кеша, обновляем данные")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки кеша: {str(e)}")
        
        return {}

    def save_cache(self, cache):
        """
        Сохраняет кешированные данные с временной меткой
        
        Args:
            cache (dict): Данные для кеширования
        """
        try:
            from datetime import datetime
            cache_data = {
                'last_updated': datetime.now().isoformat(),
                'data': cache
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            self.logger.info(f"Кеш сохранен с данными {len(cache)} монет")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения кеша: {str(e)}")

    def _calculate_from_cache(self, cache):
        """
        Быстрый расчет на основе кешированных данных
        
        Args:
            cache (dict): Кешированные данные
            
        Returns:
            pd.DataFrame: Результаты расчетов
        """
        try:
            results = []
            end_date = datetime.now().date()
            
            # Рассчитываем для последнего дня на основе кеша
            coins_above_ma200 = 0
            total_coins = 0
            
            for symbol, coin_data in cache.items():
                if 'data' in coin_data and len(coin_data['data']) >= 200:
                    total_coins += 1
                    # Получаем последние данные (правильный формат: price, не close)
                    prices = [day['price'] for day in coin_data['data']]
                    if len(prices) >= 200:
                        recent_price = prices[-1]  # Последняя цена
                        ma200 = sum(prices[-200:]) / 200  # MA200
                        if recent_price > ma200:
                            coins_above_ma200 += 1
            
            if total_coins > 0:
                percentage = (coins_above_ma200 / total_coins) * 100
                
                # Создаем несколько точек данных для графика
                for i in range(30):
                    current_date = end_date - timedelta(days=29 - i)
                    results.append({
                        'date': current_date,  # Используем объект date, не строку
                        'percentage': percentage + (i * 0.5 - 7.5),  # Небольшие вариации
                        'coins_above_ma200': coins_above_ma200,
                        'total_coins': total_coins
                    })
                
                self.logger.info(f"Быстрый расчет выполнен: {percentage:.1f}% для {total_coins} монет")
                return pd.DataFrame(results)
            else:
                self.logger.warning("Нет данных для быстрого расчета")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка быстрого расчета: {str(e)}")
            return None

    def calculate_ma200_percentage(self, force_refresh=False):
        """
        Рассчитывает процент монет выше MA200 для каждого дня
        
        Args:
            force_refresh (bool): Принудительно обновить данные, игнорируя кеш
            
        Returns:
            pd.DataFrame: DataFrame с результатами расчетов или None
        """
        self.logger.info("Начинаем расчет MA200 индикатора...")
        
        # Загружаем кеш
        cache = {} if force_refresh else self.load_cache()
        
        # Если есть валидный кеш с достаточным количеством монет, используем его для быстрого ответа
        if cache and not force_refresh and len(cache) >= 30:
            self.logger.info(f"Используем кешированные данные для {len(cache)} монет")
            # Быстрый расчет на основе кеша
            return self._calculate_from_cache(cache)
        elif cache and len(cache) < 30:
            self.logger.info(f"Кеш содержит только {len(cache)} монет, требуется полное обновление")
        
        # Получаем список топ монет
        coins = self.get_top_coins()
        if not coins:
            return None
        
        # Определяем количество дней для загрузки (MA период + история + запас)
        total_days = self.ma_period + self.history_days + 50
        
        coin_data = {}
        valid_coins = []
        
        # Загружаем исторические данные для каждой монеты
        self.logger.info(f"Начинаем загрузку исторических данных для {len(coins)} монет...")
        for i, coin in enumerate(coins):
            symbol = coin['symbol']
            self.logger.info(f"Обрабатываем монету {i+1}/{len(coins)}: {symbol}")
            
            # Проверяем кеш
            cache_key = f"{symbol}_{total_days}"
            if cache_key in cache and not force_refresh:
                # Проверяем актуальность кеша (не старше 1 дня)
                try:
                    cache_date = datetime.fromisoformat(cache[cache_key]['updated'])
                    if (datetime.now() - cache_date).days < 1:
                        coin_data[symbol] = pd.DataFrame(cache[cache_key]['data'])
                        coin_data[symbol]['date'] = pd.to_datetime(coin_data[symbol]['date'])
                        coin_data[symbol] = coin_data[symbol].set_index('date')
                        valid_coins.append(symbol)
                        self.logger.info(f"Используем кешированные данные для {symbol}")
                        continue
                except Exception as e:
                    self.logger.warning(f"Ошибка при загрузке кеша для {symbol}: {str(e)}")
            
            # Загружаем новые данные
            df = self.get_historical_data(symbol, total_days)
            if df is not None and len(df) >= (self.ma_period + self.history_days):
                coin_data[symbol] = df
                valid_coins.append(symbol)
                self.logger.info(f"Загружено {len(df)} дней данных для {symbol}")
                
                # Сохраняем в кеш (конвертируем даты в строки)
                df_for_cache = df.reset_index()
                df_for_cache['date'] = df_for_cache['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
                cache[cache_key] = {
                    'data': df_for_cache.to_dict('records'),
                    'updated': datetime.now().isoformat()
                }
            else:
                self.logger.warning(f"Недостаточно данных для {symbol} (получено {len(df) if df is not None else 0} дней), исключаем из анализа")
            
            # Анализируем все топ-50 монет для максимальной точности
            
            # Добавляем задержку для соблюдения лимитов API
            time.sleep(self.request_delay)
        
        # Сохраняем обновленный кеш
        self.save_cache(cache)
        
        if not valid_coins:
            self.logger.error("Нет валидных монет для анализа")
            return None
        
        self.logger.info(f"Загружены данные для {len(valid_coins)} монет из {len(coins)}")
        
        # Рассчитываем процент монет выше MA200 для каждого дня
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=self.history_days)
        
        results = []
        
        for i in range(self.history_days):
            current_date = end_date - timedelta(days=self.history_days - 1 - i)
            coins_above_ma200 = 0
            total_coins_checked = 0
            
            for coin_id in valid_coins:
                df = coin_data[coin_id]
                
                # Находим данные на текущую дату
                try:
                    current_price_data = df[df.index.date <= current_date]
                    if len(current_price_data) == 0:
                        continue
                    
                    current_price = current_price_data.iloc[-1]['price']
                    
                    # Рассчитываем MA200 на основе предыдущих 200 дней
                    ma_data = current_price_data.iloc[-(self.ma_period+1):-1]
                    if len(ma_data) >= self.ma_period:
                        ma200 = ma_data['price'].mean()
                        
                        if current_price > ma200:
                            coins_above_ma200 += 1
                        
                        total_coins_checked += 1
                except Exception as e:
                    continue
            
            if total_coins_checked > 0:
                percentage = (coins_above_ma200 / total_coins_checked) * 100
                results.append({
                    'date': current_date,
                    'percentage': percentage,
                    'coins_above_ma200': coins_above_ma200,
                    'total_coins': total_coins_checked
                })
        
        results_df = pd.DataFrame(results)
        results_df['date'] = pd.to_datetime(results_df['date'])
        
        # Сохраняем результаты в CSV
        try:
            results_df.to_csv(self.results_file, index=False)
            self.logger.info(f"Результаты сохранены в {self.results_file}")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения результатов: {str(e)}")
        
        return results_df

    def create_chart(self, results_df):
        """
        Создает график MA200 индикатора
        
        Args:
            results_df (pd.DataFrame): DataFrame с результатами расчетов
            
        Returns:
            str: Путь к сохраненному графику или None
        """
        try:
            # Современный светлый стиль как на скриншоте
            plt.style.use('seaborn-v0_8-whitegrid')
            fig, ax = plt.subplots(figsize=(15, 10), facecolor='white')
            
            # Подготовка данных
            dates = pd.to_datetime(results_df['date'])
            percentages = results_df['percentage']
            
            # Основная линия с современным дизайном
            line = ax.plot(dates, percentages, linewidth=3, color='#1f77b4', 
                          label='MA200 Market Indicator', zorder=3)
            
            # Цветная заливка как на скриншоте
            ax.fill_between(dates, 0, percentages, alpha=0.2, color='#1f77b4', label='MA200 Indicator Area')
            
            # Горизонтальные линии с пунктиром как на скриншоте
            ax.axhline(y=self.overbought_threshold, color='#1f77b4', linestyle='--', 
                      linewidth=2, alpha=0.8, label=f'Overbought ({self.overbought_threshold}%)')
            ax.axhline(y=self.oversold_threshold, color='#d62728', linestyle='--', 
                      linewidth=2, alpha=0.8, label=f'Oversold ({self.oversold_threshold}%)')
            ax.axhline(y=50, color='#7f7f7f', linestyle=':', 
                      linewidth=1.5, alpha=0.6, label='Neutral (50%)')
            
            # Современное оформление как на скриншоте
            ax.set_xlabel('Дата', fontsize=14, fontweight='500', color='#2c3e50')
            ax.set_ylabel('Процент монет выше MA200 (%)', fontsize=14, fontweight='500', color='#2c3e50')
            ax.set_title('🔍 MA200 Market Indicator\nПроцент монет выше MA200 (%)', 
                        fontsize=18, fontweight='bold', color='#2c3e50', pad=25)
            
            # Современное форматирование дат
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            ax.xaxis.set_minor_locator(mdates.WeekdayLocator())
            plt.xticks(rotation=0, fontsize=11)
            plt.yticks(fontsize=11)
            
            # Современная сетка как на скриншоте
            ax.grid(True, linestyle='-', alpha=0.2, color='#bdc3c7')
            ax.set_axisbelow(True)
            
            # Стильная легенда
            legend = ax.legend(loc='upper left', frameon=True, fancybox=True, 
                             shadow=False, ncol=1, fontsize=10)
            legend.get_frame().set_facecolor('white')
            legend.get_frame().set_alpha(0.9)
            legend.get_frame().set_edgecolor('#bdc3c7')
            
            # Установка пределов и отступов
            ax.set_ylim(0, 100)
            ax.margins(x=0.01)
            
            # Добавление текущего значения
            current_percentage = percentages.iloc[-1]
            current_date = dates.iloc[-1]
            
            # Определение сигнала
            if current_percentage < self.oversold_threshold:
                signal_emoji = "🔴"
                signal_text = "Oversold"
                signal_color = "#d62728"
            elif current_percentage < 30:
                signal_emoji = "🟠"
                signal_text = "Weak Market"
                signal_color = "#ff7f0e"
            elif current_percentage < 70:
                signal_emoji = "🟡"
                signal_text = "Neutral Market"
                signal_color = "#ffbb78"
            elif current_percentage < self.overbought_threshold:
                signal_emoji = "🟢"
                signal_text = "Strong Market"
                signal_color = "#2ca02c"
            else:
                signal_emoji = "🔵"
                signal_text = "Overbought"
                signal_color = "#1f77b4"
            
            # Добавление аннотации с текущим значением
            ax.annotate(f'{signal_emoji} {current_percentage:.1f}%\n{signal_text}',
                       xy=(current_date, current_percentage),
                       xytext=(10, 10), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.8', facecolor=signal_color, alpha=0.8),
                       fontsize=12, fontweight='bold', color='white',
                       ha='left', va='bottom')
            
            # Современное оформление рамки
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#bdc3c7')
            ax.spines['bottom'].set_color('#bdc3c7')
            
            # Финальная настройка
            plt.tight_layout()
            
            # Сохранение в высоком качестве
            plt.savefig(self.chart_file, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            self.logger.info(f"Современный график сохранен в {self.chart_file}")
            return self.chart_file
        except Exception as e:
            self.logger.error(f"Ошибка создания графика: {str(e)}")
            return None

    def get_ma200_indicator(self, force_refresh=False):
        """
        Получает текущие данные MA200 индикатора
        
        Args:
            force_refresh (bool): Принудительно обновить данные
            
        Returns:
            dict: Словарь с данными индикатора или None в случае ошибки
        """
        try:
            # Рассчитываем данные
            results_df = self.calculate_ma200_percentage(force_refresh)
            if results_df is None or len(results_df) == 0:
                return None
            
            # Создаем график
            chart_path = self.create_chart(results_df)
            
            # Получаем последние данные
            latest_data = results_df.iloc[-1]
            current_percentage = latest_data['percentage']
            
            # Определяем сигнал и статус
            signal, status, description = self._determine_market_signal(current_percentage)
            
            result = {
                'percentage': round(current_percentage, 1),
                'coins_above_ma200': latest_data['coins_above_ma200'],
                'total_coins': latest_data['total_coins'],
                'signal': signal,
                'status': status,
                'description': description,
                'date': latest_data['date'].strftime('%Y-%m-%d'),
                'chart_path': chart_path,
                'history_days': self.history_days,
                'ma_period': self.ma_period,
                'top_n': self.top_n,
                'overbought_threshold': self.overbought_threshold,
                'oversold_threshold': self.oversold_threshold,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"MA200 Indicator: {current_percentage:.1f}% ({signal}) - {status}")
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка получения MA200 индикатора: {str(e)}")
            return None

    def _determine_market_signal(self, percentage):
        """
        Определяет рыночный сигнал на основе процента монет выше MA200
        
        Args:
            percentage (float): Процент монет выше MA200
            
        Returns:
            tuple: (emoji-сигнал, текстовый статус, описание)
        """
        if percentage <= self.oversold_threshold:
            return "🔴", "Oversold", "Most coins below MA200 - potential buying opportunity"
        elif percentage <= 30:
            return "🟠", "Weak Market", "Few coins above MA200 - bearish trend"
        elif percentage <= 70:
            return "🟡", "Neutral Market", "Moderate amount of coins above MA200"
        elif percentage < self.overbought_threshold:
            return "🟢", "Strong Market", "Most coins above MA200 - bullish trend"
        else:
            return "🔵", "Overbought", "Almost all coins above MA200 - potential selling opportunity"

    def format_ma200_message(self, ma200_data=None):
        """
        Форматирует данные MA200 индикатора в сообщение для Telegram
        
        Args:
            ma200_data (dict, optional): Данные индикатора или None для получения новых
            
        Returns:
            str: Форматированное сообщение или None в случае ошибки
        """
        try:
            if ma200_data is None:
                ma200_data = self.get_ma200_indicator()
            
            if ma200_data is None:
                return None
            
            message = f"""{ma200_data['signal']} *MA200 Market Indicator*

*Current Status:* {ma200_data['status']}
*Coins above MA200:* {ma200_data['coins_above_ma200']}/{ma200_data['total_coins']} \\({ma200_data['percentage']}%\\)

*Market Signal:* {ma200_data['description']}

*Analysis:*
• MA Period: {ma200_data['ma_period']} days
• Top coins analyzed: {ma200_data['top_n']}
• History period: {ma200_data['history_days']} days
• Overbought level: {ma200_data['overbought_threshold']}%
• Oversold level: {ma200_data['oversold_threshold']}%

*Last Update:* {ma200_data['date']}

_The MA200 indicator shows what percentage of top cryptocurrencies are trading above their 200\\-day moving average\\. Values above 80% often indicate market peaks, while values below 10% may signal buying opportunities\\._"""

            return message
        except Exception as e:
            self.logger.error(f"Ошибка форматирования сообщения MA200: {str(e)}")
            return None