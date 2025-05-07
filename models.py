from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class CoinbaseRankHistory(db.Model):
    """
    Модель для хранения истории рейтинга Coinbase в App Store
    """
    id = db.Column(db.Integer, primary_key=True)
    rank = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Категория приложения (Finance, Social, etc)
    category = db.Column(db.String(50), nullable=True)
    
    # Изменение относительно предыдущего значения (up, down, none)
    change_direction = db.Column(db.String(10), nullable=True)
    
    # Абсолютное значение изменения (может быть null для первой записи)
    change_value = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f"<CoinbaseRank {self.rank} at {self.timestamp}>"

class FearGreedIndex(db.Model):
    """
    Модель для хранения истории индекса страха и жадности
    """
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    classification = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<FearGreedIndex {self.value} ({self.classification}) at {self.timestamp}>"

class GoogleTrendsData(db.Model):
    """
    Модель для хранения истории данных Google Trends
    """
    id = db.Column(db.Integer, primary_key=True)
    signal = db.Column(db.String(10), nullable=False)  # Emoji-сигнал
    description = db.Column(db.String(100), nullable=False)
    fomo_score = db.Column(db.Float, nullable=True)
    fear_score = db.Column(db.Float, nullable=True)
    general_score = db.Column(db.Float, nullable=True)
    fomo_to_fear_ratio = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<GoogleTrendsData {self.signal} at {self.timestamp}>"

class OrderBookImbalance(db.Model):
    """
    Модель для хранения истории данных Order Book Imbalance
    """
    id = db.Column(db.Integer, primary_key=True)
    imbalance = db.Column(db.Float, nullable=False)  # Значение дисбаланса (-1.0 до +1.0)
    status = db.Column(db.String(20), nullable=False)  # Текстовый статус (Bullish, Bearish и т.д.)
    signal = db.Column(db.String(10), nullable=False)  # Emoji-сигнал
    description = db.Column(db.String(100), nullable=False)  # Текстовое описание
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<OrderBookImbalance {self.imbalance:.3f} ({self.status}) at {self.timestamp}>"