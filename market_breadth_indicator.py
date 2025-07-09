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
        self.top_n = 50
        self.ma_period = 200
        self.analysis_days = 30  # Короткий период для телеграм сообщений
        
    def get_market_breadth_data(self) -> Optional[Dict]:
        """
        Получает текущие данные индикатора ширины рынка
        
        Returns:
            dict: Данные индикатора или None при ошибке
        """
        try:
            self.logger.info("Начинаем анализ ширины рынка...")
            
            # Получение топ монет
            top_coins = self.analyzer.get_top_coins(self.top_n)
            if not top_coins:
                self.logger.error("Не удалось получить список топ монет")
                return None
            
            self.logger.info(f"Получено {len(top_coins)} топ монет")
            
            # Загрузка исторических данных
            historical_data = self.analyzer.load_historical_data(
                top_coins, 
                self.ma_period + self.analysis_days + 50  # Запас для расчета MA
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
            
            # Дополнительная обработка для телеграм сообщения
            current_value = summary.get('current_value', 0)
            
            # Определение рыночного сигнала
            if current_value >= 80:
                signal = "🔴"
                condition = "Перекупленность"
                description = "Большинство монет выше MA200, возможна коррекция"
            elif current_value <= 20:
                signal = "🟢" 
                condition = "Перепроданность"
                description = "Большинство монет ниже MA200, возможен отскок"
            else:
                signal = "🟡"
                condition = "Нейтральная зона"
                description = "Смешанные сигналы рынка"
            
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
                'ma_period': self.ma_period
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе ширины рынка: {str(e)}")
            return None
    
    def format_breadth_message(self, breadth_data: Optional[Dict] = None) -> Optional[str]:
        """
        Форматирует данные индикатора ширины рынка в сообщение для Telegram
        
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
            # Формирование сообщения
            message = f"""📊 **Ширина рынка (MA{breadth_data['ma_period']})**

{breadth_data['signal']} **{breadth_data['condition']}**: {breadth_data['current_value']:.1f}%

{breadth_data['description']}

📈 **Статистика ({breadth_data['analysis_period']}д):**
• Текущий: {breadth_data['current_value']:.1f}%
• Средний: {breadth_data['average_value']:.1f}%
• Максимум: {breadth_data['max_value']:.1f}%
• Минимум: {breadth_data['min_value']:.1f}%

📋 Анализ {breadth_data['total_coins']} топ монет"""
            
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
        Очищает кеш данных
        """
        try:
            self.cache.clear_all()
            self.logger.info("Кеш индикатора ширины рынка очищен")
        except Exception as e:
            self.logger.error(f"Ошибка очистки кеша: {str(e)}")