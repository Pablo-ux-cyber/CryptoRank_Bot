#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест разных простых периодов для Google Trends API.
Проверяет один период за раз для лучшей точности.
"""

import sys
import logging
import time
from pytrends.request import TrendReq

# Настройка базового логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

def test_period(period='today 3-m'):
    """
    Тестирует конкретный период для Google Trends API
    """
    logger.info(f"Тестирование периода: {period}")
    logger.info("-" * 40)
    
    try:
        # Создание клиента с явным указанием локали
        logger.info("Создание TrendReq клиента (en-US)...")
        pytrends = TrendReq(hl='en-US', tz=0)
        
        # Формирование запроса
        logger.info(f"Формирование запроса для 'bitcoin' с периодом {period}...")
        pytrends.build_payload(['bitcoin'], cat=0, timeframe=period)
        
        # Получение данных
        logger.info("Запрос данных interest_over_time()...")
        data_frame = pytrends.interest_over_time()
        
        # Анализ результатов
        if data_frame is None or data_frame.empty:
            logger.warning("Получен пустой результат!")
            return False
        else:
            logger.info(f"УСПЕХ! Получено {len(data_frame)} записей")
            logger.info(f"Столбцы данных: {list(data_frame.columns)}")
            logger.info(f"Диапазон дат: с {data_frame.index.min()} по {data_frame.index.max()}")
            
            # Примеры значений
            logger.info("Примеры значений:")
            for i, (date, row) in enumerate(data_frame.iterrows()):
                if i < 3:  # Показываем только первые три записи
                    logger.info(f"  {date}: bitcoin={row['bitcoin']}")
                    
            # Статистика
            avg = data_frame['bitcoin'].mean()
            min_val = data_frame['bitcoin'].min()
            max_val = data_frame['bitcoin'].max()
            logger.info(f"Статистика: мин={min_val}, макс={max_val}, среднее={avg:.2f}")
            
            return True
    
    except Exception as e:
        logger.error(f"ОШИБКА: {str(e)}")
        import traceback
        logger.error(f"Трассировка:\n{traceback.format_exc()}")
        return False

def main():
    """
    Главная функция для тестирования разных периодов
    """
    # Список тестируемых периодов
    periods = [
        'today 3-m',    # Последние 3 месяца - наиболее вероятный рабочий вариант
        'today 1-m',    # Текущий месяц - тоже должен работать
        'today 12-m',   # Последние 12 месяцев - хороший запасной вариант
        'now 7-d',      # Последние 7 дней - может не работать
        'now 1-d'       # Последний день - может не работать
    ]
    
    logger.info("=" * 60)
    logger.info("ТЕСТИРОВАНИЕ ПЕРИОДОВ GOOGLE TRENDS")
    logger.info("=" * 60)
    
    # Проверка аргументов командной строки
    if len(sys.argv) > 1 and sys.argv[1] in periods:
        # Тестируем только один указанный период
        periods = [sys.argv[1]]
        logger.info(f"Тестирование только периода: {periods[0]}")
    else:
        logger.info(f"Тестирование {len(periods)} периодов")
    
    results = {}
    
    # Проверяем каждый период
    for period in periods:
        logger.info("\n" + "=" * 40)
        result = test_period(period)
        results[period] = result
        
        # Пауза между запросами, чтобы избежать ограничений API
        if period != periods[-1]:  # Кроме последнего периода
            delay = 10
            logger.info(f"Пауза {delay} секунд перед следующим запросом...")
            time.sleep(delay)
    
    # Вывод итоговых результатов
    logger.info("\n" + "=" * 60)
    logger.info("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    logger.info("-" * 60)
    
    success_count = 0
    for period, success in results.items():
        status = "✓ РАБОТАЕТ" if success else "✗ НЕ РАБОТАЕТ"
        logger.info(f"{period}: {status}")
        if success:
            success_count += 1
    
    logger.info("-" * 60)
    logger.info(f"ИТОГО: {success_count} из {len(periods)} периодов работают")
    
    # Рекомендации
    logger.info("\nРЕКОМЕНДАЦИИ:")
    if success_count > 0:
        working_periods = [p for p, s in results.items() if s]
        logger.info(f"- Рекомендуется использовать период: {working_periods[0]}")
        logger.info(f"- Все рабочие периоды: {', '.join(working_periods)}")
        logger.info("- Измените строку 461 в google_trends_pulse.py:")
        logger.info(f"  pytrends.build_payload(['bitcoin'], cat=0, timeframe='{working_periods[0]}')")
    else:
        logger.info("- В Replit все периоды не работают из-за ограничений Google")
        logger.info("- На вашем сервере, вероятно, будет работать 'today 3-m'")
        logger.info("- Попробуйте увеличить задержку между запросами (time.sleep) до 15-20 секунд")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())