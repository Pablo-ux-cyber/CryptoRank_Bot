import time
import pandas as pd
from datetime import datetime, timedelta
from pytrends.request import TrendReq
from logger import logger

class GoogleTrendsTracker:
    def __init__(self):
        """
        Инициализирует трекер Google Trends для криптовалютных терминов
        """
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.last_request_time = None
        self.min_request_interval = 5  # Минимальный интервал между запросами в секундах (для предотвращения блокировки)
        
        # Ключевые термины для отслеживания
        self.crypto_terms = {
            "bitcoin": {"name": "Bitcoin", "icon": "₿"},
        }
        
        # Период времени для отслеживания тренда (на прошлую неделю по умолчанию)
        self.timeframe = 'now 7-d'
        
        # Геолокация (весь мир по умолчанию)
        self.geo = ''
        
        # Кеш результатов для избежания повторных запросов
        self.results_cache = {}
        self.cache_expiry = 3600  # Срок действия кеша в секундах (1 час)

    def _respect_rate_limit(self):
        """
        Соблюдает минимальный интервал между запросами к API Google Trends
        для избежания блокировки
        """
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                sleep_time = self.min_request_interval - elapsed
                logger.info(f"Ожидание {sleep_time:.2f} сек. перед следующим запросом к Google Trends...")
                time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def get_interest_over_time(self, terms=None, timeframe=None, geo=None):
        """
        Получает данные интереса к указанным терминам за указанный период времени
        
        Args:
            terms (list): Список терминов для отслеживания 
                          (если None, используются все термины из self.crypto_terms)
            timeframe (str): Период времени в формате Google Trends 
                            (если None, используется self.timeframe)
            geo (str): Код страны или '' для всего мира
                      (если None, используется self.geo)
                      
        Returns:
            dict: Словарь с данными интереса к терминам или None в случае ошибки
        """
        try:
            # Определяем параметры запроса
            if terms is None:
                terms = list(self.crypto_terms.keys())
            
            if timeframe is None:
                timeframe = self.timeframe
                
            if geo is None:
                geo = self.geo
            
            # Проверяем наличие данных в кеше
            cache_key = f"{','.join(sorted(terms))};{timeframe};{geo}"
            
            if cache_key in self.results_cache:
                cache_entry = self.results_cache[cache_key]
                
                # Проверяем, не истек ли срок действия кеша
                if time.time() - cache_entry['timestamp'] < self.cache_expiry:
                    logger.info(f"Используем кешированные данные для терминов: {', '.join(terms)}")
                    return cache_entry['data']
            
            # Соблюдаем ограничения API
            self._respect_rate_limit()
            
            # Выполняем запрос к Google Trends
            logger.info(f"Запрос данных Google Trends для терминов: {', '.join(terms)}")
            
            # Можно запрашивать не более 5 терминов за раз
            if len(terms) > 5:
                logger.warning(f"Слишком много терминов ({len(terms)}), ограничиваемся первыми 5")
                terms = terms[:5]
            
            self.pytrends.build_payload(terms, cat=0, timeframe=timeframe, geo=geo)
            data = self.pytrends.interest_over_time()
            
            if data.empty:
                logger.warning(f"Google Trends не вернул данные для терминов: {', '.join(terms)}")
                return None
            
            # Преобразуем данные в более удобный формат
            results = {
                'timeframe': timeframe,
                'geo': geo,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'terms': {},
                'raw_data': data.to_dict()
            }
            
            for term in terms:
                if term in data.columns:
                    term_data = data[term].to_dict()
                    
                    # Находим среднее, минимальное и максимальное значения
                    values = list(term_data.values())
                    avg_value = sum(values) / len(values) if values else 0
                    min_value = min(values) if values else 0
                    max_value = max(values) if values else 0
                    
                    # Определяем тренд (последнее значение выше/ниже среднего)
                    last_value = values[-1] if values else 0
                    last_date = list(term_data.keys())[-1] if term_data else None
                    
                    term_info = self.crypto_terms.get(term, {"name": term, "icon": "📊"})
                    
                    results['terms'][term] = {
                        'name': term_info['name'],
                        'icon': term_info['icon'],
                        'average': avg_value,
                        'min': min_value,
                        'max': max_value,
                        'last_value': last_value,
                        'last_date': last_date.strftime('%Y-%m-%d') if last_date else None,
                        'trend': 'up' if last_value > avg_value else 'down' if last_value < avg_value else 'stable'
                    }
            
            # Сохраняем результаты в кеш
            self.results_cache[cache_key] = {
                'timestamp': time.time(),
                'data': results
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при получении данных Google Trends: {str(e)}")
            return None

    def format_trends_message(self, trends_data):
        """
        Форматирует данные тренда в читаемое сообщение для Telegram
        
        Args:
            trends_data (dict): Данные трендов
            
        Returns:
            str: Отформатированное сообщение для Telegram
        """
        if not trends_data or 'terms' not in trends_data or not trends_data['terms']:
            return "❌ Не удалось получить данные Google Trends."
        
        # Получаем информацию о временном периоде
        timeframe = trends_data.get('timeframe', 'неизвестно')
        timeframe_display = timeframe.replace('now ', 'последние ').replace('-d', ' дней')
        
        # Получаем данные по Bitcoin
        bitcoin_data = trends_data['terms'].get('bitcoin')
        if not bitcoin_data:
            return "❌ Не удалось получить данные о Bitcoin в Google Trends."
        
        # Определяем цветовой индикатор
        value = int(bitcoin_data['last_value'])
        if value >= 70:
            level_icon = "🟢"
            level_text = "ВЫСОКИЙ"
        elif value >= 40:
            level_icon = "🟡"
            level_text = "СРЕДНИЙ"
        else:
            level_icon = "🔴"
            level_text = "НИЗКИЙ"
            
        # Определяем тренд
        trend_icon = "🔼" if bitcoin_data['trend'] == 'up' else "🔽" if bitcoin_data['trend'] == 'down' else "➡️"
        trend_text = "РАСТЁТ" if bitcoin_data['trend'] == 'up' else "ПАДАЕТ" if bitcoin_data['trend'] == 'down' else "СТАБИЛЕН"
        
        # Создаем базовый прогресс-бар
        progress_bar = self._generate_progress_bar(value, 100, 10)
        
        # Форматируем сообщение в нескольких вариантах
        
        # Вариант 1: Подробный с прогресс-баром
        message = f"📊 *BITCOIN TRENDS PULSE* ({timeframe_display})\n\n"
        message += f"₿ Интерес: {level_icon} *{value}/100* {trend_icon}\n"
        message += f"📈 Тренд: *{trend_text}*\n"
        message += f"⏱️ Относительно среднего: {trend_icon} {trend_text}\n"
        message += f"{progress_bar}\n\n"
        
        # Вариант 2: Компактный для быстрого восприятия
        compact_message = f"₿ *BITCOIN PULSE*: {level_icon}{value} {trend_icon} | {level_text} ИНТЕРЕС, {trend_text}\n"
        
        # Вариант 3: Процентное отношение к максимуму/минимуму
        avg_value = int(bitcoin_data['average'])
        min_value = int(bitcoin_data['min'])
        max_value = int(bitcoin_data['max'])
        
        pct_from_min = int(((value - min_value) / (max_value - min_value if max_value > min_value else 1)) * 100) if min_value < value else 0
        pct_from_avg = int(((value - avg_value) / avg_value if avg_value > 0 else 0) * 100)
        
        analytical_message = f"₿ *BITCOIN* ({bitcoin_data['last_date']}): {value}/100 ({pct_from_avg:+d}% от среднего)\n"
        analytical_message += f"Мин: {min_value} | Сред: {avg_value} | Макс: {max_value} | Текущий: {value} ({pct_from_min}% диапазона)\n"
        analytical_message += f"{progress_bar}\n\n"
        
        # Объединяем всё в одно сообщение
        full_message = message + "---\n" + compact_message + "\n---\n" + analytical_message
        
        return full_message

    def _generate_progress_bar(self, value, max_value, length, filled_char="█", empty_char="░"):
        """
        Генерирует визуальный прогресс-бар
        
        Args:
            value (int): Текущее значение
            max_value (int): Максимальное значение
            length (int): Длина прогресс-бара
            filled_char (str): Символ для заполненной части
            empty_char (str): Символ для пустой части
            
        Returns:
            str: Строка прогресс-бара
        """
        # Определяем цвет прогресс-бара на основе значения
        if value >= 70:
            filled_char = "🟢"  # Зеленый для высоких значений
        elif value >= 40:
            filled_char = "🟡"  # Желтый для средних значений 
        else:
            filled_char = "🔴"  # Красный для низких значений
            
        # Рассчитываем количество заполненных символов
        filled_length = int(length * (value / max_value))
        
        # Создаем прогресс-бар
        bar = filled_char * filled_length + empty_char * (length - filled_length)
        
        return bar