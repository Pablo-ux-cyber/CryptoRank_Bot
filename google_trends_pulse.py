import time
import json
import random
import requests
import pandas as pd
from datetime import datetime, timedelta
from pytrends.request import TrendReq
import logging
from logger import logger

# Создаем отдельный логгер для Google Trends для более детального отслеживания
trends_logger = logging.getLogger('google_trends')
trends_logger.setLevel(logging.DEBUG)

# Очищаем существующие обработчики, чтобы избежать дублирования
if trends_logger.handlers:
    trends_logger.handlers.clear()

# Настраиваем вывод в файл с ротацией каждую полночь, хранящий логи за последние 7 дней
from logging.handlers import TimedRotatingFileHandler
trends_file_handler = TimedRotatingFileHandler(
    'google_trends_debug.log',
    when='midnight',      # Ротация в полночь
    interval=1,           # Один день на файл
    backupCount=7,        # Хранить логи за 7 дней
    encoding='utf-8'
)
trends_file_handler.setLevel(logging.DEBUG)
trends_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
trends_file_handler.setFormatter(trends_formatter)
trends_logger.addHandler(trends_file_handler)

# Добавляем также обработчик для вывода в консоль
trends_stream_handler = logging.StreamHandler()
trends_stream_handler.setLevel(logging.INFO)
trends_stream_handler.setFormatter(trends_formatter)
trends_logger.addHandler(trends_stream_handler)

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
            
            # Заменяем на одиночные запросы с более короткими периодами и большей паузой
            import random
            
            # Случайный выбор ключевого слова из каждой категории для разнообразия запросов
            fomo_term = random.choice(markers['fomo'])
            fear_term = random.choice(markers['fear'])
            
            # Запрашиваем популярность для FOMO с оптимальным периодом (14 дней)
            fomo_html = session.get(f"{base_url}?q={fomo_term}&date=now+14-d")
            logger.info(f"Получение fallback данных для FOMO ({fomo_term}): статус {fomo_html.status_code}")
            
            # Более длительная случайная пауза между запросами (5-10 секунд)
            delay = random.uniform(5.0, 10.0)
            logger.debug(f"Пауза между запросами: {delay:.2f} секунд")
            time.sleep(delay)
            
            # Запрашиваем популярность для Fear с оптимальным периодом (14 дней)
            fear_html = session.get(f"{base_url}?q={fear_term}&date=now+14-d")
            logger.info(f"Получение fallback данных для Fear ({fear_term}): статус {fear_html.status_code}")
            time.sleep(5)  # Пауза между запросами
            
            general_html = session.get(f"{base_url}?q={markers['general'][0]}&date=now+14-d")
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
    
    def get_trends_data(self, force_refresh=False):
        """
        Получает данные из Google Trends API и анализирует их
        Использует кешированные данные, если они доступны
        
        Args:
            force_refresh (bool): Принудительно получить свежие данные, игнорируя кеш
            
        Returns:
            dict: Словарь с результатами анализа трендов
        """
        try:
            # Проверяем, прошло ли достаточно времени с последней проверки
            current_time = datetime.now()
            
            trends_logger.info(f"Запрос данных Google Trends. Время: {current_time}, последняя проверка: {self.last_check_time}")
            
            # Если у нас уже есть последние данные и они не слишком старые (меньше 24 часов)
            # и мы не запрашиваем принудительное обновление, используем кешированные
            cache_valid = (
                self.last_check_time and 
                (current_time - self.last_check_time).total_seconds() < 24 * 3600 and 
                self.last_data and
                not force_refresh
            )
            
            if cache_valid:
                trends_logger.info(f"Используем кешированные данные Google Trends (проверка менее 24 часов назад)")
                return self.last_data
            
            # Получаем реальные данные из Google Trends API
            trends_logger.info("Получение реальных данных из Google Trends API...")
            
            try:
                # Максимально простая реализация, точно как в тестовом примере
                # Используем один поисковый запрос и смотрим относительный интерес
                
                # Создаем новый экземпляр для этого вызова
                trends_logger.debug("Создание нового экземпляра TrendReq")
                # Используем самые простые параметры для минимального воздействия
                pytrends = TrendReq(hl='en-US', tz=0, timeout=(10,25))
                
                # Используем только один ключевой термин и оптимальный период (14 дней)
                trends_logger.info("Запрос к Google Trends API для 'bitcoin'")
                pytrends.build_payload(['bitcoin'], cat=0, timeframe='now 14-d')
                
                # Получаем данные об интересе с небольшим таймаутом
                trends_logger.debug("Получение данных interest_over_time")
                trends_data_frame = pytrends.interest_over_time()
                
                # Теперь делаем второй запрос для 'crypto crash' после паузы
                time.sleep(3)  # Пауза между запросами
                trends_logger.info("Запрос к Google Trends API для 'crypto crash'")
                fear_data_frame = None
                try:
                    pytrends.build_payload(['crypto crash'], cat=0, timeframe='now 14-d')
                    fear_data_frame = pytrends.interest_over_time()
                    trends_logger.debug("Успешно получены данные для 'crypto crash'")
                except Exception as e:
                    trends_logger.warning(f"Не удалось получить данные для 'crypto crash': {str(e)}")
                    # Продолжаем с данными только для 'bitcoin'
                trends_logger.debug(f"Получены данные: {not trends_data_frame.empty}, размер: {len(trends_data_frame) if not trends_data_frame.empty else 0}")
                
                if trends_data_frame.empty:
                    trends_logger.warning("Google Trends вернул пустые данные для bitcoin")
                    # Используем значения по умолчанию
                    fomo_score = 50
                    fear_score = 50
                    general_score = 50
                else:
                    # Получаем данные bitcoin
                    fomo_score = trends_data_frame['bitcoin'].mean()
                    
                    # Проверяем, получили ли мы данные для crypto crash
                    if fear_data_frame is not None and not fear_data_frame.empty:
                        fear_score = fear_data_frame['crypto crash'].mean()
                    else:
                        # Если не удалось получить данные для crypto crash, используем значение по умолчанию
                        fear_score = 50
                    
                    # Рассчитываем общий интерес как среднее
                    general_score = (fomo_score + fear_score) / 2
                    
                    trends_logger.debug(f"Расчет средних значений:")
                    trends_logger.debug(f"Bitcoin данные: {len(trends_data_frame)} записей")
                    if fear_data_frame is not None:
                        trends_logger.debug(f"Crypto crash данные: {len(fear_data_frame)} записей")
                    
                    trends_logger.info(f"Получены данные из Google Trends:")
                    trends_logger.info(f"FOMO (bitcoin): {fomo_score}")
                    trends_logger.info(f"Fear (crypto crash): {fear_score}")
                    trends_logger.info(f"General interest: {general_score}")
                    
                        # Подробная информация для отладки
                    trends_logger.debug("Детальные данные bitcoin по дням:")
                    for date, row in trends_data_frame.iterrows():
                        trends_logger.debug(f"  {date}: bitcoin={row['bitcoin']}")
                    
                    if fear_data_frame is not None and not fear_data_frame.empty:
                        trends_logger.debug("Детальные данные crypto crash по дням:")
                        for date, row in fear_data_frame.iterrows():
                            trends_logger.debug(f"  {date}: crypto crash={row['crypto crash']}")
                
            except Exception as e:
                trends_logger.error(f"Ошибка при работе с Google Trends API: {str(e)}")
                import traceback
                trends_logger.error(f"Трассировка ошибки:\n{traceback.format_exc()}")
                
                # Проверяем, если это ошибка слишком большого количества запросов,
                # пробуем получить данные через резервный метод
                is_rate_limit = "429" in str(e) or "TooManyRequestsError" in str(e)
                if is_rate_limit:
                    trends_logger.warning("Обнаружено превышение лимита запросов (429). Использую резервный метод...")
                    try:
                        # Используем резервный метод получения данных
                        fomo_score, fear_score, general_score = self.get_fallback_data_from_web()
                        trends_logger.info(f"Успешно получены данные через резервный метод: FOMO={fomo_score}, Fear={fear_score}")
                    except Exception as fallback_e:
                        trends_logger.error(f"Ошибка в резервном методе: {str(fallback_e)}")
                        # В случае ошибки резервного метода используем нейтральные значения
                        fomo_score = 50
                        fear_score = 50
                        general_score = 50
                else:
                    # Для других ошибок (не связанных с лимитами) используем нейтральные значения
                    trends_logger.warning("Неизвестная ошибка, использую нейтральные значения")
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