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
        self.default_exchange_id = 'binance'
        self.default_symbols = ['BTC/USDT', 'ETH/USDT']
        self.default_limit = 20  # Depth of order book levels

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

            # Process each symbol
            for symbol in symbols:
                try:
                    # Fetch order book
                    order_book = exchange.fetch_order_book(symbol, limit)
                    
                    # Calculate volume-weighted averages for bids and asks
                    symbol_bid_volume = sum(bid[1] for bid in order_book['bids'])
                    symbol_ask_volume = sum(ask[1] for ask in order_book['asks'])
                    
                    # Accumulate volumes
                    total_bid_volume += symbol_bid_volume
                    total_ask_volume += symbol_ask_volume
                    
                    self.logger.info(f"Processed {symbol}: Bids={symbol_bid_volume:.2f}, Asks={symbol_ask_volume:.2f}")
                except Exception as e:
                    self.logger.error(f"Error fetching order book for {symbol}: {str(e)}")
                    continue

            # Check if we have valid volume data
            if total_bid_volume <= 0 or total_ask_volume <= 0:
                self.logger.error("Invalid volume data: bid or ask volume is zero")
                return self._create_fallback_data()

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
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
            self.logger.info(f"Order Book Imbalance: {imbalance:.2f} ({status}) {signal}")
            return result

        except Exception as e:
            self.logger.error(f"Error calculating order book imbalance: {str(e)}")
            return self._create_fallback_data()

    def _interpret_imbalance(self, value):
        """
        Return human-readable interpretation of imbalance value.
        """
        if value < -0.5:
            return "Strongly Bearish"
        elif value < -0.2:
            return "Bearish"
        elif value < 0.2:
            return "Neutral"
        elif value < 0.5:
            return "Bullish"
        else:
            return "Strongly Bullish"

    def _determine_market_signal(self, imbalance):
        """
        Определяет рыночный сигнал на основе значения дисбаланса
        
        Args:
            imbalance (float): Значение дисбаланса в диапазоне [-1.0, +1.0]
            
        Returns:
            tuple: (текстовый статус, emoji-сигнал, текстовое описание)
        """
        if imbalance < -0.5:
            return "Strongly Bearish", "🔴", "Significant selling pressure"
        elif imbalance < -0.2:
            return "Bearish", "🟠", "Moderate selling pressure" 
        elif imbalance < 0.2:
            return "Neutral", "⚪", "Balanced order book"
        elif imbalance < 0.5:
            return "Bullish", "🟢", "Moderate buying pressure"
        else:
            return "Strongly Bullish", "🔵", "Significant buying pressure"

    def _create_fallback_data(self):
        """
        Creates fallback data in case of an error
        """
        return {
            'imbalance': 0.0,
            'status': 'Neutral',
            'signal': '⚪',
            'description': 'Balanced order book (fallback)',
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