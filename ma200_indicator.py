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
        
        self.base_url = "https://api.coingecko.com/api/v3"
        self.request_delay = 1.3  # Ограничение CoinGecko API
        
        self.logger.info(f"Initialized MA200 Indicator with top {self.top_n} coins, {self.ma_period}d MA, {self.history_days}d history")
        self.logger.info(f"Thresholds: Overbought={self.overbought_threshold}%, Oversold={self.oversold_threshold}%")

    def get_top_coins(self):
        """
        Получает список топ-N монет по капитализации
        
        Returns:
            list: Список словарей с данными монет или None в случае ошибки
        """
        try:
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': self.top_n,
                'page': 1,
                'sparkline': False
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            coins = response.json()
            self.logger.info(f"Получен список {len(coins)} монет из топ-{self.top_n}")
            
            return coins
        except Exception as e:
            self.logger.error(f"Ошибка получения списка топ монет: {str(e)}")
            return None

    def get_historical_data(self, coin_id, days):
        """
        Получает исторические данные цен для монеты
        
        Args:
            coin_id (str): ID монеты в CoinGecko
            days (int): Количество дней истории
            
        Returns:
            pd.DataFrame: DataFrame с историческими данными или None
        """
        try:
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Преобразуем данные в DataFrame
            prices = data['prices']
            df = pd.DataFrame(prices)
            df.columns = ['timestamp', 'price']
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df[['date', 'price']]
            df = df.set_index('date')
            
            return df
        except Exception as e:
            self.logger.error(f"Ошибка получения исторических данных для {coin_id}: {str(e)}")
            return None

    def load_cache(self):
        """
        Загружает кешированные данные
        
        Returns:
            dict: Кешированные данные или пустой словарь
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                self.logger.info(f"Загружен кеш с данными {len(cache)} монет")
                return cache
        except Exception as e:
            self.logger.error(f"Ошибка загрузки кеша: {str(e)}")
        
        return {}

    def save_cache(self, cache):
        """
        Сохраняет кешированные данные
        
        Args:
            cache (dict): Данные для кеширования
        """
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            self.logger.info(f"Кеш сохранен с данными {len(cache)} монет")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения кеша: {str(e)}")

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
        
        # Получаем список топ монет
        coins = self.get_top_coins()
        if not coins:
            return None
        
        # Определяем количество дней для загрузки (MA период + история + запас)
        total_days = self.ma_period + self.history_days + 50
        
        coin_data = {}
        valid_coins = []
        
        # Загружаем исторические данные для каждой монеты
        for coin in tqdm(coins, desc="Загрузка исторических данных"):
            coin_id = coin['id']
            
            # Проверяем кеш
            cache_key = f"{coin_id}_{total_days}"
            if cache_key in cache and not force_refresh:
                # Проверяем актуальность кеша (не старше 1 дня)
                cache_date = datetime.fromisoformat(cache[cache_key]['updated'])
                if (datetime.now() - cache_date).days < 1:
                    coin_data[coin_id] = pd.DataFrame(cache[cache_key]['data'])
                    coin_data[coin_id]['date'] = pd.to_datetime(coin_data[coin_id]['date'])
                    coin_data[coin_id] = coin_data[coin_id].set_index('date')
                    valid_coins.append(coin_id)
                    continue
            
            # Загружаем новые данные
            df = self.get_historical_data(coin_id, total_days)
            if df is not None and len(df) >= (self.ma_period + self.history_days):
                coin_data[coin_id] = df
                valid_coins.append(coin_id)
                
                # Сохраняем в кеш
                cache[cache_key] = {
                    'data': df.reset_index().to_dict('records'),
                    'updated': datetime.now().isoformat()
                }
            else:
                self.logger.warning(f"Недостаточно данных для {coin_id}, исключаем из анализа")
            
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
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Основная линия - процент монет выше MA200
            ax.plot(results_df['date'], results_df['percentage'], 
                   color='#00d4ff', linewidth=2, label='% монет выше MA200')
            
            # Горизонтальные линии порогов
            ax.axhline(y=self.overbought_threshold, color='#ff4757', 
                      linestyle='--', alpha=0.7, label=f'Перекупленность ({self.overbought_threshold}%)')
            ax.axhline(y=self.oversold_threshold, color='#2ed573', 
                      linestyle='--', alpha=0.7, label=f'Перепроданность ({self.oversold_threshold}%)')
            
            # Заливка областей
            ax.fill_between(results_df['date'], 0, self.oversold_threshold, 
                           alpha=0.2, color='#2ed573', label='Зона покупки')
            ax.fill_between(results_df['date'], self.overbought_threshold, 100, 
                           alpha=0.2, color='#ff4757', label='Зона продажи')
            
            # Настройка осей и заголовка
            ax.set_title(f'MA200 Indicator: % монет из топ-{self.top_n} выше MA{self.ma_period}', 
                        fontsize=16, fontweight='bold', color='white')
            ax.set_xlabel('Дата', fontsize=12, color='white')
            ax.set_ylabel('Процент монет выше MA200 (%)', fontsize=12, color='white')
            
            # Форматирование дат на оси X
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Сетка и легенда
            ax.grid(True, alpha=0.3, color='white')
            ax.legend(loc='upper left', framealpha=0.8)
            
            # Настройка цветов осей
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            
            # Установка лимитов по Y
            ax.set_ylim(0, 100)
            
            plt.tight_layout()
            plt.savefig(self.chart_file, dpi=300, bbox_inches='tight', 
                       facecolor='#1a1a1a', edgecolor='none')
            plt.close()
            
            self.logger.info(f"График сохранен в {self.chart_file}")
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