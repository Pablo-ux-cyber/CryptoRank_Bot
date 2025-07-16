#!/usr/bin/env python3
"""
Тест свежести данных - проверка что кеширование действительно отключено
"""

import logging
import time
from datetime import datetime
from crypto_analyzer_cryptocompare import CryptoAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fresh_data():
    """Проверяет что данные загружаются свежими без кеширования"""
    
    logger.info("ТЕСТ СВЕЖЕСТИ ДАННЫХ")
    logger.info("="*40)
    
    analyzer = CryptoAnalyzer(cache=None)
    
    # Тест 1: Загрузка BTC дважды подряд
    logger.info("Тест 1: Двойная загрузка BTC")
    
    start1 = time.time()
    btc_data1 = analyzer.get_coin_history('BTC', 30)
    time1 = time.time() - start1
    
    time.sleep(1)  # Небольшая пауза
    
    start2 = time.time()
    btc_data2 = analyzer.get_coin_history('BTC', 30)
    time2 = time.time() - start2
    
    if btc_data1 is not None and btc_data2 is not None:
        logger.info(f"Загрузка 1: {time1:.2f}с, записей: {len(btc_data1)}")
        logger.info(f"Загрузка 2: {time2:.2f}с, записей: {len(btc_data2)}")
        
        # Проверка что время загрузки примерно одинаковое (нет кеша)
        if abs(time1 - time2) < 0.5 and time2 > 0.5:  # Обе загрузки медленные
            logger.info("✅ Кеширование ОТКЛЮЧЕНО - обе загрузки медленные")
        elif time2 < 0.1:  # Вторая загрузка быстрая
            logger.warning("❌ Возможно есть КЕШИРОВАНИЕ - вторая загрузка быстрая")
        else:
            logger.info("✅ Данные загружаются свежими")
            
        # Проверка что данные идентичны (должны быть, если запросы близко по времени)
        if len(btc_data1) == len(btc_data2):
            price_diff = abs(btc_data1['price'].iloc[-1] - btc_data2['price'].iloc[-1])
            if price_diff < 100:  # Небольшая разница в цене допустима
                logger.info(f"✅ Данные консистентны (разница цены: ${price_diff:.2f})")
            else:
                logger.warning(f"❌ Большая разница в ценах: ${price_diff:.2f}")
    else:
        logger.error("Ошибка загрузки данных BTC")
    
    # Тест 2: Проверка отсутствия папки cache
    import os
    if os.path.exists('cache'):
        logger.warning("❌ Папка cache существует!")
        cache_files = os.listdir('cache')
        logger.info(f"Файлы в cache: {cache_files}")
    else:
        logger.info("✅ Папка cache отсутствует")

if __name__ == "__main__":
    test_fresh_data()