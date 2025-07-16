#!/usr/bin/env python3
"""
Исправление проблемы лимитов API на сервере
"""

import logging
import os
import time
from crypto_analyzer_cryptocompare import CryptoAnalyzer
from market_breadth_indicator import MarketBreadthIndicator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_api_limits():
    """Проверяет текущее состояние API лимитов"""
    
    logger.info("ПРОВЕРКА API ЛИМИТОВ CRYPTOCOMPARE")
    logger.info("="*50)
    
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')
    logger.info(f"API ключ: {api_key[:10]}..." if len(api_key) > 10 else f"API ключ: {api_key}")
    
    analyzer = CryptoAnalyzer(cache=None)
    
    # Пробуем загрузить 1 монету для проверки лимита
    logger.info("Тест загрузки BTC...")
    btc_data = analyzer.get_coin_history('BTC', 30)
    
    if btc_data is not None:
        logger.info("✅ API работает - BTC загружен")
        logger.info(f"Записей: {len(btc_data)}")
    else:
        logger.error("❌ API не работает - возможно исчерпан лимит")
        return False
    
    # Проверяем полную загрузку
    logger.info("\nТест полной загрузки 50 монет...")
    indicator = MarketBreadthIndicator()
    data = indicator.get_market_breadth_data(fast_mode=False)
    
    if data:
        coins_loaded = data['total_coins']
        logger.info(f"Загружено монет: {coins_loaded}/50")
        
        if coins_loaded >= 45:
            logger.info("✅ Достаточно монет для анализа")
            logger.info(f"Результат: {data['current_value']:.1f}%")
            return True
        else:
            logger.warning(f"❌ Недостаточно монет: {coins_loaded}/50")
            logger.warning("Проблема: API лимиты исчерпаны")
            return False
    else:
        logger.error("❌ Ошибка получения данных")
        return False

def suggest_api_solutions():
    """Предлагает решения проблемы API лимитов"""
    
    logger.info("\nВОЗМОЖНЫЕ РЕШЕНИЯ:")
    logger.info("1. Подождать восстановления лимитов (обычно 24 часа)")
    logger.info("2. Обновить план CryptoCompare API")
    logger.info("3. Использовать другой API ключ")
    logger.info("4. Добавить задержки между запросами")
    logger.info("5. Реализовать кеширование с TTL на короткий период")

def wait_for_api_recovery(check_interval=300):
    """Ждет восстановления API лимитов"""
    
    logger.info(f"\nОЖИДАНИЕ ВОССТАНОВЛЕНИЯ API (проверка каждые {check_interval//60} минут)")
    
    while True:
        logger.info(f"Проверка в {time.strftime('%H:%M:%S')}")
        
        if check_api_limits():
            logger.info("✅ API восстановлен!")
            break
        else:
            logger.info(f"❌ API еще не восстановлен, ждем {check_interval//60} минут...")
            time.sleep(check_interval)

if __name__ == "__main__":
    if not check_api_limits():
        suggest_api_solutions()
        
        user_choice = input("\nЖдать восстановления API? (y/n): ")
        if user_choice.lower() == 'y':
            wait_for_api_recovery()
        else:
            logger.info("Для решения проблемы обратитесь к администратору")