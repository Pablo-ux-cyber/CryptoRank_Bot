#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой тест разных периодов для Google Trends API
"""

import time
from pytrends.request import TrendReq
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

PERIODS = [
    'now 1-d',      # Последний день
    'now 7-d',      # Последние 7 дней
    'now 1-m',      # Последний месяц
    'today 1-m',    # Текущий месяц
    'today 3-m',    # Последние 3 месяца
    'today 12-m',   # Последние 12 месяцев
]

def test_period(period):
    """Тестирует один временной период"""
    logger.info(f"Тестирование периода: {period}")
    
    try:
        # Создаем клиент с английской локалью
        pytrends = TrendReq(hl='en-US', tz=0)
        logger.info("- TrendReq клиент создан")
        
        # Делаем запрос
        pytrends.build_payload(['bitcoin'], cat=0, timeframe=period)
        logger.info("- Запрос сформирован")
        
        # Получаем данные
        data = pytrends.interest_over_time()
        if not data.empty:
            logger.info(f"✓ УСПЕХ! Получено {len(data)} записей")
            logger.info(f"- Средний интерес: {data['bitcoin'].mean()}")
            return True
        else:
            logger.warning("✗ Пустой результат")
            return False
    except Exception as e:
        logger.error(f"✗ ОШИБКА: {str(e)}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info("=" * 50)
    logger.info("Тестирование различных периодов Google Trends")
    logger.info("=" * 50)
    
    results = {}
    
    for period in PERIODS:
        success = test_period(period)
        results[period] = success
        
        # Пауза между запросами, чтобы избежать 429
        time.sleep(5)
    
    # Суммируем результаты
    logger.info("\nРезультаты тестирования:")
    success_count = 0
    for period, success in results.items():
        status = "✓ РАБОТАЕТ" if success else "✗ НЕ РАБОТАЕТ"
        logger.info(f"- {period}: {status}")
        if success:
            success_count += 1
    
    logger.info(f"\nИтого: работает {success_count} из {len(PERIODS)} периодов")
    
    if success_count > 0:
        logger.info("\nРекомендации: Используйте один из рабочих периодов вместо 'now 14-d'")
    else:
        logger.info("\nВсе периоды не работают в Replit, но могут работать на вашем сервере")

if __name__ == "__main__":
    main()