import os
import ccxt
import logging
import time
from datetime import datetime
from logger import logger

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
        self.logger = logger
        
        # Импортируем конфигурацию из общего файла config.py
        try:
            from config import GBI_EXCHANGE, GBI_MARKETS, GBI_LIMIT, GBI_THRESHOLD_STRONG_BULL, GBI_THRESHOLD_WEAK_BULL, GBI_THRESHOLD_WEAK_BEAR, GBI_THRESHOLD_STRONG_BEAR
            self.default_exchange_id = GBI_EXCHANGE
            self.default_symbols = GBI_MARKETS.split(',')
            self.default_limit = GBI_LIMIT
            self.thresholds = {
                'strong_bull': GBI_THRESHOLD_STRONG_BULL,
                'weak_bull': GBI_THRESHOLD_WEAK_BULL,
                'weak_bear': GBI_THRESHOLD_WEAK_BEAR,
                'strong_bear': GBI_THRESHOLD_STRONG_BEAR,
            }
        except ImportError:
            # Fallback на переменные окружения, если не удалось импортировать config.py
            self.default_exchange_id = os.getenv('GBI_EXCHANGE', 'binance')
            default_markets = 'BTC/USDT,ETH/USDT,SOL/USDT,ADA/USDT,BNB/USDT'
            self.default_symbols = os.getenv('GBI_MARKETS', default_markets).split(',')
            self.default_limit = int(os.getenv('GBI_LIMIT', '100'))
            self.thresholds = {
                'strong_bull': float(os.getenv('GBI_THRESHOLD_STRONG_BULL', '0.50')),
                'weak_bull': float(os.getenv('GBI_THRESHOLD_WEAK_BULL', '0.20')),
                'weak_bear': float(os.getenv('GBI_THRESHOLD_WEAK_BEAR', '-0.20')),
                'strong_bear': float(os.getenv('GBI_THRESHOLD_STRONG_BEAR', '-0.50')),
            }
        
        self.logger.info(f"Initialized Order Book Imbalance module with markets: {self.default_symbols}")
        self.logger.info(f"Using exchange: {self.default_exchange_id}, depth: {self.default_limit}")

    def get_order_book_imbalance(self, symbols=None, limit=None, exchange_id=None):
        """
        Calculate a single imbalance value across multiple trading pairs.

        Args:
            symbols (list[str], optional): List of market symbols
            limit (int, optional): Depth of order book levels to fetch
            exchange_id (str, optional): CCXT exchange identifier

        Returns:
            dict: Imbalance data with value, status, and timestamp or None if error
        """
        self.logger.info("Запрос данных Order Book Imbalance...")
        
        try:
            # Use default values if not provided
            symbols = symbols or self.default_symbols
            limit = limit or self.default_limit
            exchange_id = exchange_id or self.default_exchange_id

            # Initialize exchange
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({
                'enableRateLimit': True,
            })

            # Initialize accumulators for bids and asks volumes
            total_bid_volume = 0.0
            total_ask_volume = 0.0
            processed_symbols = 0

            # Process each symbol
            for symbol in symbols:
                try:
                    # Fetch order book
                    order_book = exchange.fetch_order_book(symbol, limit)
                    
                    # Calculate sum of volumes for bids and asks
                    symbol_bid_volume = sum(bid[1] for bid in order_book['bids'])
                    symbol_ask_volume = sum(ask[1] for ask in order_book['asks'])
                    
                    # Accumulate volumes
                    total_bid_volume += symbol_bid_volume
                    total_ask_volume += symbol_ask_volume
                    processed_symbols += 1
                    
                    self.logger.info(f"Processed {symbol}: Bids={symbol_bid_volume:.2f}, Asks={symbol_ask_volume:.2f}")
                except Exception as e:
                    self.logger.error(f"Error fetching order book for {symbol}: {str(e)}")
                    # Продолжаем с другими символами вместо возврата ошибки
                    continue

            # Check if we have valid volume data (at least один символ успешно обработан)
            if processed_symbols == 0 or total_bid_volume <= 0 or total_ask_volume <= 0:
                self.logger.error("Invalid volume data: bid or ask volume is zero")
                return None  # No fallback data, just return None

            # Calculate global order-book imbalance
            # Normalize to range [-1, 1] where:
            # -1 = 100% asks (extreme sell pressure)
            # 0 = equal bids and asks
            # +1 = 100% bids (extreme buy pressure)
            total_volume = total_bid_volume + total_ask_volume
            imbalance = (total_bid_volume - total_ask_volume) / total_volume
            
            # Round to 2 decimal places for display
            imbalance = round(imbalance, 2)
            
            # Interpret the imbalance
            status, signal, description = self._determine_market_signal(imbalance)
            
            # Create result object
            result = {
                'imbalance': imbalance,
                'status': status,
                'signal': signal,
                'description': description,
                'timestamp': int(time.time()),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'markets_processed': processed_symbols,
                'total_markets': len(symbols)
            }
            
            self.logger.info(f"Order Book Imbalance: {imbalance:.2f} ({status}) {signal}")
            return result

        except Exception as e:
            self.logger.error(f"Error calculating order book imbalance: {str(e)}")
            return None  # No fallback data, just return None

    def _determine_market_signal(self, imbalance):
        """
        Определяет рыночный сигнал на основе значения дисбаланса и настроенных порогов
        
        Args:
            imbalance (float): Значение дисбаланса в диапазоне [-1.0, +1.0]
            
        Returns:
            tuple: (текстовый статус, emoji-сигнал, текстовое описание)
        """
        if imbalance <= self.thresholds['strong_bear']:
            return "Strongly Bearish", "🔴", "Significant selling pressure"
        elif imbalance <= self.thresholds['weak_bear']:
            return "Bearish", "🟠", "Moderate selling pressure" 
        elif imbalance < self.thresholds['weak_bull']:
            return "Neutral", "⚪", "Balanced order book"
        elif imbalance < self.thresholds['strong_bull']:
            return "Bullish", "🟢", "Moderate buying pressure"
        else:
            return "Strongly Bullish", "🔵", "Significant buying pressure"

    def _create_fallback_data(self):
        """
        Returns None in case of an error instead of providing fallback data
        We should not show any imbalance data when there's an error
        """
        self.logger.warning("Order Book Imbalance error - indicator will not be shown")
        return None

    def format_imbalance_message(self, imbalance_data=None):
        """
        Форматирует данные дисбаланса ордеров в упрощенное сообщение для Telegram
        
        Args:
            imbalance_data (dict, optional): Данные дисбаланса или None для получения новых данных
            
        Returns:
            str: Форматированное сообщение в упрощенном формате или None при ошибке
        """
        if not imbalance_data:
            imbalance_data = self.get_order_book_imbalance()
            
        if not imbalance_data:
            return None
            
        # Создаем базовое сообщение с эмодзи и статусом
        message = f"{imbalance_data['signal']} Order Book Imbalance: {imbalance_data['status']}"
        
        # Добавляем описание
        if 'description' in imbalance_data and imbalance_data['description']:
            message += f" - {imbalance_data['description']}"
            
        # Добавляем значение дисбаланса для более точной информации
        if 'imbalance' in imbalance_data:
            message += f" ({imbalance_data['imbalance']})"
            
        return message