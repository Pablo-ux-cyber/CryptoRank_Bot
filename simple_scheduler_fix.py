#!/usr/bin/env python3
"""
Простой запуск планировщика без Flask
Этот файл запускает только планировщик для systemd сервиса
"""

import sys
import signal
import time

# Загружаем переменные окружения
from load_dotenv import load_dotenv
load_dotenv()

from logger import logger
from scheduler import SensorTowerScheduler

scheduler = None

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info("Получен сигнал остановки планировщика")
    if scheduler:
        scheduler.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Настройка обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Запуск планировщика через systemd")
    
    # Создаем и запускаем планировщик
    scheduler = SensorTowerScheduler()
    success = scheduler.start()
    
    if not success:
        logger.error("Не удалось запустить планировщик")
        sys.exit(1)
    
    logger.info("Планировщик запущен успешно")
    
    # Ждем сигналов
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    logger.info("Планировщик завершен")