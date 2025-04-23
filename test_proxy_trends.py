#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест для проверки работы ProxyGoogleTrends
Запускает проверку нескольких ключевых слов и выводит результаты
"""

import time
import logging
import argparse
from proxy_google_trends import ProxyGoogleTrends

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('test_proxy')

def test_keywords(keywords, locale='en-US'):
    """
    Тестирует получение данных об интересе к нескольким ключевым словам
    
    Args:
        keywords (list): Список ключевых слов для тестирования
        locale (str): Локаль для анализа
    
    Returns:
        dict: Словарь с результатами для каждого ключевого слова
    """
    proxy = ProxyGoogleTrends()
    results = {}
    
    for keyword in keywords:
        logger.info(f"Тестирование ключевого слова: {keyword}")
        
        try:
            interest, period, success = proxy.get_interest_data(keyword, locale)
            
            results[keyword] = {
                'interest': interest,
                'period': period,
                'success': success
            }
            
            logger.info(f"Результат для {keyword}: интерес={interest}, период={period}, успех={success}")
            
            # Задержка между запросами разных ключевых слов
            if keyword != keywords[-1]:
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"Ошибка при тестировании {keyword}: {str(e)}")
            results[keyword] = {
                'interest': 0,
                'period': None,
                'success': False,
                'error': str(e)
            }
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Тест ProxyGoogleTrends')
    parser.add_argument('--keywords', nargs='+', default=['bitcoin', 'ethereum', 'crypto'],
                        help='Ключевые слова для тестирования')
    parser.add_argument('--locale', default='en-US',
                        help='Локаль для анализа (например, en-US, ru-RU)')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("ТЕСТИРОВАНИЕ PROXY GOOGLE TRENDS")
    logger.info("=" * 60)
    
    if not args.keywords:
        logger.warning("Не указаны ключевые слова для тестирования")
        return 1
    
    logger.info(f"Тестирование {len(args.keywords)} ключевых слов: {', '.join(args.keywords)}")
    logger.info(f"Используемая локаль: {args.locale}")
    
    results = test_keywords(args.keywords, args.locale)
    
    logger.info("=" * 60)
    logger.info("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    logger.info("=" * 60)
    
    success_count = 0
    
    for keyword, result in results.items():
        success_status = "УСПЕХ" if result['success'] else "НЕУДАЧА"
        success_count += 1 if result['success'] else 0
        
        logger.info(f"{keyword}: {success_status}")
        logger.info(f"  - Интерес: {result['interest']}")
        logger.info(f"  - Период: {result['period']}")
        
        if not result['success'] and 'error' in result:
            logger.info(f"  - Ошибка: {result['error']}")
    
    logger.info("=" * 60)
    logger.info(f"Общий результат: {success_count}/{len(results)} успешных запросов")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    exit(main())