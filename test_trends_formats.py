#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестирование различных форматов запросов к Google Trends API
для определения работающих комбинаций
"""

import logging
import time
from pytrends.request import TrendReq
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trends_format_test')

def test_format(locale, timeframe, keyword):
    """Тестирует одну комбинацию параметров"""
    logger.info(f"Тестирование: locale={locale}, timeframe={timeframe}, keyword={keyword}")
    
    try:
        pytrends = TrendReq(hl=locale, tz=0)
        logger.info("- TrendReq клиент создан")
        
        pytrends.build_payload([keyword], cat=0, timeframe=timeframe)
        logger.info("- build_payload выполнен успешно")
        
        result = pytrends.interest_over_time()
        if not result.empty:
            logger.info(f"✓ УСПЕХ! Получено {len(result)} записей")
            logger.info(f"- Средний интерес: {result[keyword].mean()}")
            return True
        else:
            logger.warning("✗ Пустой результат")
            return False
    
    except Exception as e:
        logger.error(f"✗ Ошибка: {str(e)}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info("=" * 60)
    logger.info("Тестирование форматов запросов Google Trends")
    logger.info(f"Время запуска: {datetime.now()}")
    logger.info("=" * 60)
    
    # Список вариантов локалей
    locales = ['en-US', 'en-GB', 'ru-RU']
    
    # Список временных периодов
    timeframes = [
        'now 1-d',      # Последние 24 часа
        'now 7-d',      # Последние 7 дней
        'now 14-d',     # Последние 14 дней
        'today 1-m',    # Текущий месяц
        'today 3-m',    # Последние 3 месяца
        'today 12-m',   # Последние 12 месяцев
        'today 5-y'     # Последние 5 лет
    ]
    
    # Список ключевых слов
    keywords = ['bitcoin', 'cryptocurrency', 'crypto crash']
    
    # Счетчики
    total = 0
    success = 0
    failures = 0
    
    # Перебираем все комбинации
    for locale in locales:
        for timeframe in timeframes:
            for keyword in keywords:
                total += 1
                
                # Проверяем текущую комбинацию
                if test_format(locale, timeframe, keyword):
                    success += 1
                else:
                    failures += 1
                
                # Пауза между запросами, чтобы не получить ошибку 429
                time.sleep(3)
    
    # Вывод результатов
    logger.info("=" * 60)
    logger.info(f"Тестирование завершено. Успешно: {success}/{total}")
    logger.info(f"Процент успеха: {(success/total)*100:.1f}%")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()