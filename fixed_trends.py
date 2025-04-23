#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль с исправленной реализацией Google Trends API для преодоления проблемы с method_whitelist
"""

import logging
import json
import requests
import pandas as pd
from datetime import datetime

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('fixed_trends')

class FixedTrendReq:
    """
    Исправленная версия TrendReq, которая не использует параметр method_whitelist
    Базируется на том же API, но с исправлениями для совместимости с новыми версиями requests
    """
    
    def __init__(self, hl='en-US', tz=360, timeout=(10, 25), geo='', gprop=''):
        """
        Инициализация клиента API Google Trends
        
        Args:
            hl (str): Локаль для запросов (en-US, ru-RU и т.д.)
            tz (int): Часовой пояс
            timeout (tuple): Тайм-аут для запросов (соединение, чтение)
            geo (str): Геолокация для запросов
            gprop (str): Категория Google (пусто для веб-поиска)
        """
        self.hl = hl
        self.tz = tz
        self.geo = geo
        self.gprop = gprop
        self.cookies = None
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'referer': 'https://trends.google.com/',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
        }
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._get_cookies()
        self.token_payload = {}
        self.interest_over_time_payload = {}
        
    def _get_cookies(self):
        """Получает куки для аутентификации запросов"""
        try:
            response = self.session.get(
                'https://trends.google.com/?geo=' + self.geo, 
                timeout=self.timeout
            )
            self.cookies = response.cookies
            self.session.cookies.update(self.cookies)
            return True
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении куки: {str(e)}")
            return False
            
    def build_payload(self, kw_list, cat=0, timeframe='today 12-m', geo='', gprop=''):
        """
        Создает полезную нагрузку для запросов к Trends API
        
        Args:
            kw_list (list): Список ключевых слов для запроса
            cat (int): Категория
            timeframe (str): Временной интервал
            geo (str): Геолокация
            gprop (str): Категория Google
        """
        self.geo = geo or self.geo
        self.token_payload = {
            'hl': self.hl,
            'tz': self.tz,
            'req': {'comparisonItem': [], 'category': cat, 'property': gprop}
        }
        
        for kw in kw_list:
            self.token_payload['req']['comparisonItem'].append({
                'keyword': kw, 'time': timeframe, 'geo': self.geo
            })
        
        self.token_payload['req'] = json.dumps(self.token_payload['req'])
        
        # Устанавливаем полезную нагрузку для interest_over_time
        self.interest_over_time_payload = dict(self.token_payload)
        
    def interest_over_time(self):
        """
        Запрашивает данные о популярности запросов за определенный период
        
        Returns:
            pd.DataFrame: DataFrame с данными о популярности запросов
        """
        url = 'https://trends.google.com/trends/api/widgetdata/multiline'
        token = self._get_token()
        if token is None:
            return pd.DataFrame()
            
        # Формируем запрос
        req = dict(
            self.interest_over_time_payload,
            token=token,
            tz=self.tz
        )
        
        try:
            # Делаем запрос
            response = self.session.get(
                url,
                params=req,
                timeout=self.timeout
            )
            
            # Проверяем статус
            if response.status_code != 200:
                logger.error(f"Ошибка запроса: {response.status_code}")
                return pd.DataFrame()
                
            # Обрабатываем ответ
            # API возвращает префикс ")]}'," который нужно удалить
            content = response.text[5:]
            
            # Парсим JSON
            data = json.loads(content)
            if 'default' not in data or 'timelineData' not in data['default']:
                logger.error("Некорректный формат данных в ответе")
                return pd.DataFrame()
                
            result = {}
            time_data = []
            
            # Извлекаем данные
            for point in data['default']['timelineData']:
                timestamp = int(point['time'])
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                time_data.append(time_str)
                
                for i, value in enumerate(point['value']):
                    # Получаем имя ключевого слова из запроса
                    keyword = json.loads(
                        self.interest_over_time_payload['req']
                    )['comparisonItem'][i]['keyword']
                    
                    if keyword not in result:
                        result[keyword] = []
                    result[keyword].append(int(value))
            
            # Создаем DataFrame
            df = pd.DataFrame(result, index=time_data)
            return df
        
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе данных: {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Непредвиденная ошибка: {str(e)}")
            return pd.DataFrame()
            
    def _get_token(self):
        """Получает токен для запросов API"""
        url = 'https://trends.google.com/trends/api/explore'
        try:
            response = self.session.get(
                url,
                params=self.token_payload,
                timeout=self.timeout
            )
            if response.status_code != 200:
                logger.error(f"Ошибка при получении токена: {response.status_code}")
                return None
            
            # Обрабатываем ответ
            content = response.text[5:]  # Удаляем префикс ")]}',"
            data = json.loads(content)
            
            # Извлекаем токен для widget запросов
            widgets = data['widgets']
            for widget in widgets:
                if widget['id'] == 'TIMESERIES':
                    return widget['token']
            
            logger.error("Токен для TIMESERIES не найден")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении токена: {str(e)}")
            return None

# Экспортируем альтернативную реализацию, которая не использует метод method_whitelist
class TrendReq(FixedTrendReq):
    pass