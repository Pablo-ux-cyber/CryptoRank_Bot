import os
import json
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('migration_script')

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
    if not os.path.exists(bitcoin_json) or not os.path.exists(ethereum_json):
        logger.error("Файлы истории не найдены. Сначала запустите bootstrap_active_addresses.py")
        return False
    
    # Загружаем данные из файлов
    try:
        with open(bitcoin_json, 'r') as f:
            bitcoin_data = json.load(f)
        
        with open(ethereum_json, 'r') as f:
            ethereum_data = json.load(f)
        
        logger.info(f"Загружены данные: {len(bitcoin_data)} записей для Bitcoin, {len(ethereum_data)} записей для Ethereum")
        
        # Загружаем существующую историю
        try:
            with open(main_history_file, 'r') as f:
                main_history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            main_history = []
        
        # Преобразуем данные в формат основного файла истории
        new_entries = []
        
        # Обрабатываем данные Bitcoin
        for entry in bitcoin_data:
            # Вычисляем delta_pct на основе соседних записей
            if len(bitcoin_data) > 1:
                # Получаем индекс текущей записи
                idx = bitcoin_data.index(entry)
                # Если не первая запись, вычисляем изменение относительно предыдущей
                if idx > 0:
                    prev_value = bitcoin_data[idx-1]['value']
                    if prev_value > 0:  # Избегаем деления на ноль
                        delta_pct = (entry['value'] - prev_value) / prev_value * 100
                    else:
                        delta_pct = 0.0
                else:
                    delta_pct = 0.0
            else:
                delta_pct = 0.0
            
            # Определяем статус на основе delta_pct
            if delta_pct < -10:
                status = "Very Low Demand"
                emoji = "📉"
            elif delta_pct < -2:
                status = "Weakened Demand"
                emoji = "🔻"
            elif delta_pct <= 2:
                status = "Normal Level"
                emoji = "⚖️"
            elif delta_pct <= 10:
                status = "Increased Demand"
                emoji = "🔺"
            else:
                status = "Very High Demand"
                emoji = "📈"
            
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
            
            new_entries.append(history_entry)
        
        # Обрабатываем данные Ethereum
        for entry in ethereum_data:
            # Вычисляем delta_pct на основе соседних записей
            if len(ethereum_data) > 1:
                # Получаем индекс текущей записи
                idx = ethereum_data.index(entry)
                # Если не первая запись, вычисляем изменение относительно предыдущей
                if idx > 0:
                    prev_value = ethereum_data[idx-1]['value']
                    if prev_value > 0:  # Избегаем деления на ноль
                        delta_pct = (entry['value'] - prev_value) / prev_value * 100
                    else:
                        delta_pct = 0.0
                else:
                    delta_pct = 0.0
            else:
                delta_pct = 0.0
            
            # Определяем статус на основе delta_pct
            if delta_pct < -10:
                status = "Very Low Demand"
                emoji = "📉"
            elif delta_pct < -2:
                status = "Weakened Demand"
                emoji = "🔻"
            elif delta_pct <= 2:
                status = "Normal Level"
                emoji = "⚖️"
            elif delta_pct <= 10:
                status = "Increased Demand"
                emoji = "🔺"
            else:
                status = "Very High Demand"
                emoji = "📈"
            
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
            
            new_entries.append(history_entry)
        
        # Добавляем новые записи к существующей истории
        main_history.extend(new_entries)
        
        # Сортируем записи по времени (новые сначала)
        main_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Сохраняем обновленную историю
        with open(main_history_file, 'w') as f:
            json.dump(main_history, f, indent=2)
        
        logger.info(f"Успешно добавлено {len(new_entries)} записей в основной файл истории")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при миграции данных: {str(e)}")
        return False

if __name__ == "__main__":
    main()