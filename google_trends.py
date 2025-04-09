import time
from datetime import datetime, timedelta
import pandas as pd
from pytrends.request import TrendReq
from logger import logger

class GoogleTrendsPulse:
    def __init__(self):
        """
        Инициализация модуля Google Trends Pulse для отслеживания популярности криптовалютных поисковых запросов
        """
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.crypto_keywords = [
            "Bitcoin", 
            "Ethereum", 
            "Crypto", 
            "Buy Bitcoin", 
            "Cryptocurrency"
        ]
        # Время между запросами к API Google Trends (сек) - избегаем блокировки
        self.request_delay = 1
        
    def get_trending_data(self, timeframe='now 1-d'):
        """
        Получает данные трендов для ключевых криптовалютных терминов
        
        Args:
            timeframe (str): Временной интервал в формате Google Trends 
                             (now 1-d, now 7-d, today 1-m, today 3-m, today 12-m, today 5-y)
        
        Returns:
            dict: Словарь с данными трендов и дополнительной информацией
        """
        try:
            logger.info(f"Получение данных Google Trends для {len(self.crypto_keywords)} ключевых слов")
            
            # Результаты для всех ключевых слов
            trends_data = {}
            max_values = {}
            current_values = {}
            change_pct = {}
            
            # Обрабатываем каждое ключевое слово отдельно для лучших результатов
            for keyword in self.crypto_keywords:
                logger.info(f"Проверка тренда для ключевого слова: {keyword}")
                
                # Сбрасываем параметры поиска
                self.pytrends.build_payload([keyword], cat=0, timeframe=timeframe)
                
                # Ожидание между запросами
                time.sleep(self.request_delay)
                
                # Получение данных по интересу с течением времени
                interest_over_time = self.pytrends.interest_over_time()
                
                if interest_over_time.empty:
                    logger.warning(f"Нет данных для ключевого слова {keyword}")
                    continue
                
                # Очищаем данные и берем только нужный столбец
                trend_series = interest_over_time[keyword]
                
                # Сохраняем в общий результат
                trends_data[keyword] = trend_series.tolist()
                
                # Находим максимальное значение за период
                max_values[keyword] = trend_series.max()
                
                # Текущее значение (последнее в серии)
                current_values[keyword] = trend_series.iloc[-1]
                
                # Изменение от предыдущего значения (в процентах)
                if len(trend_series) > 1:
                    previous = trend_series.iloc[-2]
                    current = trend_series.iloc[-1]
                    
                    if previous > 0:
                        pct_change = ((current - previous) / previous) * 100
                    else:
                        pct_change = 0 if current == 0 else 100
                        
                    change_pct[keyword] = round(pct_change, 2)
                else:
                    change_pct[keyword] = 0
            
            # Формируем итоговый результат
            result = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "timeframe": timeframe,
                "trends_data": trends_data,
                "max_values": max_values,
                "current_values": current_values,
                "change_pct": change_pct,
                "keywords": self.crypto_keywords
            }
            
            # Вычисляем средний интерес и изменение по всем ключевым словам
            if current_values:
                avg_interest = sum(current_values.values()) / len(current_values)
                avg_change = sum(change_pct.values()) / len(change_pct)
                
                result["average_interest"] = round(avg_interest, 2)
                result["average_change"] = round(avg_change, 2)
                
                # Определяем "пульс" тренда
                if avg_change > 50:
                    pulse_status = "Very High Activity"
                    pulse_emoji = "🔥"
                elif avg_change > 20:
                    pulse_status = "High Activity"
                    pulse_emoji = "📈"
                elif avg_change > 5:
                    pulse_status = "Moderate Growth"
                    pulse_emoji = "📊"
                elif avg_change < -20:
                    pulse_status = "Sharp Decline"
                    pulse_emoji = "📉"
                elif avg_change < -5:
                    pulse_status = "Moderate Decline"
                    pulse_emoji = "🔻"
                else:
                    pulse_status = "Stable"
                    pulse_emoji = "➡️"
                
                result["pulse_status"] = pulse_status
                result["pulse_emoji"] = pulse_emoji
            
            logger.info(f"Данные Google Trends успешно получены, средний интерес: {result.get('average_interest', 'N/A')}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении данных Google Trends: {str(e)}")
            return None
    
    def format_trends_message(self, trends_data):
        """
        Форматирует данные Google Trends для отображения в Telegram
        
        Args:
            trends_data (dict): Данные, полученные от метода get_trending_data
            
        Returns:
            str: Форматированное сообщение для Telegram
        """
        if not trends_data:
            return "❌ Не удалось получить данные Google Trends."
        
        # Основная информация
        message = f"🔍 *Google Trends Pulse*\n\n"
        
        # Добавляем "пульс" запросов
        pulse_emoji = trends_data.get("pulse_emoji", "❓")
        pulse_status = trends_data.get("pulse_status", "Unknown")
        message += f"{pulse_emoji} *Status:* {pulse_status}\n\n"
        
        # Добавляем данные по каждому ключевому слову
        message += "*Keywords Activity:*\n"
        
        current_values = trends_data.get("current_values", {})
        change_pct = trends_data.get("change_pct", {})
        
        # Сортируем ключевые слова по текущему интересу (по убыванию)
        sorted_keywords = sorted(
            current_values.keys(), 
            key=lambda k: current_values[k], 
            reverse=True
        )
        
        for keyword in sorted_keywords:
            current = current_values.get(keyword, 0)
            change = change_pct.get(keyword, 0)
            
            # Определяем emoji в зависимости от изменения
            if change > 15:
                change_emoji = "🔥"
            elif change > 5:
                change_emoji = "📈"
            elif change < -15:
                change_emoji = "📉"
            elif change < -5:
                change_emoji = "🔻"
            else:
                change_emoji = "➡️"
                
            # Оформляем с правильным форматированием для Telegram
            message += f"{change_emoji} *{keyword}*: {current}/100 "
            if change != 0:
                sign = "+" if change > 0 else ""
                message += f"({sign}{change}%)\n"
            else:
                message += "(no change)\n"
        
        # Добавляем среднее значение
        avg_interest = trends_data.get("average_interest", "N/A")
        avg_change = trends_data.get("average_change", "N/A")
        
        message += f"\n📊 *Average Interest:* {avg_interest}/100"
        if avg_change != "N/A":
            sign = "+" if avg_change > 0 else ""
            message += f" ({sign}{avg_change}%)"
            
        # Добавляем временную метку
        timestamp = trends_data.get("timestamp", "N/A")
        timeframe = trends_data.get("timeframe", "N/A")
        
        # Преобразуем timeframe в более читаемый формат
        if timeframe == "now 1-d":
            readable_timeframe = "last 24 hours"
        elif timeframe == "now 7-d":
            readable_timeframe = "last 7 days"
        elif timeframe == "today 1-m":
            readable_timeframe = "last month"
        elif timeframe == "today 3-m":
            readable_timeframe = "last 3 months"
        elif timeframe == "today 12-m":
            readable_timeframe = "last year"
        else:
            readable_timeframe = timeframe
            
        message += f"\n\n🕒 *Period:* {readable_timeframe}"
        message += f"\n🕐 *Updated:* {timestamp}"
        
        return message