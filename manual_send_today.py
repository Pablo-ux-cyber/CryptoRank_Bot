#!/usr/bin/env python3
"""
Ручной запуск отправки сегодняшних данных в Telegram
Используется когда автоматический планировщик пропустил время отправки
"""

import sys
import os
import logging
from datetime import datetime

# Добавляем текущую директорию в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram_bot import TelegramBot
from scraper import SensorTowerScraper  
from fear_greed_index import FearGreedIndexTracker
from altcoin_season_index import AltcoinSeasonIndex
from market_breadth_indicator import MarketBreadthIndicator

def main():
    """Ручное получение и отправка всех данных"""
    
    print("=== РУЧНАЯ ОТПРАВКА ДАННЫХ В TELEGRAM ===")
    print(f"Время запуска: {datetime.now()}")
    
    try:
        # Инициализация всех модулей
        telegram_bot = TelegramBot()
        scraper = SensorTowerScraper()
        fear_greed_tracker = FearGreedIndexTracker()
        altcoin_season_index = AltcoinSeasonIndex()
        market_breadth = MarketBreadthIndicator()
        
        print("✅ Все модули инициализированы")
        
        # Сбор всех данных
        print("\n--- Сбор данных ---")
        
        # 1. Рейтинг Coinbase
        print("📱 Получение рейтинга Coinbase...")
        rank = scraper.get_rank()
        print(f"   Рейтинг: {rank}")
        
        # 2. Fear & Greed Index
        print("😨 Получение Fear & Greed Index...")
        fear_greed_data = fear_greed_tracker.get_fear_greed_index()
        print(f"   Индекс: {fear_greed_data}")
        
        # 3. Altcoin Season Index
        print("🪙 Получение Altcoin Season Index...")
        altseason_data = altcoin_season_index.get_altseason_index()
        print(f"   Альткоин сезон: {altseason_data}")
        
        # 4. Market Breadth Indicator
        print("📊 Анализ Market Breadth (может занять 3-4 минуты)...")
        market_data = market_breadth.get_market_breadth_data()
        print(f"   Market Breadth: {market_data}")
        
        print("\n--- Формирование сообщения ---")
        
        # Формирование единого сообщения
        message_parts = []
        
        # Рейтинг Coinbase
        if rank:
            message_parts.append(f"📱 Coinbase AppRank: #{rank}")
        
        # Fear & Greed Index
        if fear_greed_data:
            fear_greed_message = fear_greed_tracker.format_fear_greed_message(fear_greed_data)
            if fear_greed_message:
                message_parts.append(fear_greed_message)
        
        # Altcoin Season Index  
        if altseason_data:
            altseason_message = altcoin_season_index.format_altseason_message(altseason_data)
            if altseason_message:
                message_parts.append(altseason_message)
                
        # Market Breadth Indicator
        if market_data:
            market_message = market_breadth.format_simple_telegram_message(market_data)
            if market_message:
                message_parts.append(market_message)
        
        # Отправка сообщения
        if message_parts:
            final_message = "\\n".join(message_parts)
            print(f"\\n--- Отправка в Telegram ---")
            print(f"Сообщение:\\n{final_message}")
            
            success = telegram_bot.send_message(final_message)
            
            if success:
                print("✅ Сообщение успешно отправлено в Telegram!")
            else:
                print("❌ Ошибка отправки сообщения в Telegram")
                return 1
        else:
            print("❌ Нет данных для отправки")
            return 1
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\\n🎉 Ручная отправка завершена успешно!")
    return 0

if __name__ == "__main__":
    sys.exit(main())