#!/usr/bin/env python3
"""
Быстрый тест отправки сообщения в Telegram без лишних данных
"""

from load_dotenv import load_dotenv
load_dotenv()

from logger import logger
from telegram_bot_sync import TelegramBotSync
from json_rank_reader import get_rank_from_json
from fear_greed_index import FearGreedIndexTracker
from altcoin_season_index import AltcoinSeasonIndex

def quick_telegram_test():
    logger.info("=== БЫСТРЫЙ ТЕСТ TELEGRAM ===")
    
    try:
        # 1. Telegram API
        import os
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
        
        if not token or not channel_id:
            logger.error("❌ Нет токена или channel_id в .env")
            return False
            
        telegram_bot = TelegramBotSync(token, channel_id)
        if not telegram_bot.test_connection():
            logger.error("❌ Telegram API не работает")
            return False
        logger.info("✅ Telegram API работает")
        
        # 2. Данные рейтинга из JSON
        rank = get_rank_from_json()
        logger.info(f"✅ Рейтинг: {rank}")
        
        # 3. Fear & Greed Index
        fear_greed_tracker = FearGreedIndexTracker()
        fear_greed_data = fear_greed_tracker.get_fear_greed_index()
        logger.info(f"✅ Fear & Greed: {fear_greed_data['value']}")
        
        # 4. Altcoin Season
        altseason_tracker = AltcoinSeasonIndex()
        altseason_data = altseason_tracker.get_altseason_index()
        logger.info(f"✅ Altcoin Season: {altseason_data['index_value']*100:.1f}%")
        
        # 5. Формируем простое сообщение БЕЗ MARKET BREADTH
        message = f"""📊 Daily Market Report
        
🏪 Coinbase Rank: #{rank}
😱 Fear & Greed: {fear_greed_data['value']} ({fear_greed_data['classification']})
🔄 Altcoin Season: {altseason_data['signal']} {altseason_data['index']*100:.1f}% ({altseason_data['status']})

⏰ {fear_greed_data['last_update']}"""
        
        # 6. Отправляем сообщение
        logger.info("Отправляем простое сообщение...")
        success = telegram_bot.send_message_sync(message)
        
        if success:
            logger.info("✅ СООБЩЕНИЕ ОТПРАВЛЕНО В TELEGRAM!")
            return True
        else:
            logger.error("❌ Ошибка отправки в Telegram")
            return False
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    quick_telegram_test()