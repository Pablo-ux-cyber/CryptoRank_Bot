#!/usr/bin/env python3
"""
Быстрый тест системы с полными 50 монетами
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from market_breadth_indicator import MarketBreadthIndicator
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_50_coins():
    """Тест Market Breadth с полными 50 монетами"""
    try:
        # Инициализация Market Breadth Indicator
        market_breadth = MarketBreadthIndicator()
        
        logger.info("Запуск теста с полными 50 монетами...")
        
        # Получение данных с полными 50 монетами (fast_mode=False)
        result = market_breadth.get_market_breadth_data(fast_mode=False)
        
        if result:
            logger.info(f"✅ УСПЕХ! Получены данные Market Breadth:")
            logger.info(f"   Сигнал: {result['signal']}")
            logger.info(f"   Состояние: {result['condition']}")
            logger.info(f"   Значение: {result['current_value']:.1f}%")
            logger.info(f"   Проанализировано монет: {result.get('coins_analyzed', 'неизвестно')}")
            
            # Форматирование сообщения
            message = market_breadth.format_breadth_message(result)
            logger.info(f"   Сообщение: {message}")
            
            return True
        else:
            logger.error("❌ ОШИБКА: Не удалось получить данные Market Breadth")
            return False
            
    except Exception as e:
        logger.error(f"❌ ИСКЛЮЧЕНИЕ: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== ТЕСТ СИСТЕМЫ С 50 МОНЕТАМИ ===")
    success = test_50_coins()
    
    if success:
        print("\n🎉 СИСТЕМА ГОТОВА К РАБОТЕ С 50 МОНЕТАМИ!")
    else:
        print("\n⚠️ СИСТЕМА НЕ ПРОШЛА ТЕСТ")
    
    sys.exit(0 if success else 1)