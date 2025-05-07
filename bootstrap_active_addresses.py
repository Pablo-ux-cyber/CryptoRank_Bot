import os
import json
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bootstrap_script')

# Импортируем класс ActiveAddressesTracker
from active_addresses import ActiveAddressesTracker

def main():
    """
    Функция для загрузки исторических данных об активных адресах
    """
    logger.info("Запуск загрузки исторических данных об активных адресах")
    
    # Создаем экземпляр трекера активных адресов
    tracker = ActiveAddressesTracker()
    
    # Загружаем историю для Bitcoin
    logger.info("Загрузка исторических данных для Bitcoin...")
    btc_result = tracker.bootstrap_history("bitcoin")
    logger.info(f"Результат загрузки для Bitcoin: {'успешно' if btc_result else 'ошибка'}")
    
    # Загружаем историю для Ethereum
    logger.info("Загрузка исторических данных для Ethereum...")
    eth_result = tracker.bootstrap_history("ethereum")
    logger.info(f"Результат загрузки для Ethereum: {'успешно' if eth_result else 'ошибка'}")
    
    # Проверяем, есть ли данные в JSON-файлах
    btc_history = tracker.read_history("bitcoin")
    eth_history = tracker.read_history("ethereum")
    
    logger.info(f"Количество исторических записей для Bitcoin: {len(btc_history)}")
    logger.info(f"Количество исторических записей для Ethereum: {len(eth_history)}")

if __name__ == "__main__":
    main()