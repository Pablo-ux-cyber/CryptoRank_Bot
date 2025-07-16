#!/usr/bin/env python3
"""
Сравнение использования API ключей между Replit и сервером
"""

import logging
import os
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_api_key_usage():
    """Проверяет текущее использование API ключа"""
    
    logger.info("ПРОВЕРКА ИСПОЛЬЗОВАНИЯ API КЛЮЧА")
    logger.info("="*40)
    
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')
    logger.info(f"API ключ: {api_key[:10]}..." if len(api_key) > 10 else f"API ключ: {api_key}")
    
    # Проверка статуса API через прямой запрос
    try:
        # Простой запрос для проверки лимитов
        url = "https://min-api.cryptocompare.com/data/pricemulti"
        params = {
            'fsyms': 'BTC',
            'tsyms': 'USD',
            'api_key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        logger.info(f"HTTP статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ API работает")
            logger.info(f"BTC цена: ${data.get('BTC', {}).get('USD', 'N/A'):,}")
            
            # Проверка заголовков с информацией о лимитах
            headers = response.headers
            rate_limit_info = {}
            for header, value in headers.items():
                if 'rate' in header.lower() or 'limit' in header.lower():
                    rate_limit_info[header] = value
            
            if rate_limit_info:
                logger.info("Информация о лимитах:")
                for key, value in rate_limit_info.items():
                    logger.info(f"  {key}: {value}")
            else:
                logger.info("Информация о лимитах в заголовках не найдена")
                
        elif response.status_code == 429:
            logger.error("❌ API лимиты исчерпаны (HTTP 429)")
            logger.error(f"Ответ: {response.text}")
        else:
            logger.warning(f"⚠️ Неожиданный статус: {response.status_code}")
            logger.warning(f"Ответ: {response.text}")
            
    except Exception as e:
        logger.error(f"Ошибка при проверке API: {e}")

def compare_environments():
    """Сравнивает использование API между средами"""
    
    logger.info("\nСРАВНЕНИЕ СРЕД:")
    logger.info("Replit: стабильно 49/50 монет")
    logger.info("Сервер: только 9/50 монет (лимиты исчерпаны)")
    logger.info("\nВОЗМОЖНЫЕ ПРИЧИНЫ РАЗЛИЧИЙ:")
    logger.info("1. На сервере больше запросов (scheduler + тесты)")
    logger.info("2. Разное время запуска (сервер мог начать раньше)")
    logger.info("3. Возможны другие приложения использующие тот же ключ")
    logger.info("4. Лимиты считаются по часам/дням - сервер мог исчерпать суточный лимит")

def suggest_solutions():
    """Предлагает решения проблемы"""
    
    logger.info("\nРЕШЕНИЯ:")
    logger.info("1. НЕМЕДЛЕННОЕ: Ждать восстановления лимитов (обычно до 24 часов)")
    logger.info("2. БЫСТРОЕ: Получить второй API ключ для сервера")
    logger.info("3. ДОЛГОСРОЧНОЕ: Обновить план CryptoCompare до платного")
    logger.info("4. ВРЕМЕННОЕ: Добавить кеширование на 2-4 часа только на сервере")

if __name__ == "__main__":
    check_api_key_usage()
    compare_environments()
    suggest_solutions()