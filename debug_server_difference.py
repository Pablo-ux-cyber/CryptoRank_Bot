#!/usr/bin/env python3
"""
Диагностика различий между Replit (40.8%) и сервером (45%)
"""

import logging
import os
from datetime import datetime
from market_breadth_indicator import MarketBreadthIndicator
from crypto_analyzer_cryptocompare import CryptoAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_environment_differences():
    """Проверяет возможные причины различий между средами"""
    
    logger.info("ДИАГНОСТИКА РАЗЛИЧИЙ МЕЖДУ REPLIT И СЕРВЕРОМ")
    logger.info("="*60)
    
    # 1. Проверка API ключа
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')
    logger.info(f"API ключ: {api_key[:10]}..." if len(api_key) > 10 else f"API ключ: {api_key}")
    
    # 2. Проверка временной зоны
    logger.info(f"Текущее время: {datetime.now()}")
    logger.info(f"UTC время: {datetime.utcnow()}")
    
    # 3. Получение списка монет
    analyzer = CryptoAnalyzer(cache=None)
    top_coins = analyzer.get_top_coins(50)
    
    if top_coins:
        logger.info(f"Получено {len(top_coins)} топ монет")
        logger.info("Первые 10 монет:")
        for i, coin in enumerate(top_coins[:10]):
            logger.info(f"  {i+1}. {coin['symbol']} - {coin['name']}")
    else:
        logger.error("Не удалось получить список монет")
        return
    
    # 4. Тест одной монеты для сравнения данных
    logger.info("\nТест загрузки данных BTC:")
    btc_data = analyzer.get_coin_history('BTC', 300)
    
    if btc_data is not None and not btc_data.empty:
        logger.info(f"BTC данные: {len(btc_data)} записей")
        logger.info(f"Первая дата: {btc_data['date'].min()}")
        logger.info(f"Последняя дата: {btc_data['date'].max()}")
        logger.info(f"Последняя цена: ${btc_data['price'].iloc[-1]:,.2f}")
    else:
        logger.error("Не удалось загрузить данные BTC")
    
    # 5. Полный тест с подробным логированием
    logger.info("\nПолный тест Market Breadth:")
    indicator = MarketBreadthIndicator()
    data = indicator.get_market_breadth_data(fast_mode=False)
    
    if data:
        logger.info(f"РЕЗУЛЬТАТ: {data['current_value']:.1f}%")
        logger.info(f"Статус: {data['condition']}")
        logger.info(f"Монет: {data['total_coins']}")
        logger.info(f"Сигнал: {data['signal']}")
        
        # Показываем среднее, мин, макс для диагностики
        logger.info(f"Среднее: {data.get('average_value', 'N/A')}")
        logger.info(f"Минимум: {data.get('min_value', 'N/A')}")
        logger.info(f"Максимум: {data.get('max_value', 'N/A')}")
    else:
        logger.error("Не удалось получить данные Market Breadth")

if __name__ == "__main__":
    debug_environment_differences()