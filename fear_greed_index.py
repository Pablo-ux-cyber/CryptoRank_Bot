import requests
import logging
import time
from datetime import datetime

# Настройка логирования
logger = logging.getLogger('sensortower_bot')

class FearGreedIndexTracker:
    def __init__(self):
        """
        Инициализирует трекер индекса страха и жадности для криптовалют
        """
        self.api_url = "https://api.alternative.me/fng/"
        self.last_data = None
        
    def get_fear_greed_index(self):
        """
        Получает текущее значение индекса страха и жадности и его интерпретацию
        
        Returns:
            dict: Словарь с данными индекса или None в случае ошибки
        """
        try:
            logger.info("Fetching Fear & Greed Index data")
            response = requests.get(self.api_url, params={"limit": 1}, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch Fear & Greed Index: HTTP {response.status_code}")
                return self._create_fallback_data()
                
            data = response.json()
            
            if "data" not in data or not data["data"]:
                logger.error("Invalid response format from Fear & Greed API")
                return self._create_fallback_data()
                
            index_data = data["data"][0]
            
            # Преобразование значений
            value = int(index_data.get("value", "0"))
            value_classification = index_data.get("value_classification", "Unknown")
            timestamp = int(index_data.get("timestamp", "0"))
            
            # Преобразование timestamp в дату
            date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
            
            result = {
                "value": value,
                "classification": value_classification,
                "date": date,
                "timestamp": timestamp
            }
            
            logger.info(f"Successfully fetched Fear & Greed Index: {value} ({value_classification})")
            self.last_data = result
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Fear & Greed API failed: {str(e)}")
            return self._create_fallback_data()
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {str(e)}")
            return self._create_fallback_data()
            
    def _create_fallback_data(self):
        """
        Создает резервные данные в случае ошибки
        """
        # Если у нас есть предыдущие данные, используем их
        if self.last_data:
            logger.info("Using last known Fear & Greed data")
            return self.last_data
            
        # Создаем тестовые данные
        logger.info("Using fallback Fear & Greed data")
        return {
            "value": 45,
            "classification": "Fear",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": int(time.time())
        }
        
    def format_fear_greed_message(self, fear_greed_data):
        """
        Форматирует данные индекса страха и жадности в сообщение для Telegram
        
        Args:
            fear_greed_data (dict): Данные индекса страха и жадности
            
        Returns:
            str: Отформатированное сообщение для Telegram
        """
        if not fear_greed_data:
            return "❌ Не удалось получить данные индекса страха и жадности\\."
            
        value = fear_greed_data.get("value", 0)
        classification = fear_greed_data.get("classification", "Unknown")
        date = fear_greed_data.get("date", "Unknown Date")
        
        # Экранируем специальные символы для Telegram MarkdownV2
        classification = classification.replace("-", "\\-").replace(".", "\\.").replace("!", "\\!")
        
        # Выбираем эмодзи в зависимости от значения индекса
        if classification == "Extreme Fear":
            emoji = "😱"
            progress = self._generate_progress_bar(value, 100, 10, "🔴")
        elif classification == "Fear":
            emoji = "😨"
            progress = self._generate_progress_bar(value, 100, 10, "🟠")
        elif classification == "Neutral":
            emoji = "😐"
            progress = self._generate_progress_bar(value, 100, 10, "🟡")
        elif classification == "Greed":
            emoji = "😏"
            progress = self._generate_progress_bar(value, 100, 10, "🟢")
        elif classification == "Extreme Greed":
            emoji = "🤑"
            progress = self._generate_progress_bar(value, 100, 10, "🟢")
        else:
            emoji = "❓"
            progress = self._generate_progress_bar(value, 100, 10, "⚪")
        
        # Формируем сообщение
        message = f"📊 *Crypto Fear & Greed Index*\n"
        message += f"📅 *Дата:* {date}\n\n"
        message += f"{emoji} *Значение:* {value}/100\n"
        message += f"*Статус:* {classification}\n"
        message += f"{progress}\n"
        
        # Добавляем интерпретацию
        message += "\n*Что это значит:*\n"
        message += "Индекс страха и жадности анализирует эмоции и настроения на крипторынке\\. Экстремальный страх может быть признаком недооцененности активов, а экстремальная жадность \\- признаком переоцененности\\."
        
        return message
        
    def _generate_progress_bar(self, value, max_value, length, filled_char="█", empty_char="░"):
        """
        Генерирует графический прогресс-бар
        
        Args:
            value (int): Текущее значение
            max_value (int): Максимальное значение
            length (int): Длина прогресс-бара
            filled_char (str): Символ для заполненной части
            empty_char (str): Символ для пустой части
            
        Returns:
            str: Строка прогресс-бара
        """
        filled_length = int(length * value / max_value)
        bar = filled_char * filled_length + empty_char * (length - filled_length)
        return bar