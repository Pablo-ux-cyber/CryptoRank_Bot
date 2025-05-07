import os
import json
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('migration_script')

def calculate_and_classify_delta(current_value, previous_value):
    """
    Рассчитывает и классифицирует процентное изменение
    
    Args:
        current_value (int): Текущее значение
        previous_value (int): Предыдущее значение
        
    Returns:
        tuple: (delta_pct, status, emoji)
    """
    if previous_value <= 0:
        return 0.0, "Normal Level", "⚖️"
    
    delta_pct = (current_value - previous_value) / previous_value * 100
    
    # Классификация изменения
    if delta_pct < -10:
        return delta_pct, "Very Low Demand", "📉"
    elif delta_pct < -2:
        return delta_pct, "Weakened Demand", "🔻"
    elif delta_pct <= 2:
        return delta_pct, "Normal Level", "⚖️"
    elif delta_pct <= 10:
        return delta_pct, "Increased Demand", "🔺"
    else:
        return delta_pct, "Very High Demand", "📈"

def process_data_to_history(data, reference_period=7):
    """
    Обрабатывает данные и преобразует их в формат для истории
    с вычислением изменений относительно опорного периода
    
    Args:
        data (list): Список записей с данными
        reference_period (int): Период для сравнения (дни)
        
    Returns:
        list: Преобразованные записи для истории
    """
    # Проверяем, что у нас есть данные
    if not data:
        return []
    
    # Сортируем данные по времени (старые сначала)
    data = sorted(data, key=lambda x: x.get('timestamp', 0))
    
    # Создаем список истории
    history_entries = []
    
    # Для каждой записи вычисляем изменение относительно средних значений
    for i, entry in enumerate(data):
        # Для самого первого элемента нет изменения
        if i == 0:
            delta_pct = 0.0
            status = "Normal Level"
            emoji = "⚖️"
        else:
            # Выбираем предыдущую запись для сравнения
            ref_idx = max(0, i - reference_period)
            ref_entry = data[ref_idx]
            
            # Вычисляем изменение
            delta_pct, status, emoji = calculate_and_classify_delta(
                entry['value'], ref_entry['value']
            )
        
        # Создаем запись в формате основного файла истории
        history_entry = {
            "chain": entry['chain'],
            "symbol": entry['symbol'],
            "value": entry['value'],
            "delta_pct": delta_pct,
            "status": status,
            "emoji": emoji,
            "timestamp": datetime.fromtimestamp(entry['timestamp']).isoformat()
        }
        
        history_entries.append(history_entry)
    
    return history_entries

def main():
    """
    Функция для миграции данных из отдельных файлов JSON в основной файл истории
    """
    logger.info("Запуск миграции данных об активных адресах")
    
    # Пути к файлам
    history_dir = "history"
    bitcoin_json = os.path.join(history_dir, "active_addresses_bitcoin.json")
    ethereum_json = os.path.join(history_dir, "active_addresses_ethereum.json")
    main_history_file = "active_addresses_history.json"
    
    # Проверяем существование файлов
    files_exists = True
    if not os.path.exists(bitcoin_json):
        logger.warning(f"Файл {bitcoin_json} не найден")
        files_exists = False
    
    if not os.path.exists(ethereum_json):
        logger.warning(f"Файл {ethereum_json} не найден")
        files_exists = False
    
    if not files_exists:
        logger.error("Файлы истории не найдены. Сначала запустите bootstrap_active_addresses.py")
        return False
    
    # Загружаем данные из файлов
    try:
        btc_data = []
        eth_data = []
        
        with open(bitcoin_json, 'r') as f:
            btc_data = json.load(f)
        
        with open(ethereum_json, 'r') as f:
            eth_data = json.load(f)
        
        logger.info(f"Загружены данные: {len(btc_data)} записей для Bitcoin, {len(eth_data)} записей для Ethereum")
        
        # Загружаем существующую историю
        try:
            with open(main_history_file, 'r') as f:
                main_history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            main_history = []
        
        # Очищаем существующую историю (опционально)
        main_history = []
        
        # Преобразуем данные в формат основного файла истории
        btc_history = process_data_to_history(btc_data)
        eth_history = process_data_to_history(eth_data)
        
        logger.info(f"Преобразовано записей: {len(btc_history)} для Bitcoin, {len(eth_history)} для Ethereum")
        
        # Добавляем новые записи к истории
        main_history.extend(btc_history)
        main_history.extend(eth_history)
        
        # Сортируем записи по времени (новые сначала)
        main_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Сохраняем обновленную историю
        with open(main_history_file, 'w') as f:
            json.dump(main_history, f, indent=2)
        
        logger.info(f"Успешно добавлено {len(btc_history) + len(eth_history)} записей в основной файл истории")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при миграции данных: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    main()