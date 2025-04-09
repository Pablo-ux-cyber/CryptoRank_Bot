import requests
import json
from datetime import datetime, timedelta
import time
from logger import logger

class GoogleTrendsPulse:
    """
    Класс для отслеживания популярности запросов в Google Trends
    Использует неофициальный API Google Trends, не требующий авторизации
    """
    def __init__(self):
        self.base_url = "https://trends.google.com/trends/api/explore"
        self.interest_over_time_url = "https://trends.google.com/trends/api/widgetdata/multiline"
        
        # Ключевые криптозапросы для отслеживания
        self.crypto_keywords = [
            "bitcoin", 
            "crypto", 
            "buy bitcoin", 
            "coinbase",
            "cryptocurrency"
        ]
        
        # Сохраняем предыдущие значения для отображения трендов
        self.previous_values = {}
        self.history_file = "/tmp/coinbasebot_trends_history.txt"
        
        # Попробуем загрузить исторические данные из файла
        try:
            import os
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    data = f.read().strip()
                    if data:
                        self.previous_values = json.loads(data)
                        logger.info(f"Загружены предыдущие данные Google Trends: {len(self.previous_values)} ключевых слов")
        except Exception as e:
            logger.error(f"Ошибка при чтении файла истории Google Trends: {str(e)}")
    
    def _get_token_and_cookies(self, keywords, timeframe='now 7-d'):
        """
        Получает токен и куки для дальнейших запросов
        
        Args:
            keywords (list): Список ключевых слов для отслеживания
            timeframe (str): Временной период ('now 1-d', 'now 7-d', 'today 3-m', 'today 12-m')
            
        Returns:
            tuple: (token, cookies) или (None, None) в случае ошибки
        """
        try:
            # Подготовка параметров запроса
            params = {
                'hl': 'en-US',
                'tz': '-180',  # GMT+3 timeframe
                'req': json.dumps({
                    'comparisonItem': [{'keyword': kw, 'geo': '', 'time': timeframe} for kw in keywords],
                    'category': 0,
                    'property': ''
                })
            }
            
            # Отправка запроса
            response = requests.get(
                self.base_url,
                params=params
            )
            
            # Проверка ответа
            if response.status_code != 200:
                logger.error(f"Ошибка запроса к Google Trends: HTTP {response.status_code}")
                return None, None
            
            # Извлечение токена
            # API возвращает ответ с префиксом ")]}'", который нужно удалить
            response_text = response.text[5:]
            response_json = json.loads(response_text)
            
            widgets = response_json.get('widgets', [])
            if not widgets:
                logger.error("В ответе Google Trends не найдены widgets")
                return None, None
            
            token = widgets[0].get('token')
            
            if not token:
                logger.error("В ответе Google Trends не найден token")
                return None, None
            
            return token, response.cookies
        
        except Exception as e:
            logger.error(f"Ошибка при получении токена Google Trends: {str(e)}")
            return None, None
    
    def _get_interest_over_time(self, token, cookies, timeframe='now 7-d'):
        """
        Получает данные о популярности запросов за указанный период
        
        Args:
            token (str): Токен, полученный из _get_token_and_cookies
            cookies (CookieJar): Куки, полученные из _get_token_and_cookies
            timeframe (str): Временной период
            
        Returns:
            dict: Данные о популярности запросов или None в случае ошибки
        """
        try:
            # Подготовка параметров запроса
            params = {
                'req': json.dumps({
                    'time': timeframe,
                    'resolution': 'HOUR', # час для коротких периодов, WEEK/DAY для длинных
                    'locale': 'en-US',
                    'comparisonItem': [{'geo': {}, 'complexKeywordsRestriction': {'keyword': [{'type': 'BROAD', 'value': kw}]}} for kw in self.crypto_keywords],
                    'requestOptions': {'property': '', 'backend': 'IZG', 'category': 0}
                }),
                'token': token,
                'tz': '-180'
            }
            
            # Отправка запроса
            response = requests.get(
                self.interest_over_time_url,
                params=params,
                cookies=cookies
            )
            
            # Проверка ответа
            if response.status_code != 200:
                logger.error(f"Ошибка запроса данных популярности: HTTP {response.status_code}")
                return None
            
            # Обработка ответа
            response_text = response.text[5:]  # Убираем префикс ")]}'"
            response_json = json.loads(response_text)
            
            # Проверка данных
            if 'default' not in response_json or 'timelineData' not in response_json['default']:
                logger.error("В ответе Google Trends отсутствуют данные timeline")
                return None
            
            # Получаем последние значения
            timeline_data = response_json['default']['timelineData']
            if not timeline_data:
                logger.warning("Google Trends вернул пустой timeline")
                return {}
            
            # Возвращаем последнее значение из временного ряда
            latest_data = timeline_data[-1]
            
            # Форматируем данные
            result = {}
            for i, kw in enumerate(self.crypto_keywords):
                if 'value' in latest_data and i < len(latest_data['value']):
                    result[kw] = int(latest_data['value'][i])
                else:
                    result[kw] = 0
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении данных популярности: {str(e)}")
            return None

    def get_trends_data(self):
        """
        Получает текущие данные о популярности криптозапросов в Google
        
        Returns:
            dict: Данные о популярности и трендах запросов или None в случае ошибки
        """
        try:
            # Получаем токен и куки
            token, cookies = self._get_token_and_cookies(self.crypto_keywords, timeframe='now 7-d')
            
            if not token or not cookies:
                logger.error("Не удалось получить токен и куки Google Trends")
                return None
            
            # Получаем данные о популярности
            trends_data = self._get_interest_over_time(token, cookies, timeframe='now 7-d')
            
            if not trends_data:
                logger.error("Не удалось получить данные о популярности запросов")
                return None
            
            # Добавляем информацию о трендах, сравнивая с предыдущими значениями
            result = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "keywords": {}
            }
            
            for kw, value in trends_data.items():
                # Готовим данные о тренде
                trend_info = {
                    "current": value,
                    "trend": "same"
                }
                
                # Если есть предыдущее значение, определяем направление тренда
                if kw in self.previous_values:
                    prev_value = self.previous_values[kw]
                    trend_info["previous"] = prev_value
                    
                    if value > prev_value:
                        trend_info["trend"] = "up"
                    elif value < prev_value:
                        trend_info["trend"] = "down"
                
                # Сохраняем значение как текущее
                self.previous_values[kw] = value
                
                # Добавляем в результат
                result["keywords"][kw] = trend_info
            
            # Сохраняем текущие значения для будущего сравнения
            try:
                with open(self.history_file, "w") as f:
                    f.write(json.dumps(self.previous_values))
                    logger.info(f"Данные Google Trends сохранены в {self.history_file}")
            except Exception as e:
                logger.error(f"Ошибка при сохранении данных Google Trends: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении данных Google Trends: {str(e)}")
            return None
    
    def format_trends_message(self, trends_data):
        """
        Форматирует данные трендов для отправки в Telegram
        
        Args:
            trends_data (dict): Данные, полученные из get_trends_data()
            
        Returns:
            str: Отформатированное сообщение для Telegram
        """
        if not trends_data or "keywords" not in trends_data:
            return "❌ Не удалось получить данные Google Trends"
        
        # Используем Markdown V2 формат для Telegram
        message = "🔍 *Google Trends Pulse*\n\n"
        
        # Добавляем дату
        date_str = trends_data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M"))
        message += f"📅 *Дата:* {date_str}\n\n"
        
        # Добавляем данные по ключевым словам
        for kw, data in trends_data["keywords"].items():
            # Форматируем ключевое слово
            kw_display = kw.capitalize()
            
            # Добавляем иконку тренда
            if "trend" in data:
                if data["trend"] == "up":
                    trend_icon = "🔼"  # Рост популярности
                elif data["trend"] == "down":
                    trend_icon = "🔽"  # Падение популярности
                else:
                    trend_icon = "➡️"  # Без изменений
            else:
                trend_icon = "🆕"  # Новое измерение, без исторических данных
            
            # Добавляем строку с данными
            current_value = data.get("current", "N/A")
            
            if "previous" in data:
                prev_value = data.get("previous")
                message += f"{trend_icon} *{kw_display}:* {current_value} \\(было: {prev_value}\\)\n"
            else:
                message += f"{trend_icon} *{kw_display}:* {current_value}\n"
            
            # Добавляем прогресс-бар
            if current_value != "N/A" and isinstance(current_value, int):
                filled_char = "🟦"  # Символ для заполненной части
                empty_char = "⬜"    # Символ для пустой части
                
                # Ограничиваем до 10 символов
                progress_length = 10
                filled_length = int((current_value / 100) * progress_length)
                filled_length = min(filled_length, progress_length)  # Не больше максимальной длины
                
                progress_bar = filled_char * filled_length + empty_char * (progress_length - filled_length)
                message += f"{progress_bar}\n"
            
            message += "\n"
        
        message += "📌 *Что это значит?*\n"
        message += "🔼 Рост интереса может сигнализировать о приближении к пику рыночных ожиданий\n"
        message += "🔽 Снижение интереса может указывать на уменьшение хайпа\n"
        
        return message

# Пример использования
if __name__ == "__main__":
    trends = GoogleTrendsPulse()
    data = trends.get_trends_data()
    if data:
        message = trends.format_trends_message(data)
        print(message)
    else:
        print("Failed to retrieve Google Trends data")