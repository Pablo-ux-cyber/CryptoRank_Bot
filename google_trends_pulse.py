import time
import requests
import json
from datetime import datetime, timedelta
from pytrends.request import TrendReq
from logger import logger

class GoogleTrendsPulse:
    def __init__(self):
        """
        Инициализация модуля для анализа Google Trends
        
        Система использует следующие цветовые сигналы для обозначения рыночных условий,
        согласованные с цветовой схемой Fear & Greed Index:
        - 🔴 Красный сигнал: высокий страх и низкий FOMO - возможная точка входа
        - 🟡 Жёлтый сигнал: растущий интерес к криптовалютам - рынок разогревается
        - ⚪ Белый сигнал: нейтральный интерес без сильных эмоциональных перекосов
        - 🟢 Зелёный сигнал: высокий FOMO-фактор - возможный пик рынка
        - 🔵 Синий сигнал: рынок в спячке - очень низкий общий интерес
        """
        # Создаем подключение с увеличенными таймаутами
        # Не используем параметры retries и backoff_factor из-за несовместимости с новыми версиями библиотеки requests
        self.pytrends = TrendReq(
            hl='en-US', 
            tz=360,
            timeout=(10, 25)  # Увеличенный таймаут для подключения и чтения
        )
        self.last_check_time = None
        self.last_data = None
        self.cache_duration = 12 * 3600  # Увеличено до 12 часов (было 6)
        
        # Категории ключевых запросов для отслеживания разбиты на более мелкие списки
        # (позволяет избежать превышения лимитов)
        self.fomo_keywords = [
            ["bitcoin price"],
            ["crypto millionaire"],
            ["buy bitcoin now"]
        ]
        
        self.fear_keywords = [
            ["crypto crash"],
            ["bitcoin scam"],
            ["crypto tax"]
        ]
        
        self.general_keywords = [
            ["bitcoin"],
            ["cryptocurrency"],
            ["blockchain"]
        ]
        
        # Периоды времени для сравнения трендов
        self.timeframes = {
            "current": "now 7-d",  # Текущая неделя
            "previous": "now 14-d",  # Предыдущая неделя
        }
        
        # Прогрессивные задержки между запросами (для предотвращения ошибок 429)
        self.min_delay = 2.0  # Минимальная задержка между запросами (секунды)
        self.max_delay = 5.0  # Максимальная задержка
    
    def get_trends_data(self):
        """
        Получает данные из Google Trends и анализирует их
        
        Returns:
            dict: Словарь с результатами анализа трендов
        """
        try:
            # Проверяем, прошло ли достаточно времени с последней проверки
            current_time = datetime.now()
            
            # Если данные уже проверялись в течение настроенного срока кеширования, используем кешированные данные
            if self.last_check_time and (current_time - self.last_check_time).total_seconds() < self.cache_duration and self.last_data:
                logger.info(f"Используем кешированные данные Google Trends (проверка менее {self.cache_duration//3600} часов назад)")
                return self.last_data
                
            # Получаем данные для FOMO-запросов
            fomo_score = self._get_category_score(self.fomo_keywords)
            
            # Получаем данные для негативных запросов
            fear_score = self._get_category_score(self.fear_keywords)
            
            # Получаем данные для общих запросов
            general_score = self._get_category_score(self.general_keywords)
            
            # Анализируем соотношения и тренды
            fomo_to_fear_ratio = fomo_score / max(fear_score, 1)  # Предотвращаем деление на ноль
            
            # Определяем сигнал на основе набора правил
            signal, description = self._determine_market_signal(fomo_score, fear_score, general_score, fomo_to_fear_ratio)
            
            # Создаем результирующий словарь
            trends_data = {
                "signal": signal,
                "description": description,
                "fomo_score": fomo_score,
                "fear_score": fear_score,
                "general_score": general_score,
                "fomo_to_fear_ratio": fomo_to_fear_ratio,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Обновляем время последней проверки и кешированные данные
            self.last_check_time = current_time
            self.last_data = trends_data
            
            logger.info(f"Успешно получены данные Google Trends: {signal} - {description}")
            return trends_data
            
        except Exception as e:
            logger.error(f"Ошибка при получении данных Google Trends: {str(e)}")
            
            # Если есть кешированные данные, возвращаем их в случае ошибки
            if self.last_data:
                logger.info("Используем кешированные данные Google Trends из-за ошибки")
                return self.last_data
                
            # Иначе возвращаем нейтральные данные
            return {
                "signal": "⚪",  # Белый сигнал для нейтрального состояния
                "description": "Нейтральный интерес к криптовалютам",
                "fomo_score": 50,
                "fear_score": 50,
                "general_score": 50,
                "fomo_to_fear_ratio": 1.0,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def _get_category_score(self, keyword_groups):
        """
        Получает и анализирует тренды для категории ключевых слов
        
        Args:
            keyword_groups (list): Список групп ключевых слов для анализа
            
        Returns:
            float: Оценка интереса к категории (0-100)
        """
        try:
            results = []
            
            # Обрабатываем каждую группу ключевых слов по отдельности
            for i, keyword_group in enumerate(keyword_groups):
                # Используем динамическую задержку для предотвращения ошибок 429
                if i > 0:
                    # Увеличиваем задержку для каждого последующего запроса
                    delay = min(self.min_delay + (i * 0.5), self.max_delay)
                    logger.info(f"Делаем паузу {delay:.1f} секунд между запросами Google Trends")
                    time.sleep(delay)
                
                # Получаем данные трендов за текущую неделю
                try:
                    self.pytrends.build_payload(keyword_group, cat=0, timeframe=self.timeframes["current"])
                    current_data = self.pytrends.interest_over_time()
                    
                    # Если данных нет, используем нейтральное значение для этой группы
                    if current_data.empty:
                        results.append(50)
                        continue
                    
                    # Вычисляем средний интерес по всем ключевым словам в группе
                    current_avg = current_data[keyword_group].mean().mean()
                    
                    # Делаем паузу, чтобы не превысить лимиты API
                    time.sleep(self.min_delay)
                    
                    # Получаем данные трендов за предыдущую неделю
                    self.pytrends.build_payload(keyword_group, cat=0, timeframe=self.timeframes["previous"])
                    previous_data = self.pytrends.interest_over_time()
                    
                    # Если данных нет, используем только текущее значение
                    if previous_data.empty:
                        results.append(current_avg)
                        continue
                    
                    # Вычисляем средний интерес за предыдущую неделю
                    previous_avg = previous_data[keyword_group].mean().mean()
                    
                    # Вычисляем прирост (в процентах)
                    growth_pct = 0 if previous_avg == 0 else (current_avg - previous_avg) / previous_avg * 100
                    
                    # Модифицируем текущее среднее с учетом прироста
                    adjusted_score = current_avg + min(growth_pct, 30)
                    
                    # Добавляем в результаты
                    results.append(min(max(adjusted_score, 0), 100))
                    
                except Exception as e:
                    logger.error(f"Ошибка при получении данных для группы ключевых слов {keyword_group}: {str(e)}")
                    results.append(50)  # Нейтральное значение при ошибке для этой группы
            
            # Если не удалось получить никаких данных, возвращаем нейтральное значение
            if not results:
                return 50
            
            # Вычисляем среднее по всем группам
            return sum(results) / len(results)
            
        except Exception as e:
            logger.error(f"Ошибка при получении оценки категории: {str(e)}")
            return 50  # Нейтральное значение в случае ошибки
    
    def _determine_market_signal(self, fomo_score, fear_score, general_score, fomo_to_fear_ratio):
        """
        Определяет рыночный сигнал на основе оценок различных категорий
        
        Args:
            fomo_score (float): Оценка FOMO-запросов
            fear_score (float): Оценка запросов, связанных со страхом
            general_score (float): Оценка общих запросов о криптовалютах
            fomo_to_fear_ratio (float): Соотношение FOMO к страху
            
        Returns:
            tuple: (emoji-сигнал, текстовое описание на английском)
        """
        # Правило 1: Высокий FOMO и низкий страх = возможный пик рынка
        # Согласованно с индексом страха и жадности - зеленый для потенциального пика
        if fomo_score > 70 and fomo_to_fear_ratio > 3.0:
            return "🟢", "High FOMO factor - possible market peak"
            
        # Правило 2: Растущий FOMO, средний страх = разогрев рынка
        elif fomo_score > 60 and fomo_to_fear_ratio > 1.5:
            return "🟡", "Growing interest in cryptocurrencies"
            
        # Правило 3: Высокий страх, низкий FOMO = возможная точка входа
        # Согласованно с индексом страха и жадности - красный для потенциальной точки входа
        elif fear_score > 70 and fomo_to_fear_ratio < 0.7:
            return "🔴", "High fear - potential entry point"
            
        # Правило 4: Очень низкий общий интерес = рынок в спячке
        elif general_score < 30:
            return "🔵", "Market hibernation - low general interest"
            
        # По умолчанию: нейтральное состояние
        else:
            return "⚪", "Neutral interest in cryptocurrencies"
    
    def format_trends_message(self, trends_data=None):
        """
        Форматирует данные трендов в краткое сообщение для Telegram
        
        Args:
            trends_data (dict, optional): Данные трендов или None для получения новых данных
            
        Returns:
            str: Форматированное сообщение
        """
        if not trends_data:
            trends_data = self.get_trends_data()
            
        signal = trends_data["signal"]
        description = trends_data["description"]
            
        # Создаем краткое сообщение, содержащее только сигнал и описание
        message = f"{signal} Google Trends: {description}"
            
        return message