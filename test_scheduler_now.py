#!/usr/bin/env python3
"""
Быстрый тест планировщика с отправкой сообщения прямо сейчас
"""

import sys
import time
from datetime import datetime

# Загружаем переменные окружения
from load_dotenv import load_dotenv
load_dotenv()

from logger import logger
from scheduler import SensorTowerScheduler

def test_scheduler_immediate():
    """Тестируем планировщик с немедленным запуском"""
    
    logger.info("=== НЕМЕДЛЕННЫЙ ТЕСТ ПЛАНИРОВЩИКА ===")
    
    try:
        # Создаем планировщик
        scheduler = SensorTowerScheduler()
        
        # Принудительно устанавливаем время на сейчас для немедленного запуска
        now = datetime.now()
        scheduler.last_rank_update_date = None  # Сбрасываем дату последнего обновления
        
        logger.info(f"Принудительный запуск сбора данных в {now}")
        
        # Вызываем метод сбора данных напрямую
        scheduler.run_scraping_job()
        
        logger.info("Тест завершен успешно!")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка в тесте планировщика: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_scheduler_immediate()
    sys.exit(0 if success else 1)