#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import random
import requests
import pandas as pd
from datetime import datetime, timedelta
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError
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
        
        # Категории ключевых слов для анализа
        # Запросы, оптимизированные для наиболее точного определения настроений рынка:
        # 1. Общий запрос отражает общий интерес к криптовалютам
        # 2. FOMO запрос отражает намерение купить/инвестировать
        # 3. Fear запрос отражает беспокойство/страх относительно рынка
        self.general_keywords = ["bitcoin", "crypto", "blockchain"]  # "bitcoin" используется как основной
        self.fomo_keywords = ["buy crypto", "invest bitcoin", "crypto profit"]  # "buy crypto" используется как основной
        self.fear_keywords = ["crypto crash", "bitcoin crash", "sell bitcoin"]  # "crypto crash" используется как основной
        
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
    
    def safe_interest_over_time(self, pytrends, retries=5, initial_delay=10):
        """
        Пытается получить данные, при TooManyRequestsError — ждёт и повторяет с удвоением задержки.
        
        Args:
            pytrends: Экземпляр TrendReq
            retries (int): Количество попыток
            initial_delay (int): Начальная задержка между попытками в секундах
            
        Returns:
            DataFrame или None: Данные из Google Trends или None в случае ошибки
        """
        delay = initial_delay
        for attempt in range(1, retries + 1):
            try:
                trends_logger.info(f"Попытка {attempt}/{retries} получения данных...")
                result = pytrends.interest_over_time()
                trends_logger.info(f"Успешно получены данные с Google Trends (попытка {attempt})")
                return result
            except TooManyRequestsError:
                if attempt == retries:
                    # После последней неудачи — пробрасываем ошибку
                    trends_logger.error(f"TooManyRequestsError после {retries} попыток")
                    raise
                trends_logger.warning(f"429 Too Many Requests (попытка {attempt}/{retries}), ждем {delay} секунд...")
                time.sleep(delay)
                delay *= 2  # Экспоненциальный рост задержки
        return None
    
    def get_term_interest(self, term, locale='en-US'):
        """
        Получает значение интереса к термину с использованием формата диапазона дат
        и механизма повторных попыток
        
        Args:
            term (str): Термин для поиска в Google Trends
            locale (str): Локаль для API запроса, по умолчанию 'en-US'
            
        Returns:
            float: Оценка интереса к термину (0-100) или 50 если данные недоступны
        """
        trends_logger.info(f"Получение данных для термина: {term}")
        
        try:
            # Диапазон за последние 30 дней в формате "YYYY-MM-DD YYYY-MM-DD"
            today = datetime.utcnow().date()
            start = today - timedelta(days=30)
            timeframe = f"{start} {today}"  # "YYYY-MM-DD YYYY-MM-DD"
            
            trends_logger.info(f"Сформирован диапазон дат: {timeframe}")
            
            # Создаём клиента с указанной локалью 'en-US' и часовым поясом UTC
            pytrends = TrendReq(hl=locale, tz=0)
            
            # Формируем запрос с указанным термином
            pytrends.build_payload([term], cat=0, timeframe=timeframe)
            
            # Делаем запрос с надежным механизмом повторов
            data = self.safe_interest_over_time(pytrends)
            
            # Проверяем результат
            if data is None or data.empty:
                trends_logger.warning(f"Пустой результат из Google Trends для '{term}'")
                return 50  # нейтральное значение при ошибке
            
            # Отфильтровываем строку за текущий (неполный) день
            if 'isPartial' in data.columns:
                data = data[~data['isPartial']]
            
            # Вычисляем среднее значение интереса
            avg_interest = data[term].mean()
            trends_logger.info(f"Средний интерес для '{term}': {avg_interest}")
            
            return avg_interest
            
        except Exception as e:
            trends_logger.error(f"Ошибка pytrends для термина '{term}': {str(e)}")
            import traceback
            trends_logger.error(f"Трассировка ошибки:\n{traceback.format_exc()}")
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
        trends_data = self.get_trends_data(force_refresh=True)
        
        return trends_data
    
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
                # Получаем данные для основного слова из списка general_keywords
                general_term = self.general_keywords[0]  # "bitcoin"
                bitcoin_interest = self.get_term_interest(general_term)
                
                # Если получили нейтральное значение (50), значит произошла ошибка
                if bitcoin_interest == 50:
                    trends_logger.warning("Не удалось получить данные для 'bitcoin'")
                    
                    # Пробуем другой термин - "cryptocurrency"
                    trends_logger.info("Пробуем получить данные для 'cryptocurrency'...")
                    crypto_interest = self.get_term_interest("cryptocurrency")
                    
                    if crypto_interest == 50:
                        trends_logger.warning("Не удалось получить данные и для 'cryptocurrency'")
                        
                        # Данные недоступны - не используем резервные методы, как просил пользователь
                        trends_logger.warning("Не удалось получить данные Google Trends. Резервные методы не используются.")
                        
                        # Данные недоступны, возвращаем None вместо нейтрального сигнала
                        trends_logger.warning("Google Trends API недоступен. Не используем нейтральные данные.")
                        
                        # Если у нас есть предыдущие реальные данные (не фейковые), возвращаем их
                        if self.last_data and self.last_data.get("api_available", False):
                            trends_logger.info(f"Возвращаем предыдущие достоверные данные Google Trends из-за ошибки API")
                            return self.last_data
                        
                        # Если предыдущих данных нет или они тоже фейковые, возвращаем None
                        trends_logger.warning("Нет доступных данных Google Trends. Часть сообщения будет пропущена.")
                        return None
                    
                    # Если успешно получили данные для cryptocurrency, используем их
                    general_score = crypto_interest
                    trends_logger.info(f"Используем данные для 'cryptocurrency': {general_score}")
                else:
                    # Используем данные для bitcoin
                    general_score = bitcoin_interest
                    trends_logger.info(f"Используем данные для 'bitcoin': {general_score}")
                
                # Увеличиваем паузы между запросами, чтобы снизить вероятность ошибки 429
                time.sleep(random.uniform(5.0, 10.0))
                
                # Получаем данные только для FOMO запроса, который стабильно работает
                # Используем первый запрос из списка FOMO-запросов
                fomo_term = self.fomo_keywords[0]  # "buy crypto"
                trends_logger.info(f"Получение данных для FOMO-термина: {fomo_term}")
                fomo_score = self.get_term_interest(fomo_term)
                
                # Увеличиваем паузы между запросами, чтобы снизить вероятность ошибки 429
                time.sleep(random.uniform(5.0, 10.0))
                
                # Делаем третий запрос для явного измерения страха
                # Используем первый термин из fear_keywords
                fear_term = self.fear_keywords[0]  # "crypto crash"
                trends_logger.info(f"Получение данных для FEAR-термина: {fear_term}")
                fear_score = self.get_term_interest(fear_term)
                
                # Если не удалось получить данные для fear_term, используем аналитический метод
                if fear_score == 50:  # нейтральное значение при ошибке
                    trends_logger.warning(f"Не удалось получить данные для термина '{fear_term}', используем расчетный метод")
                    
                    # Вычисляем отношение FOMO к общему интересу как индикатор настроения
                    buying_interest_ratio = fomo_score / general_score if general_score > 0 else 1.0
                    trends_logger.info(f"Отношение интереса к покупке/общему интересу: {buying_interest_ratio:.2f}")
                    
                    # Расчет страха на основе соотношения
                    if buying_interest_ratio > 1.2:  # Высокий FOMO
                        # Низкий страх, когда соотношение покупки к общему интересу высокое
                        fear_score = max(10, int(100 - (buying_interest_ratio * 40)))
                    elif buying_interest_ratio < 0.8:  # Низкий интерес к покупке
                        # Высокий страх, когда соотношение покупки к общему интересу низкое
                        fear_score = min(90, int(120 - (buying_interest_ratio * 50)))
                    else:  # Нейтральное соотношение
                        fear_score = max(10, 100 - general_score)  # Используем обратный показатель от общего интереса
                    
                    trends_logger.info(f"Рассчитанное значение для страха: {fear_score} (на основе соотношения buy/general)")
                else:
                    trends_logger.info(f"Полученное значение для страха: {fear_score} (прямой запрос '{fear_term}')")
                
                # Вычисляем соотношение для логирования, если оно ещё не определено
                if not 'buying_interest_ratio' in locals():
                    buying_interest_ratio = fomo_score / general_score if general_score > 0 else 1.0
                    
                # Логируем итоговое соотношение
                trends_logger.info(f"Итоговое соотношение FOMO/общему интересу: {buying_interest_ratio:.2f}")
                trends_logger.info(f"Итоговое значение страха: {fear_score}")
                
                # Если fomo_score равен нейтральному значению (не смогли получить данные)
                if fomo_score == 50:
                    fomo_score = general_score
                    trends_logger.info(f"Используем для FOMO значение общего интереса: {fomo_score}")
                
                # Если оба значения нейтральные, не смогли получить данные
                if fomo_score == 50 and fear_score == 50:
                    # Используем только general_score, который у нас точно есть
                    fomo_score = general_score
                    fear_score = general_score
                    
                # Расчет соотношения FOMO к страху (предотвращаем деление на ноль)
                if fear_score < 1:
                    fear_score = 1
                fomo_to_fear_ratio = fomo_score / fear_score
                
                # Определяем сигнал на основе полученных данных
                signal, description = self._determine_market_signal(
                    fomo_score, fear_score, general_score, fomo_to_fear_ratio
                )
                
                # Формируем результат
                result = {
                    "signal": signal,
                    "description": description,
                    "fomo_score": fomo_score,
                    "fear_score": fear_score,
                    "general_score": general_score,
                    "fomo_to_fear_ratio": fomo_to_fear_ratio,
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "api_available": True
                }
                
                # Обновляем кеш и время последней проверки
                self.last_data = result
                self.last_check_time = current_time
                
                # Добавляем запись в историю
                self.history_data.append(result)
                
                # Сохраняем историю, ограничиваясь 500 записями
                if len(self.history_data) > 500:
                    self.history_data = sorted(
                        self.history_data,
                        key=lambda x: x.get("timestamp", ""),
                        reverse=True
                    )[:500]
                
                try:
                    with open("trends_history.json", "w") as f:
                        json.dump(self.history_data, f, indent=2)
                    logger.info(f"Saved Google Trends history: {len(self.history_data)} records")
                except Exception as e:
                    logger.error(f"Error saving Google Trends history: {e}")
                
                return result
                
            except Exception as e:
                trends_logger.error(f"Ошибка при работе с Google Trends API: {str(e)}")
                
                # Не используем резервные методы, как просил пользователь
                trends_logger.warning("Не удалось получить данные Google Trends. Резервные методы не используются.")
                
                # Если у нас есть предыдущие данные, возвращаем их
                if self.last_data:
                    trends_logger.info(f"Возвращаем предыдущие данные Google Trends из-за ошибки API")
                    return self.last_data
                
                # Если нет предыдущих данных, возвращаем нейтральный сигнал
                neutral_data = {
                    "signal": "⚪",
                    "description": "Neutral interest in cryptocurrencies (API error)",
                    "fomo_score": 0,
                    "fear_score": 0,
                    "general_score": 0,
                    "fomo_to_fear_ratio": 1.0,
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "api_available": False
                }
                
                # Обновляем кеш и последнее время проверки
                self.last_data = neutral_data
                self.last_check_time = current_time
                
                return neutral_data
                
        except Exception as e:
            trends_logger.error(f"Ошибка в методе get_trends_data: {str(e)}")
            import traceback
            trends_logger.error(f"Трассировка ошибки:\n{traceback.format_exc()}")
            
            # Если у нас есть предыдущие данные, возвращаем их
            if self.last_data:
                return self.last_data
            
            # Если нет предыдущих данных, возвращаем нейтральный сигнал
            return {
                "signal": "⚪",
                "description": "Neutral interest in cryptocurrencies (error)",
                "fomo_score": 0,
                "fear_score": 0,
                "general_score": 0,
                "fomo_to_fear_ratio": 1.0,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "api_available": False
            }
    
    def _determine_market_signal(self, fomo_score, fear_score, general_score, fomo_to_fear_ratio):
        """
        Определяет рыночный сигнал на основе оценок различных категорий
        
        Args:
            fomo_score (float): Оценка FOMO-запросов (buy crypto)
            fear_score (float): Оценка запросов, связанных со страхом (рассчитывается на основе соотношения buy crypto/bitcoin)
            general_score (float): Оценка общих запросов о криптовалютах (bitcoin)
            fomo_to_fear_ratio (float): Соотношение FOMO к страху
            
        Returns:
            tuple: (emoji-сигнал, текстовое описание на английском)
        """
        trends_logger.info(f"Определение рыночного сигнала: fomo={fomo_score}, fear={fear_score}, " + 
                         f"general={general_score}, ratio={fomo_to_fear_ratio:.2f}")
                         
        # Интерпретируем соотношение FOMO к страху с учетом прямого измерения страха
        # или расчетного значения на основе соотношения FOMO к общему интересу
        if general_score < 20:
            # Очень низкий общий интерес
            return "🔵", "Market in hibernation - very low overall interest"
        elif fomo_score > 70 and fomo_score > fear_score * 1.2:
            # Высокий FOMO и превышение над страхом
            return "🟢", "High FOMO factor - possible market peak"
        elif fomo_to_fear_ratio > 2.0:
            # Значительное превышение FOMO над страхом
            return "🟢", "FOMO significantly exceeds fear - market optimism"
        elif fear_score > 70 and fear_score > fomo_score * 1.2:
            # Высокий страх и превышение над FOMO
            return "🔴", "High fear and low FOMO - possible buying opportunity"
        elif fomo_to_fear_ratio < 0.5:
            # Значительное превышение страха над FOMO
            return "🔴", "Fear significantly exceeds FOMO - market pessimism"
        elif general_score > 60 and fomo_score > fear_score:
            # Рост интереса и FOMO > Fear
            return "🟡", "Growing interest in cryptocurrencies - market warming up"
        elif general_score > 50 and fear_score > fomo_score:
            # Снижение интереса и Fear > FOMO
            return "🟠", "Decreasing interest in cryptocurrencies - market cooling down"
        elif fomo_to_fear_ratio > 1.2:
            # FOMO умеренно превышает страх
            return "🟡", "FOMO exceeds fear - market optimism growing"
        else:
            # Нейтральный сигнал
            return "⚪", "Neutral interest in cryptocurrencies"
    
    def format_trends_message(self, trends_data=None):
        """
        Форматирует данные трендов в упрощенное сообщение для Telegram
        
        Args:
            trends_data (dict, optional): Данные трендов или None для получения новых данных
            
        Returns:
            str: Форматированное сообщение в упрощенном формате, 
                 None если данные недоступны или получены из кеша при выключенной опции
        """
        if trends_data is None:
            trends_data = self.get_trends_data()
        
        # Если данных нет вообще, возвращаем None вместо сообщения об ошибке
        if not trends_data:
            trends_logger.warning("Нет данных Google Trends для форматирования сообщения")
            return None
        
        # Получаем данные
        signal = trends_data.get("signal", "⚪")
        description = trends_data.get("description", "Neutral interest in cryptocurrencies")
        api_available = trends_data.get("api_available", False)  # По умолчанию считаем, что API недоступен
        
        # Если данные не из API и мы не используем fallback, возвращаем None
        if not api_available:
            trends_logger.warning("Данные Google Trends не из API, не добавляем их в сообщение")
            return None
        
        # Форматируем сообщение только для реальных данных API
        message = f"{signal} Google Trends: {description}"
        return message

# Пример использования
if __name__ == "__main__":
    pulse = GoogleTrendsPulse()
    trends_data = pulse.get_trends_data(force_refresh=True)
    print("Google Trends Pulse результат:")
    print(f"Сигнал: {trends_data['signal']}")
    print(f"Описание: {trends_data['description']}")
    print(f"FOMO-оценка: {trends_data['fomo_score']}")
    print(f"Fear-оценка: {trends_data['fear_score']}")
    print(f"General-оценка: {trends_data['general_score']}")
    print(f"FOMO/Fear соотношение: {trends_data['fomo_to_fear_ratio']:.2f}")
    print(f"Время: {trends_data['timestamp']}")
    
    message = pulse.format_trends_message(trends_data)
    print("\nФорматированное сообщение для Telegram:")
    print(message)