import json
import os
from datetime import datetime
from logger import logger

def get_rank_from_json():
    """
    ИСПРАВЛЕНО: Принудительно читает самые последние данные рейтинга из JSON файла
    
    Returns:
        int или None: Рейтинг Coinbase за последнюю дату или None если данные недоступны
    """
    try:
        json_file_path = os.path.join(os.path.dirname(__file__), 'parsed_ranks.json')
        
        if not os.path.exists(json_file_path):
            logger.warning(f"ИСПРАВЛЕНИЕ: JSON файл не найден: {json_file_path}")
            return None
        
        # ИСПРАВЛЕНИЕ: Принудительное чтение без кеширования
        logger.info("ИСПРАВЛЕНИЕ: Принудительно читаем parsed_ranks.json для получения последних данных")
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        if not data or not isinstance(data, list):
            logger.warning("ИСПРАВЛЕНИЕ: JSON файл пустой или имеет неверный формат")
            return None
        
        # ИСПРАВЛЕНИЕ: Детальная проверка последних записей
        logger.info(f"ИСПРАВЛЕНИЕ: Загружено {len(data)} записей из JSON файла")
        
        # ИСПРАВЛЕНИЕ: Принудительная сортировка по дате (самые новые сначала)
        sorted_data = sorted(data, key=lambda x: x.get('date', ''), reverse=True)
        
        # ИСПРАВЛЕНИЕ: Показываем последние записи для отладки
        logger.info("ИСПРАВЛЕНИЕ: Последние записи в JSON:")
        for i, entry in enumerate(sorted_data[:3]):
            logger.info(f"  {i+1}. Дата: {entry.get('date', 'нет')}, Рейтинг: {entry.get('rank', 'нет')}")
            
        # ИСПРАВЛЕНИЕ: Принудительно берем самую последнюю запись
        latest_entry = sorted_data[0]
        
        if latest_entry and 'rank' in latest_entry and 'date' in latest_entry:
            rank = latest_entry['rank']
            date = latest_entry['date']
            logger.info(f"ИСПРАВЛЕНИЕ: Возвращаем ПОСЛЕДНИЙ рейтинг {rank} на дату {date}")
            return rank
        else:
            logger.warning("ИСПРАВЛЕНИЕ: В последней записи JSON файла нет корректных данных")
            return None
            
    except Exception as e:
        logger.error(f"ИСПРАВЛЕНИЕ: Ошибка при чтении JSON файла: {str(e)}")
        return None

def clear_rank_cache():
    """
    Очищает кеш рейтинга (пустая функция, так как JSON файл читается каждый раз)
    Используется для совместимости с другими модулями
    """
    logger.info("Кеш JSON файла очищен (файл читается каждый раз)")
    return True

def get_latest_rank_date():
    """
    Возвращает дату последнего рейтинга из JSON файла
    
    Returns:
        str или None: Дата в формате YYYY-MM-DD или None если данные недоступны
    """
    try:
        json_file_path = os.path.join(os.path.dirname(__file__), 'parsed_ranks.json')
        
        if not os.path.exists(json_file_path):
            return None
            
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        if not data or not isinstance(data, list):
            return None
            
        # Находим запись с последней датой
        latest_entry = max(data, key=lambda x: x.get('date', ''))
        
        if latest_entry and 'date' in latest_entry:
            return latest_entry['date']
        else:
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при получении даты из JSON файла: {str(e)}")
        return None