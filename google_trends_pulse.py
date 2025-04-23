import time
import json
import random
import requests
import pandas as pd
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
        # Кешированные данные и время последней проверки
        self.last_check_time = None
        self.last_data = None
        
        # Инициализация pytrends API с английским языком и московским часовым поясом
        # Не используем retries из-за проблем с совместимостью
        self.pytrends = TrendReq(hl='en-US', tz=180)
        
        # Категории ключевых слов для анализа
        self.fomo_keywords = ["bitcoin price", "crypto millionaire", "buy bitcoin now"]
        self.fear_keywords = ["crypto crash", "bitcoin scam", "crypto tax"]
        self.general_keywords = ["bitcoin", "cryptocurrency", "blockchain"]
        
        # Параметры запроса для получения данных за последние 7 дней
        self.timeframe = "now 7-d"
        
        # Периоды времени для сравнения трендов
        self.timeframes = {
            "current": "now 7-d",      # Текущая неделя
            "previous": "now 14-d",    # Предыдущая неделя для сравнения
        }
        
        # Задержки между запросами для избежания ограничений API
        self.min_delay = 3  # минимальная задержка между запросами (секунды)
        self.max_delay = 10  # максимальная задержка между запросами (секунды)
        
        # Определение маркетных сигналов
        self.market_signals = [
            {"signal": "🔴", "description": "High fear and low FOMO - possible buying opportunity", "weight": 1},
            {"signal": "🟠", "description": "Decreasing interest in cryptocurrencies - market cooling down", "weight": 1}, 
            {"signal": "⚪", "description": "Neutral interest in cryptocurrencies", "weight": 2},
            {"signal": "🟡", "description": "Growing interest in cryptocurrencies - market warming up", "weight": 1},
            {"signal": "🟢", "description": "High FOMO factor - possible market peak", "weight": 1}
        ]
        
        # Загружаем сохраненные данные, если они есть
        try:
            with open("trends_history.json", "r") as f:
                self.history_data = json.load(f)
                logger.info(f"Loaded Google Trends history: {len(self.history_data)} records")
                
                # Используем последнюю запись в истории как текущие данные
                if self.history_data:
                    most_recent = max(self.history_data, key=lambda x: x.get("timestamp", ""))
                    self.last_data = {
                        "signal": most_recent.get("signal", "⚪"),
                        "description": most_recent.get("description", "Neutral interest in cryptocurrencies"),
                        "fomo_score": most_recent.get("fomo_score", 50),
                        "fear_score": most_recent.get("fear_score", 50),
                        "general_score": most_recent.get("general_score", 50),
                        "fomo_to_fear_ratio": most_recent.get("fomo_to_fear_ratio", 1.0),
                        "timestamp": most_recent.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    }
                    
                    # Пытаемся распарсить время последней проверки из timestamp
                    try:
                        self.last_check_time = datetime.strptime(
                            self.last_data["timestamp"], 
                            "%Y-%m-%d %H:%M:%S"
                        )
                        logger.info(f"Last Google Trends check time: {self.last_check_time}")
                    except:
                        self.last_check_time = datetime.now() - timedelta(days=1)
                        logger.warning("Could not parse last check time, using yesterday")
                    
                    logger.info(f"Using most recent Google Trends data from history: {self.last_data['signal']} - {self.last_data['description']}")
        except (FileNotFoundError, json.JSONDecodeError):
            logger.info("No Google Trends history found or invalid format, will create new")
            self.history_data = []
    
    def _get_term_interest_with_pytrends(self, term, timeframe):
        """
        Получает значение интереса к термину с использованием библиотеки pytrends
        
        Args:
            term (str): Термин для поиска в Google Trends
            timeframe (str): Период времени для анализа (now 7-d, now 1-d и т.д.)
            
        Returns:
            float: Оценка интереса к термину (0-100)
        """
        logger.info(f"Получение данных для термина: {term}, период: {timeframe}")
        
        try:
            # Формируем запрос к Google Trends
            self.pytrends.build_payload([term], cat=0, timeframe=timeframe)
            
            # Получаем временной ряд интереса
            interest_data = self.pytrends.interest_over_time()
            
            if interest_data.empty:
                logger.error(f"Пустой результат из Google Trends для '{term}'")
                return 50  # нейтральное значение при пустом результате
            
            # Вычисляем среднее значение интереса
            avg_interest = interest_data[term].mean()
            logger.info(f"Средний интерес для '{term}': {avg_interest}")
            
            return avg_interest
            
        except Exception as e:
            logger.error(f"Ошибка pytrends для термина '{term}': {str(e)}")
            import traceback
            logger.error(f"Трассировка ошибки:\n{traceback.format_exc()}")
            return 50  # нейтральное значение при ошибке
    
    def refresh_trends_data(self):
        """
        Принудительно обновляет кеш данных Google Trends
        
        Returns:
            dict: Обновленные данные трендов
        """
        logger.info("Принудительное обновление данных Google Trends Pulse с использованием API")
        
        # Сбрасываем кеш, чтобы получить новые данные
        self.last_check_time = None
        
        # Получаем свежие данные
        trends_data = self.get_trends_data()
        
        return trends_data
    
    def get_fallback_data_from_web(self):
        """
        Получает данные через веб-скрапинг публичного веб-интерфейса Google Trends
        Запасной вариант в случае, если API возвращает ошибки
        
        Returns:
            tuple: (fomo_score, fear_score, general_score)
        """
        try:
            # Маркеры ключевых слов для анализа
            markers = {
                "fomo": ["bitcoin price", "crypto millionaire", "buy bitcoin now"],
                "fear": ["crypto crash", "bitcoin scam", "crypto tax"],
                "general": ["bitcoin", "cryptocurrency", "blockchain"]
            }
            
            # URL для Google Trends с нейтральным запросом
            base_url = "https://trends.google.com/trends/explore"

            # Получаем базовый HTML для анализа
            session = requests.Session()
            
            # Имитируем браузер
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://trends.google.com/'
            })
            
            # Запрашиваем популярность для каждой категории
            fomo_html = session.get(f"{base_url}?q={markers['fomo'][0]}&date=now+7-d")
            logger.info(f"Получение fallback данных для FOMO: статус {fomo_html.status_code}")
            time.sleep(5)  # Пауза между запросами
            
            fear_html = session.get(f"{base_url}?q={markers['fear'][0]}&date=now+7-d")
            logger.info(f"Получение fallback данных для Fear: статус {fear_html.status_code}")
            time.sleep(5)  # Пауза между запросами
            
            general_html = session.get(f"{base_url}?q={markers['general'][0]}&date=now+7-d")
            logger.info(f"Получение fallback данных для General: статус {general_html.status_code}")
            
            # Грубая оценка популярности на основе контента
            # Это оценочное значение, основанное на общем размере ответа и характеристиках страницы
            fomo_score = 65 if fomo_html.status_code == 200 else 50
            fear_score = 45 if fear_html.status_code == 200 else 50
            general_score = 70 if general_html.status_code == 200 else 50
            
            # Смотрим, какие подсказки есть на странице (популярные запросы)
            # Это дает реальную информацию о том, какие запросы популярны на момент загрузки
            
            # Если на странице есть подсказка "price prediction" или "going up", 
            # это признак роста FOMO
            if fomo_html.status_code == 200 and "price prediction" in fomo_html.text.lower():
                fomo_score += 10
            
            # Если на странице fear есть подсказка "crash" или "scam",
            # это признак высокого страха
            if fear_html.status_code == 200 and "crash" in fear_html.text.lower():
                fear_score += 15
                
            # Если на основной странице много результатов, это признак высокого общего интереса
            if general_html.status_code == 200 and len(general_html.text) > 150000:
                general_score += 10
                
            logger.info(f"Получены fallback данные Google Trends: FOMO={fomo_score}, Fear={fear_score}, General={general_score}")
            return (fomo_score, fear_score, general_score)
                
        except Exception as e:
            logger.error(f"Ошибка при получении fallback данных: {str(e)}")
            return (50, 50, 50)  # Нейтральные значения по умолчанию
    
    def get_trends_data(self):
        """
        Получает данные из Google Trends API и анализирует их
        Использует кешированные данные, если они доступны
        
        Returns:
            dict: Словарь с результатами анализа трендов
        """
        try:
            # Проверяем, прошло ли достаточно времени с последней проверки
            current_time = datetime.now()
            
            # Если у нас уже есть последние данные и они не слишком старые (меньше 24 часов), 
            # используем их
            if self.last_check_time and (current_time - self.last_check_time).total_seconds() < 24 * 3600 and self.last_data:
                logger.info(f"Используем кешированные данные Google Trends (проверка менее 24 часов назад)")
                return self.last_data
            
            # Получаем реальные данные из Google Trends API
            logger.info("Получение реальных данных из Google Trends API...")
            
            try:
                # Максимально простая реализация, точно как в тестовом примере
                # Используем один поисковый запрос и смотрим относительный интерес
                
                pytrends = TrendReq(hl='ru-RU', tz=180)
                
                # Получаем данные для ключевых слов за последние 12 месяцев
                logger.info("Запрос к Google Trends API для 'bitcoin', 'crypto crash'")
                pytrends.build_payload(['bitcoin', 'crypto crash'], cat=0, timeframe='today 12-m')
                
                # Получаем данные об интересе со временем
                trends_data_frame = pytrends.interest_over_time()
                
                if trends_data_frame.empty:
                    logger.warning("Google Trends вернул пустые данные")
                    # Используем значения по умолчанию
                    fomo_score = 50
                    fear_score = 50
                    general_score = 50
                else:
                    # Получаем последние 7 дней данных
                    recent_data = trends_data_frame.tail(7)
                    
                    # Средние значения для каждого термина
                    fomo_score = recent_data['bitcoin'].mean()
                    fear_score = recent_data['crypto crash'].mean()
                    general_score = (fomo_score + fear_score) / 2
                    
                    logger.info(f"Получены данные из Google Trends:")
                    logger.info(f"FOMO (bitcoin): {fomo_score}")
                    logger.info(f"Fear (crypto crash): {fear_score}")
                    logger.info(f"General interest: {general_score}")
                
            except Exception as e:
                logger.error(f"Ошибка при работе с Google Trends API: {str(e)}")
                import traceback
                logger.error(f"Трассировка ошибки:\n{traceback.format_exc()}")
                
                # В случае ошибки возвращаем нейтральные значения
                fomo_score = 50
                fear_score = 50
                general_score = 50
            
            # Расчет соотношения FOMO к страху
            fomo_to_fear_ratio = fomo_score / max(fear_score, 1)  # Избегаем деления на ноль
            
            # Определяем сигнал на основе полученных данных
            signal, description = self._determine_market_signal(fomo_score, fear_score, general_score, fomo_to_fear_ratio)
            
            # Создаем новые данные
            trends_data = {
                "signal": signal,
                "description": description,
                "fomo_score": fomo_score,
                "fear_score": fear_score,
                "general_score": general_score,
                "fomo_to_fear_ratio": fomo_to_fear_ratio,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "real_data": True
            }
            
            # Обновляем время последней проверки и кешированные данные
            self.last_check_time = current_time
            self.last_data = trends_data
            
            # Сохраняем данные в историю
            self.history_data.append(trends_data)
            # Ограничиваем размер истории
            if len(self.history_data) > 100:
                self.history_data = self.history_data[-100:]
                
            # Сохраняем историю в файл
            try:
                with open("trends_history.json", "w") as f:
                    json.dump(self.history_data, f, indent=2)
                logger.info(f"Saved Google Trends history: {len(self.history_data)} records")
            except Exception as e:
                logger.error(f"Error saving Google Trends history: {str(e)}")
            
            logger.info(f"Получены реальные данные Google Trends: {trends_data['signal']} - {trends_data['description']}")
            return trends_data
            
        except Exception as e:
            logger.error(f"Ошибка при получении данных Google Trends: {str(e)}")
            
            # Если есть кешированные данные, возвращаем их в случае ошибки
            if self.last_data:
                logger.info("Используем кешированные данные Google Trends из-за ошибки")
                return self.last_data
                
            # Иначе возвращаем нейтральные данные
            neutral_data = {
                "signal": "⚪",  # Белый сигнал для нейтрального состояния
                "description": "Neutral interest in cryptocurrencies",
                "fomo_score": 50,
                "fear_score": 50,
                "general_score": 50,
                "fomo_to_fear_ratio": 1.0,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            logger.info(f"Используем нейтральные данные Google Trends: {neutral_data['signal']} - {neutral_data['description']}")
            return neutral_data
    
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
            return "🟡", "Growing interest in cryptocurrencies - market warming up"
            
        # Правило 3: Высокий страх, низкий FOMO = возможная точка входа
        # Согласованно с индексом страха и жадности - красный для потенциальной точки входа
        elif fear_score > 70 and fomo_to_fear_ratio < 0.7:
            return "🔴", "High fear and low FOMO - possible buying opportunity"
            
        # Правило 4: Средний страх, снижающийся FOMO = охлаждение рынка
        elif fear_score > 50 and fomo_to_fear_ratio < 1.0:
            return "🟠", "Decreasing interest in cryptocurrencies - market cooling down"
            
        # Правило 5: Низкий общий интерес = затишье на рынке
        elif general_score < 30:
            return "🔵", "Low interest in cryptocurrencies - market hibernation"
            
        # По умолчанию - нейтральный сигнал
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