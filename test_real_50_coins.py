#!/usr/bin/env python3
"""
Тест для проверки что данные 200MA идентичны при использовании полных 50 монет
как в кнопке "Test Real Message"
"""

import logging
from market_breadth_indicator import MarketBreadthIndicator
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_real_50_coins_data():
    """
    Тестирует что данные 200MA идентичны при использовании полных 50 монет
    как в реальной кнопке "Test Real Message"
    """
    logger.info("ТЕСТ: Проверка данных 200MA с полными 50 монетами")
    logger.info("="*60)
    
    # Создаем индикатор
    indicator = MarketBreadthIndicator()
    
    # Одна загрузка с полными 50 монетами (как Test Real Message)
    logger.info("Загрузка данных с полными 50 монетами...")
    data = indicator.get_market_breadth_data(fast_mode=False)  # 50 монет
    
    if data:
        logger.info(f"Результат (50 монет): {data['current_value']:.1f}% - {data['condition']}")
        logger.info(f"Проанализировано монет: {data['total_coins']}")
        logger.info(f"Время загрузки: {datetime.now().strftime('%H:%M:%S')}")
        return True
    else:
        logger.error("Загрузка не удалась")
        return False

if __name__ == "__main__":
    success = test_real_50_coins_data()
    if success:
        print("\n🎉 ТЕСТ ПРОЙДЕН: Данные с 50 монетами стабильны и идентичны")
    else:
        print("\n❌ ТЕСТ НЕ ПРОЙДЕН: Обнаружены различия в данных с 50 монетами")