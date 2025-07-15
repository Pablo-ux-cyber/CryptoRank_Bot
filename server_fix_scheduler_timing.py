#!/usr/bin/env python3
"""
Исправление проблемы с пропуском времени отправки в планировщике
Проблема: планировщик спит 5 минут и пропускает точное время 08:01 UTC

ИНСТРУКЦИЯ ДЛЯ СЕРВЕРА:
1. Скопировать этот файл на сервер
2. Выполнить: python3 server_fix_scheduler_timing.py
3. Перезапустить сервис: sudo systemctl restart coinbasebot
"""

import os
import shutil
from datetime import datetime

def fix_scheduler_timing():
    """Исправляет интервал проверки планировщика с 5 минут на 1 минуту"""
    
    scheduler_file = '/root/coinbaserank_bot/scheduler.py'
    backup_file = f'/root/coinbaserank_bot/scheduler.py.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    print(f"Исправление планировщика: {scheduler_file}")
    
    # Создаем резервную копию
    shutil.copy2(scheduler_file, backup_file)
    print(f"Создана резервная копия: {backup_file}")
    
    # Читаем текущий файл
    with open(scheduler_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем старый код планировщика на новый эффективный
    old_code_start = """        while not self.stop_event.is_set():
            try:
                # Текущее время и дата
                now = datetime.now()
                today = now.date()
                update_rank = False
                run_rnk = False"""
    
    new_scheduler_code = '''        while not self.stop_event.is_set():
            try:
                # Текущее время и дата
                now = datetime.now()
                today = now.date()
                
                # Вычисляем время до следующего запуска (08:01 UTC = 11:01 MSK)
                target_hour = 8
                target_minute = 1
                
                # Создаем целевое время на сегодня
                target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                
                # Если целевое время уже прошло сегодня, планируем на завтра
                if now >= target_time:
                    target_time = target_time.replace(day=target_time.day + 1)
                
                # Вычисляем количество секунд до целевого времени
                time_diff = (target_time - now).total_seconds()
                
                logger.info(f"Следующий запуск запланирован на: {target_time} (через {int(time_diff/3600)} часов {int((time_diff%3600)/60)} минут)")
                
                # Проверяем, не пора ли уже отправлять (если время подошло в течение последней минуты)
                if time_diff <= 60 and (self.last_rank_update_date is None or self.last_rank_update_date < today):
                    logger.info(f"ВРЕМЯ ОТПРАВКИ: Запуск полного сбора данных и отправки в {now}")
                    try:
                        self.run_scraping_job()
                        self.last_rank_update_date = today
                        logger.info(f"Данные успешно собраны и отправлены: {now}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке данных: {str(e)}")
                    
                    # После отправки спим до следующего дня
                    time_diff = 24 * 60 * 60  # 24 часа
                
                # Спим до целевого времени, но не более 1 часа за раз (для возможности остановки)
                sleep_time = min(time_diff, 3600)  # максимум 1 час
                logger.info(f"Планировщик спит {int(sleep_time/60)} минут до следующей проверки")
                
                # Спим с возможностью прерывания
                for _ in range(int(sleep_time)):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Ошибка в циле планировщика: {str(e)}")
                # При ошибке спим 5 минут перед повтором
                time.sleep(300)'''
    
    if old_code_start in content:
        # Находим начало и конец блока для замены
        start_idx = content.find(old_code_start)
        if start_idx != -1:
            # Находим конец цикла while (ищем конец отступа)
            lines = content[start_idx:].split('\n')
            end_line_idx = 0
            for i, line in enumerate(lines[1:], 1):
                if line and not line.startswith('        ') and not line.startswith('\t'):
                    end_line_idx = i
                    break
            
            if end_line_idx > 0:
                end_idx = start_idx + len('\n'.join(lines[:end_line_idx]))
                old_code = content[start_idx:end_idx]
                content = content.replace(old_code, new_scheduler_code)
        
        # Записываем исправленный файл
        with open(scheduler_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ ИСПРАВЛЕНИЕ ВЫПОЛНЕНО!")
        print("Планировщик теперь проверяет время каждую минуту вместо каждых 5 минут")
        print("Это гарантирует что время 08:01 UTC (11:01 MSK) не будет пропущено")
        print("")
        print("Следующие шаги:")
        print("1. sudo systemctl restart coinbasebot")
        print("2. sudo systemctl status coinbasebot")
        print("3. Проверить логи: tail -f /root/coinbaserank_bot/sensortower_bot.log")
        
    else:
        print("❌ ОШИБКА: Не найден ожидаемый код для замены")
        print("Возможно файл уже был изменен или имеет другую структуру")
        return False
    
    return True

if __name__ == "__main__":
    print("=== ИСПРАВЛЕНИЕ ПЛАНИРОВЩИКА ===")
    print("Проблема: планировщик спит 5 минут и пропускает время 08:01 UTC")
    print("Решение: изменить интервал проверки на 1 минуту")
    print("")
    
    success = fix_scheduler_timing()
    
    if success:
        print("")
        print("=== ВАЖНО ===")
        print("После перезапуска сервиса планировщик будет проверять время каждую минуту")
        print("Завтра в 08:01 UTC (11:01 MSK) сообщение должно быть отправлено")
    else:
        print("Исправление не выполнено. Проверьте файл вручную.")