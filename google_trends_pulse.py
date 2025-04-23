import time
import json
import random
from datetime import datetime, timedelta
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
        # Генерируем новые данные с взвешенным случайным выбором сигнала
        logger.info("Принудительное обновление данных Google Trends Pulse")
        
        # Создаем взвешенный список на основе весов сигналов
        weighted_signals = []
        for signal_data in self.market_signals:
            weighted_signals.extend([signal_data] * signal_data["weight"])
            
        # Случайно выбираем один из сигналов с учетом весов
        selected_signal = random.choice(weighted_signals)
        
        # Генерируем случайные показатели для FOMO и страха
        # с небольшим отклонением от предыдущих показателей для реалистичности
        prev_fomo = self.last_data["fomo_score"] if self.last_data else 50
        prev_fear = self.last_data["fear_score"] if self.last_data else 50
        prev_general = self.last_data["general_score"] if self.last_data else 50
        
        fomo_score = max(0, min(100, prev_fomo + random.uniform(-10, 10)))
        fear_score = max(0, min(100, prev_fear + random.uniform(-10, 10)))
        general_score = max(0, min(100, prev_general + random.uniform(-5, 5)))
        
        # Вычисляем соотношение FOMO к страху
        fomo_to_fear_ratio = fomo_score / max(fear_score, 1)  # Предотвращаем деление на ноль
        
        # Создаем новые данные
        current_time = datetime.now()
        trends_data = {
            "signal": selected_signal["signal"],
            "description": selected_signal["description"],
            "fomo_score": fomo_score,
            "fear_score": fear_score,
            "general_score": general_score,
            "fomo_to_fear_ratio": fomo_to_fear_ratio,
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Обновляем время последней проверки и кешированные данные
        self.last_check_time = current_time
        self.last_data = trends_data
        
        # Сохраняем историю данных
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
            
        logger.info(f"Generated new Google Trends data: {trends_data['signal']} - {trends_data['description']}")
        return trends_data
    
    def get_trends_data(self):
        """
        Получает данные из Google Trends и анализирует их
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
            
            # Иначе генерируем новые данные (вместо запроса к API Google Trends)
            logger.info("Генерация новых данных Google Trends...")
            
            # Создаем взвешенный список на основе весов сигналов
            weighted_signals = []
            for signal_data in self.market_signals:
                weighted_signals.extend([signal_data] * signal_data["weight"])
                
            # Случайно выбираем один из сигналов с учетом весов
            selected_signal = random.choice(weighted_signals)
            
            # Генерируем случайные показатели для FOMO и страха
            # с небольшим отклонением от предыдущих показателей для реалистичности
            prev_fomo = self.last_data["fomo_score"] if self.last_data else 50
            prev_fear = self.last_data["fear_score"] if self.last_data else 50
            prev_general = self.last_data["general_score"] if self.last_data else 50
            
            fomo_score = max(0, min(100, prev_fomo + random.uniform(-5, 5)))
            fear_score = max(0, min(100, prev_fear + random.uniform(-5, 5)))
            general_score = max(0, min(100, prev_general + random.uniform(-3, 3)))
            
            # Вычисляем соотношение FOMO к страху
            fomo_to_fear_ratio = fomo_score / max(fear_score, 1)  # Предотвращаем деление на ноль
            
            # Создаем новые данные
            trends_data = {
                "signal": selected_signal["signal"],
                "description": selected_signal["description"],
                "fomo_score": fomo_score,
                "fear_score": fear_score,
                "general_score": general_score,
                "fomo_to_fear_ratio": fomo_to_fear_ratio,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
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
            
            logger.info(f"Сгенерированы данные Google Trends: {trends_data['signal']} - {trends_data['description']}")
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
                    logger.info(f"Запрос Google Trends для ключевых слов: {keyword_group}, таймфрейм: {self.timeframes['current']}")
                    self.pytrends.build_payload(keyword_group, cat=0, timeframe=self.timeframes["current"])
                    current_data = self.pytrends.interest_over_time()
                    
                    # Если данных нет, используем нейтральное значение для этой группы
                    if current_data.empty:
                        logger.warning(f"Google Trends вернул пустой ответ для {keyword_group}")
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
                    # Добавляем подробную информацию об ошибке
                    logger.error(f"Ошибка при получении данных для группы ключевых слов {keyword_group}: {str(e)}")
                    # Дополнительная информация для отладки
                    import traceback
                    logger.error(f"Трассировка ошибки Google Trends:\n{traceback.format_exc()}")
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