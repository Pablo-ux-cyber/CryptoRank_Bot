#!/usr/bin/env python3
"""
Тест отправки сообщений БЕЗ Market Breadth анализа
"""

from load_dotenv import load_dotenv
load_dotenv()

from logger import logger
from telegram_bot_sync import TelegramBotSync
from json_rank_reader import get_rank_from_json, get_latest_rank_date
from fear_greed_index import FearGreedIndexTracker

def test_send_simple_message():
    """Отправляем простое сообщение без Market Breadth"""
    
    logger.info("=== ТЕСТ ПРОСТОГО СООБЩЕНИЯ ===")
    
    try:
        # Telegram bot с правильными параметрами
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
        telegram_bot = TelegramBotSync(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID)
        
        # Проверяем соединение
        if not telegram_bot.test_connection():
            logger.error("Ошибка соединения с Telegram")
            return False
        
        logger.info("Telegram соединение успешно")
        
        # Получаем рейтинг из JSON
        current_rank = get_rank_from_json()
        current_date = get_latest_rank_date()
        
        logger.info(f"Рейтинг: {current_rank} на дату {current_date}")
        
        # Получаем Fear & Greed
        fear_greed_tracker = FearGreedIndexTracker()
        fear_greed_data = fear_greed_tracker.get_fear_greed_index()
        
        if fear_greed_data:
            logger.info(f"Fear & Greed: {fear_greed_data['value']} ({fear_greed_data['classification']})")
        
        # Создаем сообщение
        message = f"📱 Coinbase: #{current_rank}"
        
        if fear_greed_data:
            fear_greed_message = fear_greed_tracker.format_fear_greed_message(fear_greed_data)
            message += f"\n\n{fear_greed_message}"
        
        # Отправляем
        logger.info(f"Отправляем сообщение: {message}")
        
        success = telegram_bot.send_message(message)
        
        if success:
            logger.info("✅ СООБЩЕНИЕ ОТПРАВЛЕНО УСПЕШНО!")
            return True
        else:
            logger.error("❌ ОШИБКА ОТПРАВКИ СООБЩЕНИЯ")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка в тесте: {str(e)}")
        return False

if __name__ == "__main__":
    test_send_simple_message()