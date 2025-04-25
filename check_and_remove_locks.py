#!/usr/bin/env python3
"""
Скрипт для проверки и удаления файлов блокировки
Может быть запущен вручную или через cron для обеспечения
бесперебойной работы бота
"""

import os
import time
import logging
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('lock_checker')

def check_and_remove_locks(data_dir='.', force=False):
    """
    Проверяет и удаляет устаревшие файлы блокировки
    
    Args:
        data_dir (str): Директория, где хранятся файлы блокировки
        force (bool): Принудительно удалить все файлы блокировки, независимо от их возраста
        
    Returns:
        tuple: (bool, str) - Успех операции и сообщение с результатом
    """
    results = []
    
    # Проверяем файл блокировки бота
    bot_lock_file = os.path.join(data_dir, "coinbasebot.lock")
    if os.path.exists(bot_lock_file):
        try:
            file_time = os.path.getmtime(bot_lock_file)
            current_time = time.time()
            age_minutes = (current_time - file_time) / 60
            
            if force or age_minutes > 30:
                os.remove(bot_lock_file)
                results.append(f"Удален файл блокировки бота (возраст: {age_minutes:.1f} минут)")
                logger.info(f"Удален файл блокировки бота (возраст: {age_minutes:.1f} минут)")
            else:
                results.append(f"Обнаружен файл блокировки бота (возраст: {age_minutes:.1f} минут) - работает активный экземпляр бота")
                logger.info(f"Обнаружен файл блокировки бота (возраст: {age_minutes:.1f} минут) - работает активный экземпляр бота")
        except Exception as e:
            results.append(f"Ошибка при проверке файла блокировки бота: {str(e)}")
            logger.error(f"Ошибка при проверке файла блокировки бота: {str(e)}")
    
    # Проверяем файл блокировки ручной операции
    manual_lock_file = os.path.join(data_dir, "manual_operation.lock")
    if os.path.exists(manual_lock_file):
        try:
            file_time = os.path.getmtime(manual_lock_file)
            current_time = time.time()
            age_minutes = (current_time - file_time) / 60
            
            if force or age_minutes > 10:  # Блокировки ручных операций действительны только 10 минут
                os.remove(manual_lock_file)
                results.append(f"Удален файл блокировки ручной операции (возраст: {age_minutes:.1f} минут)")
                logger.info(f"Удален файл блокировки ручной операции (возраст: {age_minutes:.1f} минут)")
            else:
                results.append(f"Обнаружен файл блокировки ручной операции (возраст: {age_minutes:.1f} минут)")
                logger.info(f"Обнаружен файл блокировки ручной операции (возраст: {age_minutes:.1f} минут)")
        except Exception as e:
            results.append(f"Ошибка при проверке файла блокировки ручной операции: {str(e)}")
            logger.error(f"Ошибка при проверке файла блокировки ручной операции: {str(e)}")
    
    if not results:
        results.append("Файлы блокировки не обнаружены. Система работает нормально.")
        logger.info("Файлы блокировки не обнаружены. Система работает нормально.")
    
    return True, "\n".join(results)

def main():
    """
    Основная функция для запуска из командной строки
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Проверка и удаление файлов блокировки')
    parser.add_argument('--force', action='store_true', help='Принудительно удалить все файлы блокировки')
    parser.add_argument('--dir', default='.', help='Директория с файлами блокировки')
    
    args = parser.parse_args()
    
    success, message = check_and_remove_locks(data_dir=args.dir, force=args.force)
    
    print(message)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())