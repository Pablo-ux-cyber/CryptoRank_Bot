import logging
from datetime import datetime
from typing import Dict, Optional
from crypto_analyzer_cryptocompare import CryptoAnalyzer

class MarketBreadthIndicator:
    """
    Модуль для анализа ширины криптовалютного рынка
    Интегрирован в Telegram бота для мониторинга рыночных условий
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analyzer = CryptoAnalyzer(cache=None)  # Отключаем кеширование
        
        # Параметры по умолчанию
        self.top_n = 49  # Обновленный список из 49 монет по вашему файлу (убираем дубликат NEAR)
        self.ma_period = 200
        self.analysis_days = 547  # 1.5 года данных как требуется пользователем
        
        # Для избежания повторной загрузки данных
        self.last_historical_data = None
        self.last_indicator_data = None
        
    def get_market_breadth_data(self, fast_mode: bool = False) -> Optional[Dict]:
        """
        Получает текущие данные индикатора ширины рынка
        
        Args:
            fast_mode (bool): Если True, использует только 10 топ монет для быстрого тестирования
        
        Returns:
            dict: Данные индикатора или None при ошибке
        """
        try:
            self.logger.info("Начинаем анализ ширины рынка...")
            
            # Получение топ монет (всегда используем полный список - никаких быстрых тестов)
            coin_count = self.top_n
            top_coins = self.analyzer.get_top_coins(coin_count)
            if not top_coins:
                self.logger.error("Не удалось получить список топ монет")
                return None
            
            self.logger.info(f"Получено {len(top_coins)} топ монет")
            
            # Загрузка исторических данных
            historical_data = self.analyzer.load_historical_data(
                top_coins, 
                self.ma_period + self.analysis_days + 100  # Запас для расчета MA (200 + 547 + 100 = 847 дней)
            )
            
            if not historical_data:
                self.logger.error("Не удалось загрузить исторические данные")
                return None
            
            self.logger.info(f"Загружены данные для {len(historical_data)} монет")
            
            # Расчет индикатора
            indicator_data = self.analyzer.calculate_market_breadth(
                historical_data, 
                self.ma_period, 
                self.analysis_days
            )
            
            if indicator_data.empty:
                self.logger.error("Не удалось рассчитать индикатор")
                return None
            
            # Получение сводной информации
            summary = self.analyzer.get_market_summary(indicator_data)
            
            # ИСПРАВЛЕНИЕ: Сохраняем данные для повторного использования
            self.last_historical_data = historical_data
            self.last_indicator_data = indicator_data
            
            # Дополнительная обработка для телеграм сообщения
            current_value = summary.get('current_value', 0)
            
            # Определение рыночного сигнала
            if current_value >= 80:
                signal = "🔴"
                condition = "Overbought"
                description = "Most coins above MA200, possible correction"
            elif current_value <= 20:
                signal = "🟢" 
                condition = "Oversold"
                description = "Most coins below MA200, possible bounce"
            else:
                signal = "🟡"
                condition = "Neutral"
                description = "Mixed market signals"
            
            return {
                'signal': signal,
                'condition': condition,
                'description': description,
                'current_value': current_value,
                'average_value': summary.get('average_value', 0),
                'max_value': summary.get('max_value', 0),
                'min_value': summary.get('min_value', 0),
                'total_coins': len(historical_data),
                'analysis_period': self.analysis_days,
                'ma_period': self.ma_period,
                # ИСПРАВЛЕНИЕ: Добавляем данные для повторного использования в create_quick_chart
                'historical_data': historical_data,
                'indicator_data': indicator_data
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе ширины рынка: {str(e)}")
            return None
    
    def format_breadth_message(self, breadth_data: Optional[Dict] = None) -> Optional[str]:
        """
        Форматирует данные индикатора ширины рынка в упрощенное сообщение для Telegram
        
        Args:
            breadth_data (dict, optional): Данные индикатора или None для получения новых данных
            
        Returns:
            str: Форматированное сообщение или None при ошибке
        """
        if breadth_data is None:
            breadth_data = self.get_market_breadth_data()
        
        if not breadth_data:
            return None
        
        try:
            # Определяем статус на английском для упрощенного формата
            current_value = breadth_data['current_value']
            if current_value >= 80:
                status = "Overbought"
            elif current_value <= 20:
                status = "Oversold" 
            else:
                status = "Neutral"
            
            # Упрощенный формат: Market by 200MA: {emoji} {Status}: {percentage}%
            message = f"Market by 200MA: {breadth_data['signal']} {status}: {current_value:.1f}%"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Ошибка форматирования сообщения о ширине рынка: {str(e)}")
            return None
    
    def get_current_market_breadth(self) -> float:
        """
        Получает только текущее значение индикатора ширины рынка
        
        Returns:
            float: Текущее значение индикатора (0-100) или -1 при ошибке
        """
        try:
            breadth_data = self.get_market_breadth_data()
            if breadth_data:
                return breadth_data['current_value']
            return -1
        except Exception as e:
            self.logger.error(f"Ошибка получения текущего значения ширины рынка: {str(e)}")
            return -1
    
    def clear_cache(self):
        """
        Метод для совместимости - кеширование отключено
        """
        self.logger.info("Кеширование отключено - ничего не нужно очищать")