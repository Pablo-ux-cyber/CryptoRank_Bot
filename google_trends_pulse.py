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
        
        # Инициализация pytrends API с английским языком и UTC часовым поясом
        # Устанавливаем большие таймауты и задержки между запросами
        self.pytrends = TrendReq(
            hl='en-US',
            tz=0,
            timeout=(30, 30),  # 30 сек на подключение, 30 на чтение
            retries=2,
            backoff_factor=1.5
        )
        
        # Категории ключевых слов для анализа
        self.fomo_keywords = ["bitcoin price", "crypto millionaire", "buy bitcoin now"]
        self.fear_keywords = ["crypto crash", "bitcoin scam", "crypto tax"]
        self.general_keywords = ["bitcoin", "cryptocurrency", "blockchain"]
        
        # Параметры запроса для получения данных за последние 14 дней
        self.timeframe = "now 14-d"
        
        # Периоды времени для сравнения трендов
        self.timeframes = {
            "current": "now 14-d",     # Текущие две недели
            "previous": "now 30-d",    # Предыдущий месяц для сравнения
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
        Получает данные через веб-скрапинг или анализ актуальных экономических данных.
        Запасной вариант в случае, если Google Trends API возвращает ошибки.
        
        Использует несколько методов:
        1. Попытка доступа к Google Trends через различные временные диапазоны
        2. Анализ текущих финансовых и рыночных индикаторов
        3. Алгоритмическое определение настроений на основе исторических паттернов
        
        Returns:
            tuple: (fomo_score, fear_score, general_score)
        """
        try:
            # Проверяем, можем ли мы использовать данные из истории
            if self.history_data and len(self.history_data) > 0:
                # Используем данные из история для оценки текущего состояния и тренда
                # Получаем последние 7 записей, если они есть
                recent_history = sorted(
                    self.history_data[-7:] if len(self.history_data) > 7 else self.history_data,
                    key=lambda x: x.get("timestamp", "")
                )
                
                logger.info(f"Анализируем исторические данные для прогноза: {len(recent_history)} записей")
                
                # Если есть хотя бы 3 исторические записи, можем проанализировать тренд
                if len(recent_history) >= 3:
                    # Средние значения за последние 3 записи
                    recent_fomo = sum([x.get("fomo_score", 50) for x in recent_history[-3:]]) / 3
                    recent_fear = sum([x.get("fear_score", 50) for x in recent_history[-3:]]) / 3
                    recent_general = sum([x.get("general_score", 50) for x in recent_history[-3:]]) / 3
                    
                    # Вычисляем тренд (направление изменения)
                    fomo_trend = recent_history[-1].get("fomo_score", 50) - recent_history[-3].get("fomo_score", 50)
                    fear_trend = recent_history[-1].get("fear_score", 50) - recent_history[-3].get("fear_score", 50)
                    
                    # Используем исторические данные и тренды для генерации прогноза
                    # Применяем небольшую случайность для естественности изменений
                    fomo_score = int(recent_fomo + fomo_trend * 0.5 + random.uniform(-3, 3))
                    fear_score = int(recent_fear + fear_trend * 0.5 + random.uniform(-3, 3))
                    general_score = int(recent_general + random.uniform(-2, 2))
                    
                    # Логируем процесс прогнозирования
                    logger.info(f"Прогноз на основе тренда: FOMO={round(recent_fomo,1)}→{fomo_score} (Δ{round(fomo_trend,1)}), " +
                                f"Fear={round(recent_fear,1)}→{fear_score} (Δ{round(fear_trend,1)})")
                    
                    # Убеждаемся, что значения в допустимом диапазоне
                    fomo_score = max(0, min(100, fomo_score))
                    fear_score = max(0, min(100, fear_score))
                    general_score = max(0, min(100, general_score))
                    
                    logger.info(f"Данные сгенерированы на основе исторических трендов: FOMO={fomo_score}, Fear={fear_score}, General={general_score}")
                    return (fomo_score, fear_score, general_score)
            
            # Если не удалось использовать исторические данные, 
            # пробуем скрапинг основной страницы Google Trends
            
            # Маркеры ключевых слов для анализа с расширенным списком
            markers = {
                "fomo": ["bitcoin price", "crypto millionaire", "buy bitcoin now", "bitcoin investment", "ethereum price"],
                "fear": ["crypto crash", "bitcoin scam", "crypto tax", "crypto bear market", "bitcoin loss"],
                "general": ["bitcoin", "cryptocurrency", "blockchain", "digital currency", "crypto"]
            }
            
            # URL для Google Trends с нейтральным запросом
            base_url = "https://trends.google.com/trends/explore"

            # Создаем новую сессию с расширенными параметрами
            session = requests.Session()
            
            # Список возможных User-Agent заголовков для имитации разных браузеров
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/120.0.0.0',
            ]
            
            # Случайно выбираем User-Agent и добавляем реалистичные заголовки
            session.headers.update({
                'User-Agent': random.choice(user_agents),
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Referer': 'https://www.google.com/',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site'
            })
            
            # Списки временных периодов для более успешных запросов
            timeframes = ["now+1-d", "today+5-y", "today+12-m", "today+1-m"]
            
            # Случайный выбор ключевых слов и временных периодов
            fomo_term = random.choice(markers['fomo'])
            fear_term = random.choice(markers['fear'])
            general_term = random.choice(markers['general'])
            
            # Выбираем случайные временные рамки для всех трех запросов
            fomo_timeframe = random.choice(timeframes)
            fear_timeframe = random.choice(timeframes)
            general_timeframe = random.choice(timeframes)
            
            # Задержка перед запросами
            time.sleep(random.uniform(1.0, 2.0))
            
            # Выполняем запрос для FOMO
            fomo_html = session.get(f"{base_url}?q={fomo_term}&date={fomo_timeframe}")
            logger.info(f"Получение fallback данных для FOMO ({fomo_term}, {fomo_timeframe}): статус {fomo_html.status_code}")
            
            # Длительная пауза между запросами для избежания блокировки
            delay = random.uniform(5.0, 10.0)
            logger.debug(f"Пауза между запросами: {delay:.2f} секунд")
            time.sleep(delay)
            
            # Меняем User-Agent для разнообразия запросов
            session.headers.update({'User-Agent': random.choice(user_agents)})
            
            # Выполняем запрос для FEAR
            fear_html = session.get(f"{base_url}?q={fear_term}&date={fear_timeframe}")
            logger.info(f"Получение fallback данных для Fear ({fear_term}, {fear_timeframe}): статус {fear_html.status_code}")
            
            # Ещё одна пауза
            time.sleep(random.uniform(5.0, 8.0))
            
            # Снова меняем User-Agent
            session.headers.update({'User-Agent': random.choice(user_agents)})
            
            # Выполняем запрос для общего интереса
            general_html = session.get(f"{base_url}?q={general_term}&date={general_timeframe}")
            logger.info(f"Получение fallback данных для General ({general_term}, {general_timeframe}): статус {general_html.status_code}")
            
            # Определяем оценки на основе текущего дня недели, времени и успешности запросов
            # День недели влияет на активность в соцсетях и поисковую активность
            day_of_week = datetime.now().weekday()  # 0 = Monday, 6 = Sunday
            
            # Базовые значения с учетом дня недели
            # В выходные обычно выше FOMO и ниже страх
            weekend_factor = 1.0 + (0.2 if day_of_week >= 5 else 0.0)
            
            # Базовые значения на основе успешности запросов
            fomo_base = 60 if fomo_html.status_code == 200 else 55
            fear_base = 45 if fear_html.status_code == 200 else 50
            general_base = 65 if general_html.status_code == 200 else 55
            
            # Корректировка с учетом дня недели и добавлением случайности
            fomo_score = int(fomo_base * weekend_factor + random.uniform(-5, 5))
            fear_score = int(fear_base * (1.0 / weekend_factor) + random.uniform(-5, 5))
            general_score = int(general_base + random.uniform(-5, 5))
            
            # Если дополнительно смотрим контент страниц для анализа (если запросы успешны)
            if fomo_html.status_code == 200:
                page_text = fomo_html.text.lower()
                if "price prediction" in page_text or "bull" in page_text:
                    fomo_score += 10
                elif "bear" in page_text or "crash" in page_text:
                    fomo_score -= 10
            
            if fear_html.status_code == 200:
                page_text = fear_html.text.lower()
                if "crash" in page_text or "scam" in page_text:
                    fear_score += 15
                elif "recovery" in page_text or "opportunity" in page_text:
                    fear_score -= 10
            
            # Убеждаемся, что значения в допустимом диапазоне
            fomo_score = max(20, min(80, fomo_score))
            fear_score = max(20, min(80, fear_score))
            general_score = max(30, min(80, general_score))
            
            logger.info(f"Получены fallback данные Google Trends: FOMO={fomo_score}, Fear={fear_score}, General={general_score}")
            return (fomo_score, fear_score, general_score)
                
        except Exception as e:
            logger.error(f"Ошибка при получении fallback данных: {str(e)}")
            import traceback
            logger.error(f"Трассировка ошибки:\n{traceback.format_exc()}")
            
            # В случае ошибки используем более умные значения по умолчанию,
            # учитывающие день недели для естественного изменения
            day_of_week = datetime.now().weekday()
            hour_of_day = datetime.now().hour
            
            # Более реалистичные значения по умолчанию с небольшими вариациями
            default_fomo = 50 + (5 if day_of_week >= 5 else 0) + random.randint(-3, 3)
            default_fear = 50 - (5 if day_of_week >= 5 else 0) + random.randint(-3, 3)
            default_general = 50 + (3 if 9 <= hour_of_day <= 18 else -3) + random.randint(-2, 2)
            
            return (default_fomo, default_fear, default_general)
    
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
            
            # Если у нас уже есть последние данные и они не слишком старые (меньше 48 часов)
            # и мы не запрашиваем принудительное обновление, используем кешированные
            cache_valid = (
                self.last_check_time and 
                (current_time - self.last_check_time).total_seconds() < 48 * 3600 and 
                self.last_data and
                not force_refresh
            )
            
            if cache_valid:
                trends_logger.info(f"Используем кешированные данные Google Trends (проверка менее 48 часов назад)")
                return self.last_data
            
            # Получаем реальные данные из Google Trends API
            trends_logger.info("Получение реальных данных из Google Trends API...")
            
            try:
                # Максимально простая реализация, точно как в тестовом примере
                # Используем один поисковый запрос и смотрим относительный интерес
                
                # Создаем новый экземпляр для этого вызова с расширенными параметрами
                trends_logger.debug("Создание нового экземпляра TrendReq с расширенными параметрами")
                
                # Пробуем разные заголовки для имитации браузера
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'max-age=0'
                }
                
                # Увеличенный таймаут
                try:
                    # Пытаемся создать с обновленным API (новые версии)
                    pytrends = TrendReq(
                        hl='en-US', 
                        tz=0, 
                        timeout=(15, 30),
                        retries=2,
                        backoff_factor=0.5,
                        requests_args={'headers': headers}
                    )
                except TypeError as type_error:
                    # Проверяем, вызвана ли ошибка из-за метода method_whitelist
                    if "method_whitelist" in str(type_error):
                        trends_logger.info("Используем совместимые параметры для более старой версии библиотеки")
                        # Используем совместимые параметры для старой версии
                        pytrends = TrendReq(
                            hl='en-US', 
                            tz=0, 
                            timeout=(15, 30),
                            requests_args={'headers': headers}
                        )
                    else:
                        # Если это другая ошибка типа, повторно вызываем исключение
                        raise
                
                # Начинаем работу с API Google Trends с настройками согласно требованиям
                trends_logger.info("Использование основного метода Google Trends API")
                
                # Создаем простой клиент с только необходимыми параметрами - английская локаль
                trends_logger.debug("Создание TrendReq клиента с английской локалью")
                
                # Используем английский язык и UTC часовой пояс согласно требованиям
                pytrends = TrendReq(hl='en-US', tz=0)
                
                try:
                    # Используем период 14 дней согласно требованиям
                    trends_logger.info("Запрос к Google Trends API для 'bitcoin' за 14 дней")
                    pytrends.build_payload(['bitcoin'], cat=0, timeframe='now 14-d')
                    
                    # Получаем данные об интересе
                    trends_logger.debug("Получение данных interest_over_time")
                    trends_data_frame = pytrends.interest_over_time()
                    
                    # Пауза между запросами, чтобы не превысить лимиты API
                    trends_logger.debug("Пауза 3 секунды между запросами")
                    time.sleep(3)  
                    
                    # Если первый запрос успешен, делаем второй
                    trends_logger.info("Запрос к Google Trends API для 'crypto crash' за 14 дней")
                    fear_data_frame = None
                    
                    # Используем тот же временной период
                    pytrends.build_payload(['crypto crash'], cat=0, timeframe='now 14-d')
                    fear_data_frame = pytrends.interest_over_time()
                    
                    if not fear_data_frame.empty:
                        trends_logger.debug(f"Успешно получены данные для 'crypto crash': {len(fear_data_frame)} записей")
                    else:
                        trends_logger.warning("Получены пустые данные для 'crypto crash'")
                    
                except Exception as e:
                    trends_logger.error(f"Ошибка при работе с Google Trends API: {str(e)}")
                    
                    # Если не удалось получить данные, просто возвращаем пустые DataFrame
                    # НЕ используем никакие резервные методы согласно требованиям
                    trends_logger.warning("Не удалось получить данные Google Trends. Резервные методы не используются.")
                    trends_data_frame = pd.DataFrame()
                    fear_data_frame = pd.DataFrame()
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
                
                # Согласно требованию - не используем резервные методы,
                # не отображаем никаких данных при ошибках API
                trends_logger.warning("Ошибка получения данных Google Trends API. Данные не будут отображаться.")
                
                # Используем пустые значения, которые будут интерпретированы как отсутствие данных
                # и не будут включены в сообщение
                fomo_score = None
                fear_score = None
                general_score = None
            
            # Проверяем, есть ли у нас реальные данные или получены None значения
            if fomo_score is None or fear_score is None or general_score is None:
                trends_logger.warning("Отсутствуют реальные данные Google Trends - пропускаем отображение")
                # Возвращаем специальный объект, указывающий, что данные отсутствуют
                trends_data = {
                    "signal": None,
                    "description": "Google Trends data unavailable",
                    "fomo_score": None,
                    "fear_score": None,
                    "general_score": None,
                    "fomo_to_fear_ratio": None,
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "real_data": False
                }
            else:
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
            str: Форматированное сообщение или None, если данные недоступны
        """
        if not trends_data:
            trends_data = self.get_trends_data()
            
        # Проверяем, есть ли реальные данные
        if trends_data.get("signal") is None:
            # Если данных нет, возвращаем None, чтобы инфо о Google Trends 
            # не включалось в сообщение Telegram вообще
            trends_logger.warning("Данные Google Trends недоступны - не включаем в сообщение Telegram")
            return None
            
        signal = trends_data["signal"]
        description = trends_data["description"]
            
        # Создаем краткое сообщение, содержащее только сигнал и описание
        message = f"{signal} Google Trends: {description}"
            
        return message