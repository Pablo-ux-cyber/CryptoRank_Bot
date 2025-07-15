#!/usr/bin/env python3
"""
Standalone scheduler for running as systemd service
Это отдельный файл планировщика который запускается через systemd
main.py остается только для Flask веб-интерфейса
"""

import sys
import signal
import time
from datetime import datetime

# Загружаем переменные окружения из .env файла
from load_dotenv import load_dotenv
load_dotenv()

from logger import logger
from scheduler import SensorTowerScheduler

def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C) and SIGTERM signals to gracefully shut down"""
    logger.info("Получен сигнал остановки. Завершение работы планировщика...")
    if hasattr(signal_handler, 'scheduler') and signal_handler.scheduler:
        signal_handler.scheduler.stop()
    sys.exit(0)

def main():
    """Main function to run the standalone scheduler"""
    
    # Настройка обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=== ЗАПУСК STANDALONE ПЛАНИРОВЩИКА ===")
    logger.info("Это отдельный планировщик для systemd сервиса")
    
    try:
        # Создаем и запускаем планировщик
        scheduler = SensorTowerScheduler()
        signal_handler.scheduler = scheduler  # Сохраняем для signal_handler
        
        success = scheduler.start()
        if not success:
            logger.error("Не удалось запустить планировщик")
            sys.exit(1)
        
        logger.info("Планировщик успешно запущен")
        logger.info("Для остановки используйте Ctrl+C или sudo systemctl stop coinbasebot")
        
        # Основной цикл - просто ждем сигналов
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Получен KeyboardInterrupt")
            
    except Exception as e:
        logger.error(f"Критическая ошибка в standalone планировщике: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("Standalone планировщик завершен")

if __name__ == "__main__":
    main()