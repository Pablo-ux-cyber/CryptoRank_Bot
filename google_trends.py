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
            "buy crypto": {"name": "Buy Crypto", "icon": "💰"},
            "coinbase": {"name": "Coinbase", "icon": "🟦"},
            "crypto wallet": {"name": "Crypto Wallet", "icon": "👛"},
            "ethereum": {"name": "Ethereum", "icon": "Ξ"},
            "nft": {"name": "NFT", "icon": "🖼️"}
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
        if not trends_data or 'terms' not in trends_data:
            return "❌ Не удалось получить данные Google Trends."
        
        # Получаем информацию о временном периоде
        timeframe = trends_data.get('timeframe', 'неизвестно')
        timeframe_display = timeframe.replace('now ', 'последние ').replace('-d', ' дней')
        
        # Форматируем сообщение с заголовком
        message = f"📈 *Google Trends Pulse* ({timeframe_display})\n\n"
        
        # Сортируем термины по убыванию текущего значения
        sorted_terms = sorted(
            trends_data['terms'].items(),
            key=lambda x: x[1]['last_value'],
            reverse=True
        )
        
        # Добавляем информацию о каждом термине
        for term, data in sorted_terms:
            trend_icon = "🔼" if data['trend'] == 'up' else "🔽" if data['trend'] == 'down' else "➡️"
            
            # Форматируем значения в процентах от максимума (100)
            last_value = int(data['last_value'])
            
            # Создаем графическое представление прогресса
            progress_bar = self._generate_progress_bar(last_value, 100, 5)
            
            message += f"{data['icon']} *{data['name']}*: {trend_icon} {last_value}/100\n"
            message += f"{progress_bar}\n"
        
        return message

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