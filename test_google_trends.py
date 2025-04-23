#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестирование модуля Google Trends Pulse

Этот скрипт предназначен для тестирования функциональности Google Trends Pulse
в изолированном режиме. Запустите его отдельно от основного приложения
для отладки и проверки работы модуля.

Использование:
    python test_google_trends.py

Инструмент создаст отдельный лог-файл google_trends_debug.log с подробной
информацией о процессе запросов и обработки данных.
"""

import sys
import time
import json
from datetime import datetime
import argparse

# Импортируем модуль Google Trends Pulse
from google_trends_pulse import GoogleTrendsPulse, trends_logger

def print_header(text):
    """Выводит заголовок текста"""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80)
    
def print_data(data, title=None):
    """Выводит словарь данных в читаемом формате"""
    if title:
        print(f"\n{title}:")
    
    for key, value in data.items():
        print(f"  {key}: {value}")

def main():
    """Основная функция тестирования"""
    parser = argparse.ArgumentParser(description="Тестирование Google Trends Pulse")
    parser.add_argument("--force", "-f", action="store_true", 
                       help="Принудительно обновить данные из Google Trends")
    parser.add_argument("--delay", "-d", type=int, default=5,
                       help="Задержка между запросами (в секундах)")
    parser.add_argument("--repeat", "-r", type=int, default=1, 
                       help="Количество тестовых запросов")
    args = parser.parse_args()
    
    print_header("Тестирование Google Trends Pulse")
    print(f"Дата и время: {datetime.now()}")
    print(f"Режим: {'Принудительное обновление' if args.force else 'Стандартный'}")
    print(f"Повторы: {args.repeat}, задержка: {args.delay} сек")
    
    try:
        # Инициализируем модуль Google Trends Pulse
        trends_pulse = GoogleTrendsPulse()
        print("\nМодуль Google Trends Pulse успешно инициализирован")
        
        # Имеющиеся кешированные данные
        if trends_pulse.last_data:
            print_header("Кешированные данные")
            print_data(trends_pulse.last_data)
            print(f"Время последней проверки: {trends_pulse.last_check_time}")
            print(f"Возраст данных: {(datetime.now() - trends_pulse.last_check_time).total_seconds() / 3600:.2f} часов")
        else:
            print("\nКешированные данные отсутствуют")
        
        # Тестовые запросы
        for i in range(args.repeat):
            if i > 0:
                print(f"\nЗадержка {args.delay} секунд перед следующим запросом...")
                time.sleep(args.delay)
                
            print_header(f"Тестовый запрос #{i+1}")
            print(f"Время запроса: {datetime.now()}")
            
            # Получаем данные Google Trends, принудительно обновляя если нужно
            start_time = time.time()
            try:
                data = trends_pulse.get_trends_data(force_refresh=args.force)
                elapsed = time.time() - start_time
                
                print(f"Запрос выполнен за {elapsed:.2f} секунд")
                print_data(data, "Полученные данные")
                
                # Также выводим отформатированное сообщение 
                message = trends_pulse.format_trends_message(data)
                print(f"\nСообщение для Telegram: {message}")
                
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"ОШИБКА ({elapsed:.2f} сек): {str(e)}")
        
        print_header("Тестирование завершено")
        print("Проверьте файл google_trends_debug.log для более подробной информации")
        
    except Exception as e:
        print(f"\nОШИБКА: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())