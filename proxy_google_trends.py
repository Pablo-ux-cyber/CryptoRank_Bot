#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для обхода ограничений Google Trends API
Использует продвинутые техники для получения данных от Google Trends
"""

import os
import time
import random
import logging
import requests
from datetime import datetime, timedelta
from pytrends.request import TrendReq

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('google_trends_proxy')

class ProxyGoogleTrends:
    """
    Класс для обхода ограничений Google Trends API
    Использует различные техники для предотвращения блокировки:
    - Ротация временных периодов
    - Задержки между запросами
    - Пробует разные форматы запросов
    """
    
    def __init__(self):
        """
        Инициализация прокси для Google Trends
        """
        self.last_request_time = None
        self.min_delay = 3  # минимальная задержка между запросами в секундах
        self.session = requests.Session()
        self.retry_count = 0
        self.max_retries = 3
        
        # Периоды времени, которые могут работать
        # от более длинных к более коротким
        self.timeframes = [
            'today 12-m',  # 12 месяцев
            'today 3-m',   # 3 месяца
            'today 1-m',   # 1 месяц
            'now 7-d',     # 7 дней
            'now 1-d',     # 1 день
            'now 4-h'      # 4 часа
        ]
    
    def _add_delay(self):
        """
        Добавляет случайную задержку между запросами для предотвращения блокировки
        """
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_delay:
                delay = self.min_delay - elapsed + random.uniform(0.5, 2.0)
                logger.debug(f"Задержка перед запросом: {delay:.2f} секунд")
                time.sleep(delay)
        
        self.last_request_time = datetime.now()
    
    def get_interest_data(self, keyword, locale='en-US'):
        """
        Получает данные об интересе к ключевому слову, пробуя разные временные периоды
        
        Args:
            keyword (str): Ключевое слово для анализа
            locale (str): Локаль для анализа (например, 'en-US', 'ru-RU')
            
        Returns:
            tuple: (интерес, временной_период, статус_успеха)
        """
        self.retry_count = 0
        
        # Пробуем разные временные периоды
        for timeframe in self.timeframes:
            try:
                logger.info(f"Пробуем период: {timeframe}")
                interest, success = self._try_get_interest(keyword, timeframe, locale)
                
                if success:
                    logger.info(f"Успешно получены данные для периода {timeframe}")
                    return interest, timeframe, True
                
                # Увеличиваем задержку при каждой неудаче
                self.min_delay += 1
                
            except Exception as e:
                logger.warning(f"Ошибка при запросе для {timeframe}: {str(e)}")
                # Увеличиваем задержку при исключении
                self.min_delay += 2
        
        logger.error("Не удалось получить данные ни для одного периода")
        return 0, None, False
    
    def _try_get_interest(self, keyword, timeframe, locale):
        """
        Пытается получить данные о популярности запроса за определенный период
        
        Args:
            keyword (str): Ключевое слово для анализа
            timeframe (str): Временной период для анализа
            locale (str): Локаль для анализа
            
        Returns:
            tuple: (интерес, статус_успеха)
        """
        self._add_delay()
        
        try:
            # Создаем новый экземпляр для каждого запроса
            pytrends = TrendReq(hl=locale, tz=360, timeout=(10, 25), 
                              retries=2, backoff_factor=0.5)
            
            # Формируем запрос
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo='', gprop='')
            
            # Получаем данные
            data_frame = pytrends.interest_over_time()
            
            if data_frame.empty:
                logger.warning(f"Пустой ответ для {keyword} с периодом {timeframe}")
                return 0, False
            
            # Если есть данные, берем среднее или последний элемент
            if len(data_frame) > 0:
                if timeframe.startswith('now') and len(data_frame) > 1:
                    # Для краткосрочных периодов берем последнее значение
                    interest = float(data_frame[keyword].iloc[-1])
                else:
                    # Для долгосрочных периодов берем среднее значение
                    interest = float(data_frame[keyword].mean())
                
                logger.info(f"Интерес к {keyword}: {interest:.2f} за период {timeframe}")
                return interest, True
            
            return 0, False
            
        except Exception as e:
            self.retry_count += 1
            if self.retry_count <= self.max_retries:
                logger.warning(f"Попытка {self.retry_count} не удалась. Повторная попытка...")
                # Экспоненциальная задержка
                time.sleep(2 ** self.retry_count)
                return self._try_get_interest(keyword, timeframe, locale)
            else:
                logger.error(f"Превышено количество попыток для {timeframe}")
                raise e

# Пример использования
if __name__ == "__main__":
    proxy = ProxyGoogleTrends()
    interest, period, success = proxy.get_interest_data("bitcoin")
    print(f"Результат: интерес={interest}, период={period}, успех={success}")