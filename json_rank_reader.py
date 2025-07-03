import json
import os
from datetime import datetime
from logger import logger

def get_rank_from_json():
    """
    Читает данные рейтинга из JSON файла и возвращает рейтинг за последнюю дату
    
    Returns:
        int или None: Рейтинг Coinbase за последнюю дату или None если данные недоступны
    """
    try:
        json_file_path = os.path.join(os.path.dirname(__file__), 'parsed_ranks.json')
        
        if not os.path.exists(json_file_path):
            logger.warning(f"JSON файл не найден: {json_file_path}")
            return None
            
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        if not data or not isinstance(data, list):
            logger.warning("JSON файл пустой или имеет неверный формат")
            return None
            
        # Находим запись с последней датой
        latest_entry = max(data, key=lambda x: x.get('date', ''))
        
        if latest_entry and 'rank' in latest_entry and 'date' in latest_entry:
            rank = latest_entry['rank']
            date = latest_entry['date']
            logger.info(f"Найден рейтинг из JSON файла: {rank} на дату {date}")
            return rank
        else:
            logger.warning("В JSON файле нет корректных данных")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при чтении JSON файла: {str(e)}")
        return None

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