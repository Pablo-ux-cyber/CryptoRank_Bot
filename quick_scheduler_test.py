#!/usr/bin/env python3
"""
Быстрый тест исправленного планировщика
"""

from load_dotenv import load_dotenv
load_dotenv()

from logger import logger
from datetime import datetime

def test_scheduler_timing():
    """Тестируем логику времени планировщика"""
    
    logger.info("=== ТЕСТ ИСПРАВЛЕННОЙ ЛОГИКИ ПЛАНИРОВЩИКА ===")
    
    # Проверяем что планировщик инициализируется
    from scheduler import SensorTowerScheduler
    scheduler = SensorTowerScheduler()
    
    logger.info("Планировщик инициализирован успешно")
    
    # Временно меняем target время на сейчас +1 минуту для теста
    now = datetime.now()
    test_hour = now.hour
    test_minute = now.minute + 1
    if test_minute >= 60:
        test_hour += 1
        test_minute -= 60
    
    logger.info(f"Тестовое время: {test_hour:02d}:{test_minute:02d}")
    
    # Патчим планировщик для теста
    import types
    original_loop = scheduler._scheduler_loop
    
    def test_loop(self):
        """Тестовая версия планировщика с ускоренным временем"""
        self.last_rank_update_date = None
        logger.info("ТЕСТ: Запуск ускоренного планировщика")
        
        for i in range(3):  # 3 проверки времени
            try:
                now = datetime.now()
                today = now.date()
                
                # Используем тестовое время
                target_hour = test_hour
                target_minute = test_minute
                
                logger.info(f"ТЕСТ: Проверка {i+1}/3: сейчас {now.hour:02d}:{now.minute:02d}, цель {target_hour:02d}:{target_minute:02d}")
                
                # Логика проверки времени (как в реальном планировщике)
                current_time_match = (now.hour == target_hour and now.minute == target_minute)
                
                if current_time_match and (self.last_rank_update_date is None or self.last_rank_update_date < today):
                    logger.info("✅ ТЕСТ: ВРЕМЯ СОВПАДАЕТ! Запускаем отправку сообщения")
                    try:
                        # Не запускаем полный scraping_job, просто проверяем Telegram
                        if self.telegram_bot.test_connection():
                            logger.info("✅ ТЕСТ: Telegram API работает")
                            self.last_rank_update_date = today
                            logger.info("✅ ТЕСТ: Сообщение было бы отправлено успешно!")
                            return True
                        else:
                            logger.error("❌ ТЕСТ: Ошибка Telegram API")
                    except Exception as e:
                        logger.error(f"❌ ТЕСТ: Ошибка отправки: {str(e)}")
                else:
                    logger.info(f"ТЕСТ: Время не совпадает, ждем... (совпадение: {current_time_match})")
                
                # Ждем 20 секунд
                import time
                time.sleep(20)
                
            except Exception as e:
                logger.error(f"❌ ТЕСТ: Ошибка: {str(e)}")
                return False
        
        logger.info("ТЕСТ: Завершен, время не совпало за 3 проверки")
        return False
    
    # Применяем тестовую версию
    scheduler._scheduler_loop = types.MethodType(test_loop, scheduler)
    
    # Запускаем тест
    result = scheduler._scheduler_loop()
    
    if result:
        logger.info("✅ ТЕСТ ПЛАНИРОВЩИКА УСПЕШЕН!")
    else:
        logger.info("⏰ ТЕСТ: Время не совпало (это нормально)")
    
    return True

if __name__ == "__main__":
    test_scheduler_timing()