from datetime import datetime
from models import db, CoinbaseRankHistory, FearGreedIndex, GoogleTrendsData
from logger import logger

class HistoryManager:
    """
    Менеджер для работы с историей данных
    Сохраняет историю рейтинга Coinbase, индекса страха и жадности, и данных Google Trends
    """
    
    @staticmethod
    def save_rank_history(rank, category="Finance", previous_rank=None):
        """
        Сохраняет новое значение рейтинга Coinbase в историю
        
        Args:
            rank (int): Текущий рейтинг Coinbase
            category (str): Категория приложения
            previous_rank (int, optional): Предыдущее значение рейтинга для вычисления изменения
            
        Returns:
            CoinbaseRankHistory: Созданный объект истории рейтинга
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
            history_entry = CoinbaseRankHistory(
                rank=rank,
                category=category,
                change_direction=change_direction,
                change_value=change_value,
                timestamp=datetime.utcnow()
            )
            
            # Сохраняем в базу данных
            db.session.add(history_entry)
            db.session.commit()
            
            logger.info(f"Saved new rank history entry: {rank} (change: {change_direction} {change_value})")
            return history_entry
            
        except Exception as e:
            logger.error(f"Failed to save rank history: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def save_fear_greed_history(value, classification):
        """
        Сохраняет новое значение индекса страха и жадности в историю
        
        Args:
            value (int): Значение индекса
            classification (str): Классификация (Fear, Extreme Fear, Neutral, Greed, Extreme Greed)
            
        Returns:
            FearGreedIndex: Созданный объект истории индекса
        """
        try:
            # Создаем запись в истории
            history_entry = FearGreedIndex(
                value=value,
                classification=classification,
                timestamp=datetime.utcnow()
            )
            
            # Сохраняем в базу данных
            db.session.add(history_entry)
            db.session.commit()
            
            logger.info(f"Saved new Fear & Greed Index history entry: {value} ({classification})")
            return history_entry
            
        except Exception as e:
            logger.error(f"Failed to save Fear & Greed Index history: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def save_google_trends_history(signal, description, fomo_score=None, fear_score=None, 
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
            GoogleTrendsData: Созданный объект истории данных Google Trends
        """
        try:
            # Создаем запись в истории
            history_entry = GoogleTrendsData(
                signal=signal,
                description=description,
                fomo_score=fomo_score,
                fear_score=fear_score,
                general_score=general_score,
                fomo_to_fear_ratio=fomo_to_fear_ratio,
                timestamp=datetime.utcnow()
            )
            
            # Сохраняем в базу данных
            db.session.add(history_entry)
            db.session.commit()
            
            logger.info(f"Saved new Google Trends history entry: {signal} - {description}")
            return history_entry
            
        except Exception as e:
            logger.error(f"Failed to save Google Trends history: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_rank_history(limit=100, offset=0):
        """
        Получает историю рейтинга Coinbase, отсортированную по времени (новые сначала)
        
        Args:
            limit (int): Максимальное количество записей
            offset (int): Смещение для пагинации
            
        Returns:
            list: Список объектов истории рейтинга
        """
        try:
            history = CoinbaseRankHistory.query.order_by(
                CoinbaseRankHistory.timestamp.desc()
            ).offset(offset).limit(limit).all()
            
            return history
        except Exception as e:
            logger.error(f"Failed to get rank history: {str(e)}")
            return []
    
    @staticmethod
    def get_fear_greed_history(limit=100, offset=0):
        """
        Получает историю индекса страха и жадности, отсортированную по времени (новые сначала)
        
        Args:
            limit (int): Максимальное количество записей
            offset (int): Смещение для пагинации
            
        Returns:
            list: Список объектов истории индекса
        """
        try:
            history = FearGreedIndex.query.order_by(
                FearGreedIndex.timestamp.desc()
            ).offset(offset).limit(limit).all()
            
            return history
        except Exception as e:
            logger.error(f"Failed to get Fear & Greed Index history: {str(e)}")
            return []
    
    @staticmethod
    def get_google_trends_history(limit=100, offset=0):
        """
        Получает историю данных Google Trends, отсортированную по времени (новые сначала)
        
        Args:
            limit (int): Максимальное количество записей
            offset (int): Смещение для пагинации
            
        Returns:
            list: Список объектов истории данных Google Trends
        """
        try:
            history = GoogleTrendsData.query.order_by(
                GoogleTrendsData.timestamp.desc()
            ).offset(offset).limit(limit).all()
            
            return history
        except Exception as e:
            logger.error(f"Failed to get Google Trends history: {str(e)}")
            return []