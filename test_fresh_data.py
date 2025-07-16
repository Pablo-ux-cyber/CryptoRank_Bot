#!/usr/bin/env python3
"""
Тест для проверки что данные 200MA всегда свежие без кеширования
"""

import logging
from market_breadth_indicator import MarketBreadthIndicator
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fresh_data_loading():
    """
    Тестирует что данные всегда загружаются свежие, без кеширования
    """
    logger.info("🧪 ТЕСТ: Проверка свежести данных 200MA")
    logger.info("="*50)
    
    # Создаем индикатор
    indicator = MarketBreadthIndicator()
    
    # Первая загрузка
    logger.info("📡 Первая загрузка данных...")
    data1 = indicator.get_market_breadth_data(fast_mode=True)  # 10 монет для быстроты
    
    if data1:
        logger.info(f"✅ Первая загрузка: {data1['current_value']:.1f}% - {data1['condition']}")
        logger.info(f"🕐 Время первой загрузки: {datetime.now().strftime('%H:%M:%S')}")
    else:
        logger.error("❌ Первая загрузка не удалась")
        return False
    
    # Вторая загрузка (должна быть ТОЧНО такой же, если данные свежие)
    logger.info("\n📡 Вторая загрузка данных...")
    data2 = indicator.get_market_breadth_data(fast_mode=True)  # 10 монет
    
    if data2:
        logger.info(f"✅ Вторая загрузка: {data2['current_value']:.1f}% - {data2['condition']}")
        logger.info(f"🕐 Время второй загрузки: {datetime.now().strftime('%H:%M:%S')}")
    else:
        logger.error("❌ Вторая загрузка не удалась")
        return False
    
    # Сравнение результатов
    logger.info("\n🔍 АНАЛИЗ РЕЗУЛЬТАТОВ:")
    logger.info("="*30)
    
    if abs(data1['current_value'] - data2['current_value']) < 0.1:
        logger.info("✅ УСПЕХ: Результаты идентичны - данные свежие")
        logger.info(f"   Расхождение: {abs(data1['current_value'] - data2['current_value']):.3f}%")
        return True
    else:
        logger.error("❌ ПРОБЛЕМА: Результаты отличаются - возможно кеширование")
        logger.error(f"   Первая загрузка: {data1['current_value']:.1f}%")
        logger.error(f"   Вторая загрузка: {data2['current_value']:.1f}%")
        logger.error(f"   Расхождение: {abs(data1['current_value'] - data2['current_value']):.3f}%")
        return False

if __name__ == "__main__":
    success = test_fresh_data_loading()
    if success:
        print("\n🎉 ТЕСТ ПРОЙДЕН: Данные загружаются свежими без кеширования")
    else:
        print("\n❌ ТЕСТ НЕ ПРОЙДЕН: Обнаружены проблемы с кешированием")