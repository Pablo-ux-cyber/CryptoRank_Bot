#!/usr/bin/env python3
"""
Ручной тест планировщика для проверки работы
Запускает принудительную отправку сообщения для проверки всех компонентов
"""

import sys
import os
sys.path.append('/root/coinbaserank_bot')

from scheduler import SensorTowerScheduler
from config import TELEGRAM_TEST_CHANNEL_ID

def test_scheduler():
    """Тестирует планировщик вручную"""
    
    print("=== ТЕСТ ПЛАНИРОВЩИКА ===")
    print("Инициализация планировщика...")
    
    try:
        # Инициализируем планировщик
        scheduler = SensorTowerScheduler()
        
        print("Планировщик инициализирован успешно")
        print("Запуск принудительной отправки сообщения...")
        
        # Сохраняем оригинальный канал
        if hasattr(scheduler.telegram_bot, 'channel_id'):
            original_channel = scheduler.telegram_bot.channel_id
            
            # Временно меняем на тестовый канал
            scheduler.telegram_bot.channel_id = TELEGRAM_TEST_CHANNEL_ID
            print(f"Используем тестовый канал: {TELEGRAM_TEST_CHANNEL_ID}")
        
        # Запускаем принудительную отправку
        success = scheduler.run_now(force_send=True)
        
        # Возвращаем оригинальный канал
        if hasattr(scheduler.telegram_bot, 'channel_id'):
            scheduler.telegram_bot.channel_id = original_channel
        
        if success:
            print("✅ ТЕСТ УСПЕШЕН!")
            print("Сообщение отправлено в Telegram")
            print("Все компоненты работают корректно")
        else:
            print("❌ ТЕСТ НЕУДАЧЕН!")
            print("Сообщение не удалось отправить")
            
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТА: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scheduler()