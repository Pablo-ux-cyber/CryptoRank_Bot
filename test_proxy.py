#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Проверка работы прокси для Google Trends,
использующего улучшенный метод с диапазоном дат
"""

import logging
from proxy_google_trends import ProxyGoogleTrends

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_proxy')

def main():
    # Создаем экземпляр прокси
    proxy = ProxyGoogleTrends()
    
    # Тестируем получение данных для Bitcoin
    logger.info("=" * 50)
    logger.info("ТЕСТИРОВАНИЕ ПРОКСИ GOOGLE TRENDS")
    logger.info("=" * 50)
    
    keywords = ["bitcoin", "ethereum", "cryptocurrency"]
    
    for keyword in keywords:
        try:
            logger.info(f"Запрос данных для '{keyword}'...")
            
            # Получаем данные
            interest, period, success = proxy.get_interest_data(keyword)
            
            # Выводим результаты
            if success:
                logger.info(f"УСПЕХ: Получен интерес {interest:.2f} для '{keyword}', период: {period}")
            else:
                logger.error(f"НЕУДАЧА: Не удалось получить данные для '{keyword}'")
        
        except Exception as e:
            logger.error(f"ОШИБКА при запросе '{keyword}': {str(e)}")
    
    logger.info("=" * 50)
    logger.info("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()