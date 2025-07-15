#!/usr/bin/env python3
"""
Исправление проблемы двойного запуска планировщика
Проблема: Flask приложение и systemd сервис оба запускают планировщик

ИНСТРУКЦИЯ ДЛЯ СЕРВЕРА:
1. Скопировать этот файл на сервер
2. Выполнить: python3 server_fix_double_scheduler.py
3. Перезапустить сервис: sudo systemctl restart coinbasebot
"""

import os
import shutil
from datetime import datetime

def fix_double_scheduler():
    """Исправляет двойной запуск планировщика в main.py"""
    
    main_file = '/root/coinbaserank_bot/main.py'
    backup_file = f'/root/coinbaserank_bot/main.py.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    print(f"Исправление двойного планировщика: {main_file}")
    
    # Создаем резервную копию
    shutil.copy2(main_file, backup_file)
    print(f"Создана резервная копия: {backup_file}")
    
    # Читаем текущий файл
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем автоматический запуск планировщика
    old_auto_start = """# Initialize scheduler at startup - for both direct run and gunicorn
scheduler_thread = threading.Thread(target=start_scheduler_thread)
scheduler_thread.daemon = True
scheduler_thread.start()
logger.info("Starting scheduler at app initialization")"""
    
    new_auto_start = """# ИСПРАВЛЕНО: НЕ запускаем планировщик автоматически из Flask приложения
# Планировщик должен запускаться только из main.py файла когда приложение запущено напрямую
# или из отдельного systemd сервиса
logger.info("Flask app initialized without starting scheduler - scheduler should be started externally")"""
    
    # Заменяем if __name__ == "__main__"
    old_main_block = """if __name__ == "__main__":
    # Run the Flask app when called directly
    app.run(host="0.0.0.0", port=5000, debug=True)"""
    
    new_main_block = """if __name__ == "__main__":
    # ИСПРАВЛЕНО: При запуске напрямую (python main.py) запускаем планировщик
    # Initialize scheduler at startup - for both direct run and gunicorn
    scheduler_thread = threading.Thread(target=start_scheduler_thread)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    logger.info("Starting scheduler at app initialization")
    
    # Run the Flask app when called directly
    app.run(host="0.0.0.0", port=5000, debug=True)"""
    
    changes_made = 0
    
    if old_auto_start in content:
        content = content.replace(old_auto_start, new_auto_start)
        changes_made += 1
        print("✅ Убран автоматический запуск планировщика при инициализации Flask")
    
    if old_main_block in content:
        content = content.replace(old_main_block, new_main_block)
        changes_made += 1
        print("✅ Исправлен блок if __name__ == '__main__'")
    
    if changes_made > 0:
        # Записываем исправленный файл
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ ИСПРАВЛЕНИЯ ВЫПОЛНЕНЫ ({changes_made} изменений)!")
        print("Flask приложение больше не будет запускать дублированный планировщик")
        print("Планировщик запускается только через systemd сервис")
        print("")
        print("Следующие шаги:")
        print("1. sudo systemctl restart coinbasebot")
        print("2. sudo systemctl status coinbasebot")
        print("3. Проверить логи: tail -f /root/coinbaserank_bot/sensortower_bot.log")
        print("4. Должна быть ТОЛЬКО ОДНА запись планировщика без ошибок блокировки")
        
    else:
        print("❌ ОШИБКА: Не найден ожидаемый код для замены")
        print("Возможно файл уже был изменен или имеет другую структуру")
        return False
    
    return True

if __name__ == "__main__":
    print("=== ИСПРАВЛЕНИЕ ДВОЙНОГО ПЛАНИРОВЩИКА ===")
    print("Проблема: Flask приложение и systemd сервис оба запускают планировщик")
    print("Решение: убрать автоматический запуск из Flask, оставить только в systemd")
    print("")
    
    success = fix_double_scheduler()
    
    if success:
        print("")
        print("=== ВАЖНО ===")
        print("После перезапуска сервиса будет запущен только ОДИН планировщик")
        print("Без ошибок 'Другой экземпляр бота уже запущен'")
        print("Завтра в 08:01 UTC (11:01 MSK) сообщение будет отправлено")
    else:
        print("Исправление не выполнено. Проверьте файл вручную.")