import time
import json
import random
import requests
import pandas as pd
from datetime import datetime, timedelta
from pytrends.request import TrendReq
import logging
from logger import logger
from proxy_google_trends import ProxyGoogleTrends

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
        self.fomo_keywords = ["bitcoin price", "crypto millionaire", "buy bitcoin"]
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
            
            # Получаем реальные данные из Google Trends API с использованием нашего прокси
            trends_logger.info("Получение реальных данных из Google Trends API...")
            
            try:
                # Создаем экземпляр ProxyGoogleTrends, который будет пробовать разные периоды и задержки
                trends_logger.debug("Создание экземпляра ProxyGoogleTrends для обхода ограничений API")
                proxy_trends = ProxyGoogleTrends()
                
                # Получаем данные для основного слова "bitcoin"
                trends_logger.info(f"Запрос к Google Trends API для 'bitcoin' с использованием разных периодов")
                
                # Получаем интерес и период, который сработал
                bitcoin_interest, used_timeframe, success = proxy_trends.get_interest_data("bitcoin", locale='en-US')
                
                # Если не удалось получить данные для bitcoin, пробуем другие ключевые слова
                if not success:
                    trends_logger.warning("Не удалось получить данные для 'bitcoin', пробуем 'cryptocurrency'")
                    crypto_interest, used_timeframe, success = proxy_trends.get_interest_data("cryptocurrency", locale='en-US')
                    
                    if not success:
                        trends_logger.warning("Не удалось получить данные и для 'cryptocurrency'")
                        
                        # Данные недоступны - не используем резервные методы, как просил пользователь
                        trends_logger.warning("Не удалось получить данные Google Trends. Резервные методы не используются.")
                        
                        # Если у нас есть предыдущие данные, возвращаем их
                        if self.last_data:
                            trends_logger.info(f"Возвращаем предыдущие данные Google Trends из-за ошибки API")
                            return self.last_data
                        
                        # Если нет предыдущих данных, возвращаем нейтральный сигнал
                        neutral_data = {
                            "signal": "⚪",
                            "description": "Neutral interest in cryptocurrencies (API unavailable)",
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
                
                # Если успешно получили данные, продолжаем обработку
                trends_logger.info(f"Успешно получены данные Google Trends для периода: {used_timeframe}")
                trends_logger.info(f"Интерес к bitcoin: {bitcoin_interest}")
                
                # Используем значение интереса к bitcoin как базовое для general_score
                general_score = bitcoin_interest
                
                # Добавляем небольшую паузу между запросами
                time.sleep(random.uniform(3.0, 5.0))
                
                # Получаем данные для FOMO запросов
                fomo_interest = 0
                fomo_successful = 0
                
                for fomo_term in self.fomo_keywords[:1]:  # Ограничиваем до 1 запроса из-за лимитов API
                    trends_logger.info(f"Запрос FOMO-данных для '{fomo_term}'")
                    term_interest, _, term_success = proxy_trends.get_interest_data(fomo_term, locale='en-US')
                    
                    if term_success:
                        fomo_interest += term_interest
                        fomo_successful += 1
                    
                    # Короткая пауза между запросами
                    time.sleep(random.uniform(2.0, 4.0))
                
                # Вычисляем среднее значение для FOMO, если есть успешные запросы
                fomo_score = fomo_interest / max(1, fomo_successful)
                
                # Получаем данные для запросов о страхе
                fear_interest = 0
                fear_successful = 0
                
                for fear_term in self.fear_keywords[:1]:  # Ограничиваем до 1 запроса из-за лимитов API
                    trends_logger.info(f"Запрос Fear-данных для '{fear_term}'")
                    term_interest, _, term_success = proxy_trends.get_interest_data(fear_term, locale='en-US')
                    
                    if term_success:
                        fear_interest += term_interest
                        fear_successful += 1
                    
                    # Короткая пауза между запросами
                    time.sleep(random.uniform(2.0, 4.0))
                
                # Вычисляем среднее значение для Fear, если есть успешные запросы
                fear_score = fear_interest / max(1, fear_successful)
                
                # Соотношение FOMO к страху (предотвращаем деление на ноль)
                fomo_to_fear_ratio = fomo_score / max(1.0, fear_score)
                
                # Выводим отладочную информацию о полученных оценках
                trends_logger.info(f"FOMO Score: {fomo_score:.1f}, Fear Score: {fear_score:.1f}, "
                                f"General Score: {general_score:.1f}, Ratio: {fomo_to_fear_ratio:.2f}")
                
                # Определяем рыночный сигнал
                signal, description = self._determine_market_signal(
                    fomo_score, fear_score, general_score, fomo_to_fear_ratio
                )
                
                # Формируем итоговый результат
                result = {
                    "signal": signal, 
                    "description": description,
                    "fomo_score": fomo_score,
                    "fear_score": fear_score,
                    "general_score": general_score,
                    "fomo_to_fear_ratio": fomo_to_fear_ratio,
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "timeframe": used_timeframe,
                    "api_available": True
                }
                
                # Обновляем кеш и время последней проверки
                self.last_data = result
                self.last_check_time = current_time
                
                # Добавляем в историю
                self.history_data.append(result)
                
                # Сохраняем обновленную историю (только последние 500 записей)
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
                
                # Данные недоступны - не используем резервные методы, как просил пользователь
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
            fomo_score (float): Оценка FOMO-запросов
            fear_score (float): Оценка запросов, связанных со страхом
            general_score (float): Оценка общих запросов о криптовалютах
            fomo_to_fear_ratio (float): Соотношение FOMO к страху
            
        Returns:
            tuple: (emoji-сигнал, текстовое описание на английском)
        """
        # Интерпретируем соотношение FOMO к страху
        if general_score < 20:
            # Очень низкий общий интерес
            return "🔵", "Market in hibernation - very low overall interest"
        elif fomo_to_fear_ratio > 1.5 and fomo_score > 60:
            # Высокий FOMO
            return "🟢", "High FOMO factor - possible market peak"
        elif fomo_to_fear_ratio < 0.7 and fear_score > 60:
            # Высокий страх
            return "🔴", "High fear and low FOMO - possible buying opportunity"
        elif general_score > 70 and fomo_score > fear_score:
            # Рост интереса и FOMO > Fear
            return "🟡", "Growing interest in cryptocurrencies - market warming up"
        elif general_score > 50 and fear_score > fomo_score:
            # Снижение интереса и Fear > FOMO
            return "🟠", "Decreasing interest in cryptocurrencies - market cooling down"
        else:
            # Нейтральный сигнал
            return "⚪", "Neutral interest in cryptocurrencies"
    
    def format_trends_message(self, trends_data=None):
        """
        Форматирует данные трендов в краткое сообщение для Telegram
        
        Args:
            trends_data (dict, optional): Данные трендов или None для получения новых данных
            
        Returns:
            str: Форматированное сообщение или None, если данные недоступны
        """
        if trends_data is None:
            trends_data = self.get_trends_data()
        
        if not trends_data:
            return None
        
        # Получаем данные
        signal = trends_data.get("signal", "⚪")
        description = trends_data.get("description", "Neutral interest in cryptocurrencies")
        fomo_score = trends_data.get("fomo_score", 0)
        fear_score = trends_data.get("fear_score", 0)
        general_score = trends_data.get("general_score", 0)
        timestamp = trends_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        api_available = trends_data.get("api_available", True)
        
        # Форматируем сообщение
        message = f"**Google Trends Pulse** {signal}\n"
        message += f"🔍 *{description}*\n\n"
        
        # Добавляем информацию о значениях, если API доступен
        if api_available and general_score > 0:
            message += f"Bitcoin Interest: {general_score:.1f}/100\n"
            
            # Добавляем оценки FOMO и страха, только если они доступны
            if fomo_score > 0 and fear_score > 0:
                message += f"FOMO Interest: {fomo_score:.1f}/100\n"
                message += f"Fear Factor: {fear_score:.1f}/100\n"
        else:
            message += "API data unavailable. Using last known signal.\n"
        
        # Добавляем время последнего обновления
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            formatted_time = dt.strftime("%b %d, %H:%M UTC")
            message += f"\nLast updated: {formatted_time}"
        except:
            message += f"\nLast updated: {timestamp}"
        
        return message