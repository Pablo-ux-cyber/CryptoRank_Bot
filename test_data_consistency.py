#!/usr/bin/env python3
"""
Тест консистентности данных - проверка на повторяемость результатов
"""

import logging
from datetime import datetime
from market_breadth_indicator import MarketBreadthIndicator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_consistency():
    """Проверяет консистентность данных при повторных запросах"""
    
    logger.info("ТЕСТ КОНСИСТЕНТНОСТИ ДАННЫХ")
    logger.info("="*40)
    
    indicator = MarketBreadthIndicator()
    results = []
    
    # Выполняем 3 теста подряд
    for i in range(3):
        logger.info(f"\nТест {i+1}/3 в {datetime.now()}")
        
        data = indicator.get_market_breadth_data(fast_mode=False)
        
        if data:
            result = data['current_value']
            results.append(result)
            logger.info(f"Результат {i+1}: {result:.1f}%")
            logger.info(f"Монет: {data['total_coins']}")
        else:
            logger.error(f"Ошибка в тесте {i+1}")
            results.append(None)
    
    # Анализ результатов
    logger.info("\nАНАЛИЗ РЕЗУЛЬТАТОВ:")
    valid_results = [r for r in results if r is not None]
    
    if valid_results:
        logger.info(f"Результаты: {[f'{r:.1f}%' for r in valid_results]}")
        
        if len(set(f'{r:.1f}' for r in valid_results)) == 1:
            logger.info("✅ Данные КОНСИСТЕНТНЫ")
        else:
            logger.warning("❌ Данные НЕ консистентны - возможна проблема!")
            
        variance = max(valid_results) - min(valid_results)
        logger.info(f"Разброс: {variance:.1f}%")
        
        if variance > 5:
            logger.error("КРИТИЧНО: Слишком большой разброс данных!")
    else:
        logger.error("Все тесты завершились ошибкой")

if __name__ == "__main__":
    test_consistency()