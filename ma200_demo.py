#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from logger import logger

class MA200Demo:
    """
    Демонстрационная версия MA200 индикатора с тестовыми данными
    """
    def __init__(self):
        self.logger = logger
        self.top_n = 50
        self.ma_period = 200
        self.history_days = 365
        self.overbought_threshold = 80
        self.oversold_threshold = 10
        self.chart_file = 'ma200_demo_chart.png'
        self.results_file = 'ma200_demo_data.csv'
        
        self.logger.info("Initialized MA200 Demo with test data")

    def generate_demo_data(self):
        """
        Генерирует демонстрационные данные для MA200 индикатора
        """
        np.random.seed(42)  # Для воспроизводимости
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=self.history_days)
        
        # Генерируем реалистичные данные с трендами
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Симулируем рыночные циклы
        base_trend = np.linspace(20, 70, len(dates))
        seasonal = 15 * np.sin(2 * np.pi * np.arange(len(dates)) / 90)  # 90-дневные циклы
        noise = np.random.normal(0, 8, len(dates))
        
        percentages = base_trend + seasonal + noise
        percentages = np.clip(percentages, 0, 100)  # Ограничиваем от 0 до 100%
        
        # Рассчитываем количество монет
        coins_above = (percentages * self.top_n / 100).astype(int)
        
        results = []
        for date, percentage, coins in zip(dates, percentages, coins_above):
            results.append({
                'date': date.strftime('%Y-%m-%d'),
                'percentage': round(percentage, 1),
                'coins_above_ma200': coins,
                'total_coins': self.top_n
            })
        
        return pd.DataFrame(results)

    def create_demo_chart(self, results_df):
        """
        Создает демонстрационный график MA200 индикатора
        """
        try:
            # Преобразуем даты для графика
            results_df['date_parsed'] = pd.to_datetime(results_df['date'])
            
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Основная линия - процент монет выше MA200
            ax.plot(results_df['date_parsed'], results_df['percentage'], 
                   color='#00d4ff', linewidth=2, label='% монет выше MA200')
            
            # Горизонтальные линии порогов
            ax.axhline(y=self.overbought_threshold, color='#ff4757', 
                      linestyle='--', alpha=0.7, label=f'Перекупленность ({self.overbought_threshold}%)')
            ax.axhline(y=self.oversold_threshold, color='#2ed573', 
                      linestyle='--', alpha=0.7, label=f'Перепроданность ({self.oversold_threshold}%)')
            
            # Заливка областей
            ax.fill_between(results_df['date_parsed'], 0, self.oversold_threshold, 
                           alpha=0.2, color='#2ed573', label='Зона покупки')
            ax.fill_between(results_df['date_parsed'], self.overbought_threshold, 100, 
                           alpha=0.2, color='#ff4757', label='Зона продажи')
            
            # Настройка осей и заголовка
            ax.set_title(f'MA200 Indicator: % монет из топ-{self.top_n} выше MA{self.ma_period} (DEMO)', 
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
            
            self.logger.info(f"Демо график сохранен в {self.chart_file}")
            return self.chart_file
        except Exception as e:
            self.logger.error(f"Ошибка создания демо графика: {str(e)}")
            return None

    def get_demo_ma200_indicator(self):
        """
        Получает демонстрационные данные MA200 индикатора
        """
        try:
            # Генерируем данные
            results_df = self.generate_demo_data()
            
            # Сохраняем в CSV
            results_df.to_csv(self.results_file, index=False)
            
            # Создаем график
            chart_path = self.create_demo_chart(results_df)
            
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
                'date': latest_data['date'],
                'chart_path': chart_path,
                'history_days': self.history_days,
                'ma_period': self.ma_period,
                'top_n': self.top_n,
                'overbought_threshold': self.overbought_threshold,
                'oversold_threshold': self.oversold_threshold,
                'timestamp': datetime.now().isoformat(),
                'demo_mode': True
            }
            
            self.logger.info(f"MA200 Demo: {current_percentage:.1f}% ({signal}) - {status}")
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка получения демо данных MA200: {str(e)}")
            return None

    def _determine_market_signal(self, percentage):
        """
        Определяет рыночный сигнал на основе процента монет выше MA200
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
        Форматирует демо данные MA200 в сообщение для Telegram
        """
        try:
            if ma200_data is None:
                ma200_data = self.get_demo_ma200_indicator()
            
            if ma200_data is None:
                return None
            
            message = f"""{ma200_data['signal']} *MA200 Market Indicator \\(DEMO\\)*

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

⚠️ *DEMO MODE \\- Using simulated data for demonstration*

_The MA200 indicator shows what percentage of top cryptocurrencies are trading above their 200\\-day moving average\\. Values above 80% often indicate market peaks, while values below 10% may signal buying opportunities\\._"""

            return message
        except Exception as e:
            self.logger.error(f"Ошибка форматирования демо сообщения MA200: {str(e)}")
            return None