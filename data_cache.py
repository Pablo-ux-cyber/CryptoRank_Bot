import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

class DataCache:
    """
    Система кеширования для исторических данных криптовалют
    """
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.cache_duration = timedelta(hours=6)  # Кеш действителен 6 часов
        
        # Создание директории кеша
        os.makedirs(cache_dir, exist_ok=True)
        
        # Настройка логирования
        self.logger = logging.getLogger(__name__)
        
        # Файл метаданных кеша
        self.metadata_file = os.path.join(cache_dir, "cache_metadata.json")
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """
        Загрузка метаданных кеша
        """
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Ошибка загрузки метаданных кеша: {e}")
        
        return {}
    
    def _save_metadata(self):
        """
        Сохранение метаданных кеша
        """
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Ошибка сохранения метаданных кеша: {e}")
    
    def _get_cache_filename(self, coin_id: str) -> str:
        """
        Получение имени файла кеша для монеты
        """
        return os.path.join(self.cache_dir, f"{coin_id}.csv")
    
    def _is_cache_valid(self, coin_id: str, required_days: int) -> bool:
        """
        Проверка актуальности кеша
        """
        if coin_id not in self.metadata:
            return False
        
        coin_meta = self.metadata[coin_id]
        
        # Проверка времени создания
        cache_time = datetime.fromisoformat(coin_meta['timestamp'])
        if datetime.now() - cache_time > self.cache_duration:
            return False
        
        # Проверка количества дней
        if coin_meta.get('days', 0) < required_days:
            return False
        
        # Проверка существования файла
        cache_file = self._get_cache_filename(coin_id)
        if not os.path.exists(cache_file):
            return False
        
        return True
    
    def get_coin_data(self, coin_id: str, required_days: int) -> Optional[pd.DataFrame]:
        """
        Получение данных монеты из кеша
        """
        if not self._is_cache_valid(coin_id, required_days):
            return None
        
        try:
            cache_file = self._get_cache_filename(coin_id)
            df = pd.read_csv(cache_file)
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            self.logger.info(f"Данные для {coin_id} загружены из кеша")
            return df
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки кеша для {coin_id}: {e}")
            return None
    
    def save_coin_data(self, coin_id: str, data: pd.DataFrame, days: int):
        """
        Сохранение данных монеты в кеш
        """
        try:
            cache_file = self._get_cache_filename(coin_id)
            data.to_csv(cache_file, index=False)
            
            # Обновление метаданных
            self.metadata[coin_id] = {
                'timestamp': datetime.now().isoformat(),
                'days': days,
                'records': len(data)
            }
            self._save_metadata()
            
            self.logger.info(f"Данные для {coin_id} сохранены в кеш")
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения кеша для {coin_id}: {e}")
    
    def clear_coin_cache(self, coin_id: str):
        """
        Очистка кеша для конкретной монеты
        """
        try:
            cache_file = self._get_cache_filename(coin_id)
            if os.path.exists(cache_file):
                os.remove(cache_file)
            
            if coin_id in self.metadata:
                del self.metadata[coin_id]
                self._save_metadata()
            
            self.logger.info(f"Кеш для {coin_id} очищен")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки кеша для {coin_id}: {e}")
    
    def clear_all(self):
        """
        Полная очистка кеша
        """
        try:
            # Удаление всех файлов кеша
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(self.cache_dir, filename)
                    os.remove(file_path)
            
            # Очистка метаданных
            self.metadata = {}
            self._save_metadata()
            
            self.logger.info("Кеш полностью очищен")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки кеша: {e}")
    
    def get_cache_info(self) -> Dict:
        """
        Получение информации о состоянии кеша
        """
        if not self.metadata:
            return {}
        
        coins_count = len(self.metadata)
        
        # Поиск последнего обновления
        last_update = None
        for coin_meta in self.metadata.values():
            timestamp = datetime.fromisoformat(coin_meta['timestamp'])
            if last_update is None or timestamp > last_update:
                last_update = timestamp
        
        return {
            'coins_count': coins_count,
            'last_update': last_update.strftime('%Y-%m-%d %H:%M') if last_update else 'Нет данных',
            'cache_size_mb': self._get_cache_size()
        }
    
    def _get_cache_size(self) -> float:
        """
        Получение размера кеша в мегабайтах
        """
        total_size = 0
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        except Exception:
            pass
        
        return round(total_size / (1024 * 1024), 2)
    
    def cleanup_expired(self):
        """
        Удаление устаревших данных из кеша
        """
        expired_coins = []
        current_time = datetime.now()
        
        for coin_id, coin_meta in self.metadata.items():
            cache_time = datetime.fromisoformat(coin_meta['timestamp'])
            if current_time - cache_time > self.cache_duration:
                expired_coins.append(coin_id)
        
        for coin_id in expired_coins:
            self.clear_coin_cache(coin_id)
        
        if expired_coins:
            self.logger.info(f"Удалены устаревшие данные для {len(expired_coins)} монет")