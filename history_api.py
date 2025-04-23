import os
import json
from datetime import datetime
from logger import logger

class HistoryAPI:
    """
    API для управления историей данных, используя JSON-файлы вместо базы данных
    """
    def __init__(self, data_dir=None):
        """
        Инициализирует API истории данных
        
        Args:
            data_dir (str, optional): Директория для хранения файлов истории.
                                     Если не указана, используется директория скрипта.
        """
        if data_dir is None:
            self.data_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.data_dir = data_dir
            
        # Пути к файлам истории
        self.rank_history_file = os.path.join(self.data_dir, "rank_history.json")
        self.fear_greed_history_file = os.path.join(self.data_dir, "fear_greed_history.json")
        self.trends_history_file = os.path.join(self.data_dir, "trends_history.json")
        
        # Создаем файлы истории, если они не существуют
        self._ensure_history_files_exist()
    
    def _ensure_history_files_exist(self):
        """Создает файлы истории, если они не существуют"""
        for file_path in [self.rank_history_file, self.fear_greed_history_file, self.trends_history_file]:
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w') as f:
                        json.dump([], f)
                    logger.info(f"Created empty history file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to create history file {file_path}: {str(e)}")
    
    def _load_history(self, file_path):
        """
        Загружает данные истории из JSON-файла
        
        Args:
            file_path (str): Путь к файлу истории
            
        Returns:
            list: Данные истории или пустой список, если произошла ошибка
        """
        try:
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to load history from {file_path}: {str(e)}")
            return []
    
    def _save_history(self, file_path, data):
        """
        Сохраняет данные истории в JSON-файл
        
        Args:
            file_path (str): Путь к файлу истории
            data (list): Данные истории для сохранения
            
        Returns:
            bool: True если сохранение прошло успешно, False в противном случае
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=self._datetime_serializer)
            return True
        except Exception as e:
            logger.error(f"Failed to save history to {file_path}: {str(e)}")
            return False
    
    def _datetime_serializer(self, obj):
        """Сериализатор для объектов datetime в JSON"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def save_rank_history(self, rank, category="Finance", previous_rank=None):
        """
        Сохраняет новое значение рейтинга Coinbase в историю
        
        Args:
            rank (int): Текущий рейтинг Coinbase
            category (str): Категория приложения
            previous_rank (int, optional): Предыдущее значение рейтинга для вычисления изменения
            
        Returns:
            dict: Запись истории рейтинга
        """
        try:
            # Определяем направление изменения и его значение
            change_direction = None
            change_value = None
            
            if previous_rank is not None:
                if rank < previous_rank:
                    change_direction = "up"  # Рейтинг улучшился (число уменьшилось)
                    change_value = previous_rank - rank
                elif rank > previous_rank:
                    change_direction = "down"  # Рейтинг ухудшился (число увеличилось)
                    change_value = rank - previous_rank
                else:
                    change_direction = "none"
                    change_value = 0
            
            # Создаем запись в истории
            history_entry = {
                "rank": rank,
                "category": category,
                "change_direction": change_direction,
                "change_value": change_value,
                "timestamp": datetime.utcnow()
            }
            
            # Загружаем существующую историю
            history = self._load_history(self.rank_history_file)
            
            # Добавляем новую запись
            history.append(history_entry)
            
            # Сохраняем обновленную историю
            if self._save_history(self.rank_history_file, history):
                logger.info(f"Saved new rank history entry: {rank} (change: {change_direction} {change_value})")
                return history_entry
            else:
                return None
            
        except Exception as e:
            logger.error(f"Failed to save rank history: {str(e)}")
            return None
    
    def save_fear_greed_history(self, value, classification):
        """
        Сохраняет новое значение индекса страха и жадности в историю
        
        Args:
            value (int): Значение индекса
            classification (str): Классификация (Fear, Extreme Fear, Neutral, Greed, Extreme Greed)
            
        Returns:
            dict: Запись истории индекса
        """
        try:
            # Создаем запись в истории
            history_entry = {
                "value": value,
                "classification": classification,
                "timestamp": datetime.utcnow()
            }
            
            # Загружаем существующую историю
            history = self._load_history(self.fear_greed_history_file)
            
            # Добавляем новую запись
            history.append(history_entry)
            
            # Сохраняем обновленную историю
            if self._save_history(self.fear_greed_history_file, history):
                logger.info(f"Saved new Fear & Greed Index history entry: {value} ({classification})")
                return history_entry
            else:
                return None
            
        except Exception as e:
            logger.error(f"Failed to save Fear & Greed Index history: {str(e)}")
            return None
    
    def save_google_trends_history(self, signal, description, fomo_score=None, fear_score=None, 
                                 general_score=None, fomo_to_fear_ratio=None):
        """
        Сохраняет новые данные Google Trends в историю
        
        Args:
            signal (str): Emoji-сигнал
            description (str): Текстовое описание сигнала
            fomo_score (float, optional): Оценка FOMO
            fear_score (float, optional): Оценка страха
            general_score (float, optional): Общая оценка
            fomo_to_fear_ratio (float, optional): Соотношение FOMO к страху
            
        Returns:
            dict: Запись истории данных Google Trends
        """
        try:
            # Создаем запись в истории
            history_entry = {
                "signal": signal,
                "description": description,
                "fomo_score": fomo_score,
                "fear_score": fear_score,
                "general_score": general_score,
                "fomo_to_fear_ratio": fomo_to_fear_ratio,
                "timestamp": datetime.utcnow()
            }
            
            # Загружаем существующую историю
            history = self._load_history(self.trends_history_file)
            
            # Добавляем новую запись
            history.append(history_entry)
            
            # Сохраняем обновленную историю
            if self._save_history(self.trends_history_file, history):
                logger.info(f"Saved new Google Trends history entry: {signal} - {description}")
                return history_entry
            else:
                return None
            
        except Exception as e:
            logger.error(f"Failed to save Google Trends history: {str(e)}")
            return None
    
    def get_rank_history(self, limit=100, offset=0):
        """
        Получает историю рейтинга Coinbase, отсортированную по времени (новые сначала)
        
        Args:
            limit (int): Максимальное количество записей
            offset (int): Смещение для пагинации
            
        Returns:
            list: Список записей истории рейтинга
        """
        try:
            history = self._load_history(self.rank_history_file)
            
            # Парсим timestamp в datetime для правильной сортировки
            for entry in history:
                if 'timestamp' in entry and isinstance(entry['timestamp'], str):
                    try:
                        entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                    except (ValueError, TypeError):
                        entry['timestamp'] = datetime.utcnow()
            
            # Сортируем по времени (новые сначала)
            history.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
            
            # Применяем пагинацию
            return history[offset:offset + limit]
        except Exception as e:
            logger.error(f"Failed to get rank history: {str(e)}")
            return []
    
    def get_fear_greed_history(self, limit=100, offset=0):
        """
        Получает историю индекса страха и жадности, отсортированную по времени (новые сначала)
        
        Args:
            limit (int): Максимальное количество записей
            offset (int): Смещение для пагинации
            
        Returns:
            list: Список записей истории индекса
        """
        try:
            history = self._load_history(self.fear_greed_history_file)
            
            # Парсим timestamp в datetime для правильной сортировки
            for entry in history:
                if 'timestamp' in entry and isinstance(entry['timestamp'], str):
                    try:
                        entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                    except (ValueError, TypeError):
                        entry['timestamp'] = datetime.utcnow()
            
            # Сортируем по времени (новые сначала)
            history.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
            
            # Применяем пагинацию
            return history[offset:offset + limit]
        except Exception as e:
            logger.error(f"Failed to get Fear & Greed Index history: {str(e)}")
            return []
    
    def get_google_trends_history(self, limit=100, offset=0):
        """
        Получает историю данных Google Trends, отсортированную по времени (новые сначала)
        
        Args:
            limit (int): Максимальное количество записей
            offset (int): Смещение для пагинации
            
        Returns:
            list: Список записей истории данных Google Trends
        """
        try:
            history = self._load_history(self.trends_history_file)
            
            # Парсим timestamp в datetime для правильной сортировки
            for entry in history:
                if 'timestamp' in entry and isinstance(entry['timestamp'], str):
                    try:
                        entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                    except (ValueError, TypeError):
                        entry['timestamp'] = datetime.utcnow()
            
            # Сортируем по времени (новые сначала)
            history.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
            
            # Применяем пагинацию
            return history[offset:offset + limit]
        except Exception as e:
            logger.error(f"Failed to get Google Trends history: {str(e)}")
            return []