#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Отладочный скрипт для тестирования прямого доступа к Google Trends API
Проверяет настройку локали и временных периодов согласно новым требованиям
"""

import pandas as pd
import time
from pytrends.request import TrendReq
import logging
import json
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('google_trends_debug')

def make_api_request(locale='en-US', timeframe='now 14-d', keywords=['bitcoin']):
    """
    Делает тестовый запрос к Google Trends API с заданными параметрами
    """
    logger.info(f"Тестовый запрос к Google Trends API:")
    logger.info(f"  Локаль: {locale}")
    logger.info(f"  Временной период: {timeframe}")
    logger.info(f"  Ключевые слова: {keywords}")
    
    try:
        # Создаем клиент с заданной локалью
        pytrends = TrendReq(hl=locale, tz=0)
        logger.info("TrendReq клиент создан успешно")
        
        # Делаем запрос
        pytrends.build_payload(keywords, cat=0, timeframe=timeframe)
        logger.info("Запрос сформирован")
        
        # Получаем данные об интересе
        data_frame = pytrends.interest_over_time()
        logger.info(f"Получен ответ с {len(data_frame)} записями")
        
        # Выводим данные
        if not data_frame.empty:
            logger.info("Получены данные:")
            for date, row in data_frame.iterrows():
                logger.info(f"  {date}: {row.to_dict()}")
                
            # Средние значения
            averages = {kw: data_frame[kw].mean() for kw in keywords}
            logger.info(f"Средние значения: {averages}")
            return data_frame, averages
        else:
            logger.warning("Получен пустой ответ")
            return None, None
            
    except Exception as e:
        logger.error(f"Ошибка при запросе: {str(e)}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        return None, None

def main():
    """Основная функция тестирования"""
    logger.info("=" * 80)
    logger.info("Начало тестирования Google Trends API")
    logger.info(f"Дата и время: {datetime.now()}")
    
    # Тест 1: Запрос с новыми параметрами (en-US, 14 дней)
    logger.info("\nТест 1: Запрос с новыми параметрами (en-US, 14 дней)")
    df1, avg1 = make_api_request(locale='en-US', timeframe='now 14-d', keywords=['bitcoin'])
    
    # Пауза между запросами
    time.sleep(5)  
    
    # Тест 2: Запрос для 'crypto crash'
    logger.info("\nТест 2: Запрос для 'crypto crash'")
    df2, avg2 = make_api_request(locale='en-US', timeframe='now 14-d', keywords=['crypto crash'])
    
    # Пауза между запросами
    time.sleep(5)
    
    # Тест 3: Альтернативные временные периоды, если первые запросы не сработали
    if df1 is None:
        logger.info("\nТест 3: Альтернативный период (7 дней)")
        df3, avg3 = make_api_request(locale='en-US', timeframe='now 7-d', keywords=['bitcoin'])
    
    logger.info("=" * 80)
    logger.info("Тестирование завершено")
    
if __name__ == "__main__":
    main()