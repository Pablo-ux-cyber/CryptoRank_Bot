import requests
import json
from logger import logger

class TelegramBotSync:
    """
    Синхронная версия Telegram Bot для планировщика
    Использует requests вместо asyncio для избежания threading проблем
    """
    
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.api_url = f"https://api.telegram.org/bot{token}"
        
    def send_message(self, message):
        """
        Отправить сообщение в указанный канал/группу Telegram (синхронно)
        
        Args:
            message (str): Текст сообщения
            
        Returns:
            bool: True если сообщение отправлено успешно, иначе False
        """
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.channel_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            logger.info(f"ИСПРАВЛЕНИЕ: Отправка через синхронный requests в канал {self.channel_id}")
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                logger.info("ИСПРАВЛЕНИЕ: Сообщение отправлено в Telegram (sync)")
                return True
            else:
                logger.error(f"ИСПРАВЛЕНИЕ: Ошибка HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"ИСПРАВЛЕНИЕ: Ошибка отправки сообщения (sync): {str(e)}")
            return False
    
    def test_connection(self):
        """
        Тестирование соединения с Telegram API (синхронно)
        
        Returns:
            bool: True если соединение успешно, иначе False
        """
        try:
            url = f"{self.api_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    logger.info("ИСПРАВЛЕНИЕ: Соединение с Telegram API успешно (sync)")
                    return True
            
            logger.error(f"ИСПРАВЛЕНИЕ: Ошибка соединения с Telegram API (sync): {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"ИСПРАВЛЕНИЕ: Ошибка тестирования соединения (sync): {str(e)}")
            return False