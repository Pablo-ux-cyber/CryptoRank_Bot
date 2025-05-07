#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для очистки лишних логов и временных файлов
Может быть запущен вручную или через cron для поддержания чистоты на сервере
"""

import os
import glob
import datetime
import argparse

def clean_log_files(days_to_keep=7, log_dir='.', dry_run=False):
    """
    Очищает устаревшие лог-файлы, оставляя только самые свежие
    
    Args:
        days_to_keep (int): Количество дней, за которые сохраняются логи
        log_dir (str): Директория с лог-файлами
        dry_run (bool): Если True, только показывает что будет удалено, но не удаляет
        
    Returns:
        tuple: (int, list) - Количество удаленных файлов и список их имен
    """
    # Получаем текущую дату
    now = datetime.datetime.now()
    cutoff_date = now - datetime.timedelta(days=days_to_keep)
    
    # Шаблоны для поиска лог-файлов
    log_patterns = [
        "sensortower_bot.log.*",
        "google_trends_debug.log.*",
        "*.log.[0-9]*"  # Для логов с датой в формате timestamp
    ]
    
    removed_count = 0
    removed_files = []
    
    # Обрабатываем каждый шаблон
    for pattern in log_patterns:
        full_pattern = os.path.join(log_dir, pattern)
        for log_file in glob.glob(full_pattern):
            # Пропускаем основные лог-файлы без даты
            if log_file.endswith(".log"):
                continue
                
            # Получаем дату модификации файла
            file_stat = os.stat(log_file)
            mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
            
            # Если файл старше порогового значения, удаляем его
            if mod_time < cutoff_date:
                removed_files.append(log_file)
                print(f"Удаление устаревшего лог-файла: {log_file} (возраст: {(now - mod_time).days} дней)")
                
                if not dry_run:
                    try:
                        os.remove(log_file)
                        removed_count += 1
                    except Exception as e:
                        print(f"Ошибка при удалении {log_file}: {str(e)}")
    
    return removed_count, removed_files

def clean_temp_files(temp_patterns=None, temp_dir='.', dry_run=False):
    """
    Очищает временные файлы по заданным шаблонам
    
    Args:
        temp_patterns (list): Список шаблонов для временных файлов
        temp_dir (str): Директория с временными файлами
        dry_run (bool): Если True, только показывает что будет удалено, но не удаляет
        
    Returns:
        tuple: (int, list) - Количество удаленных файлов и список их имен
    """
    if temp_patterns is None:
        temp_patterns = [
            "*.tmp",
            "*.temp",
            "*.pyc",
            "*.pyo",
            ".DS_Store",
            "Thumbs.db"
        ]
    
    removed_count = 0
    removed_files = []
    
    # Обрабатываем каждый шаблон
    for pattern in temp_patterns:
        full_pattern = os.path.join(temp_dir, pattern)
        for temp_file in glob.glob(full_pattern):
            removed_files.append(temp_file)
            print(f"Удаление временного файла: {temp_file}")
            
            if not dry_run:
                try:
                    os.remove(temp_file)
                    removed_count += 1
                except Exception as e:
                    print(f"Ошибка при удалении {temp_file}: {str(e)}")
    
    return removed_count, removed_files

def main():
    """
    Основная функция для запуска из командной строки
    """
    parser = argparse.ArgumentParser(description='Очистка логов и временных файлов')
    parser.add_argument('--days', type=int, default=7, help='Количество дней, за которые сохранять логи')
    parser.add_argument('--log-dir', type=str, default='.', help='Директория с лог-файлами')
    parser.add_argument('--temp-dir', type=str, default='.', help='Директория с временными файлами')
    parser.add_argument('--dry-run', action='store_true', help='Только показать, что будет удалено')
    
    args = parser.parse_args()
    
    print(f"Начало очистки логов в директории {args.log_dir} (сохраняя логи за последние {args.days} дней)")
    if args.dry_run:
        print("Режим симуляции: файлы не будут удалены")
    
    # Очистка лог-файлов
    log_count, log_files = clean_log_files(
        days_to_keep=args.days,
        log_dir=args.log_dir,
        dry_run=args.dry_run
    )
    
    # Очистка временных файлов
    temp_count, temp_files = clean_temp_files(
        temp_dir=args.temp_dir,
        dry_run=args.dry_run
    )
    
    print(f"Завершено. Удалено лог-файлов: {log_count}, временных файлов: {temp_count}")
    
    return 0

if __name__ == "__main__":
    exit(main())