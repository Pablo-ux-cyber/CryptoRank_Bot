import os
import ccxt
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)

# List of markets to include in the global imbalance calculation
MARKETS = os.getenv('GBI_MARKETS', 'BTC/USDT,ETH/USDT,SOL/USDT,ADA/USDT,BNB/USDT').split(',')
EXCHANGE_ID = os.getenv('GBI_EXCHANGE', 'binance')
ORDERBOOK_LIMIT = int(os.getenv('GBI_LIMIT', 100))

# Thresholds for interpretation
THRESHOLDS = {
    'strong_bull': 0.50,
    'weak_bull': 0.20,
    'weak_bear': -0.20,
    'strong_bear': -0.50,
}

class OrderBookImbalance:
    def __init__(self):
        """
        Инициализация модуля для анализа Global Order-Book Imbalance
        
        Система использует следующие сигналы для обозначения рыночных условий:
        - 🔴 Сильно медвежий рынок (< -0.50): Значительное превышение предложения над спросом
        - 🟠 Медвежий рынок (от -0.50 до -0.20): Умеренное превышение предложения
        - ⚪ Нейтральный рынок (от -0.20 до +0.20): Равновесие спроса и предложения
        - 🟢 Бычий рынок (от +0.20 до +0.50): Умеренное превышение спроса
        - 🔵 Сильно бычий рынок (> +0.50): Значительное превышение спроса над предложением
        """
        self.last_data = None
        self.history_file = 'gbi_history.json'

    def get_order_book_imbalance(self, symbols=None, limit=None, exchange_id=None):
        """
        Calculate a single imbalance value across multiple trading pairs.

        Args:
            symbols (list[str], optional): List of market symbols
            limit (int, optional): Depth of order book levels to fetch
            exchange_id (str, optional): CCXT exchange identifier

        Returns:
            dict: Imbalance data with value, status, and timestamp
        """
        try:
            symbols = symbols or MARKETS
            limit = limit or ORDERBOOK_LIMIT
            exchange_id = exchange_id or EXCHANGE_ID
            
            logger.info(f"Calculating Global Order-Book Imbalance for: {symbols}")
            
            exchange = getattr(ccxt, exchange_id)()
            total_bids = 0.0
            total_asks = 0.0

            for sym in symbols:
                try:
                    ob = exchange.fetch_order_book(sym, limit)
                    total_bids += sum(qty for _, qty in ob['bids'])
                    total_asks += sum(qty for _, qty in ob['asks'])
                except Exception as e:
                    logger.warning(f"Failed to fetch order book for {sym}: {e}")

            if total_bids + total_asks == 0:
                imbalance = 0.0
            else:
                imbalance = (total_bids - total_asks) / (total_bids + total_asks)
            
            status = self._interpret_imbalance(imbalance)
            signal, description = self._determine_market_signal(imbalance)
            
            result = {
                'imbalance': round(imbalance, 3),
                'status': status,
                'signal': signal,
                'description': description,
                'timestamp': int(time.time()),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
            logger.info(f"Global Imbalance: {imbalance:+.3f} ({status}) {signal}")
            self.last_data = result
            return result
            
        except Exception as e:
            logger.error(f"Error calculating order book imbalance: {e}")
            return self._create_fallback_data()
    
    def _interpret_imbalance(self, value):
        """
        Return human-readable interpretation of imbalance value.
        """
        if value >= THRESHOLDS['strong_bull']:
            return 'Strong Bullish'
        if value >= THRESHOLDS['weak_bull']:
            return 'Bullish'
        if value <= THRESHOLDS['strong_bear']:
            return 'Strong Bearish'
        if value <= THRESHOLDS['weak_bear']:
            return 'Bearish'
        return 'Neutral'
    
    def _determine_market_signal(self, imbalance):
        """
        Определяет рыночный сигнал на основе значения дисбаланса
        
        Args:
            imbalance (float): Значение дисбаланса в диапазоне [-1.0, +1.0]
            
        Returns:
            tuple: (emoji-сигнал, текстовое описание)
        """
        if imbalance <= THRESHOLDS['strong_bear']:
            return "🔴", "Strong sell pressure"
        elif imbalance <= THRESHOLDS['weak_bear']:
            return "🟠", "Moderate sell pressure"
        elif imbalance >= THRESHOLDS['strong_bull']:
            return "🔵", "Strong buy pressure"
        elif imbalance >= THRESHOLDS['weak_bull']:
            return "🟢", "Moderate buy pressure"
        else:
            return "⚪", "Neutral market balance"
    
    def _create_fallback_data(self):
        """
        Creates fallback data in case of an error
        """
        if self.last_data:
            return self.last_data
        
        return {
            'imbalance': 0.0,
            'status': 'Neutral',
            'signal': "⚪",
            'description': "Neutral market balance",
            'timestamp': int(time.time()),
            'date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def format_imbalance_message(self, imbalance_data=None):
        """
        Форматирует данные дисбаланса ордеров в упрощенное сообщение для Telegram
        
        Args:
            imbalance_data (dict, optional): Данные дисбаланса или None для получения новых данных
            
        Returns:
            str: Форматированное сообщение в упрощенном формате
        """
        if not imbalance_data:
            if not self.last_data:
                imbalance_data = self.get_order_book_imbalance()
            else:
                imbalance_data = self.last_data
        
        signal = imbalance_data.get('signal', "⚪")
        status = imbalance_data.get('status', 'Neutral')
        imbalance = imbalance_data.get('imbalance', 0.0)
        description = imbalance_data.get('description', "Neutral market balance")
        
        # Форматируем значение дисбаланса, чтобы всегда показывать знак + или -
        if imbalance > 0:
            imbalance_str = f"+{imbalance:.3f}"
        else:
            imbalance_str = f"{imbalance:.3f}"
        
        # Формируем сообщение в формате: "Эмодзи Статус: значение_дисбаланса - описание"
        message = f"{signal} Order Book: {status} ({imbalance_str}) - {description}"
        
        return message


# Для тестирования модуля
if __name__ == '__main__':
    gbi = OrderBookImbalance()
    imbalance_data = gbi.get_order_book_imbalance()
    message = gbi.format_imbalance_message(imbalance_data)
    print(message)