#!/usr/bin/env python3
"""
Реальный тест загрузки 50 монет на сервере
"""
import os
import requests
import json
from datetime import datetime

def test_real_server_coins():
    """Тестирует реальную загрузку 50 монет на сервере через API"""
    print("РЕАЛЬНЫЙ ТЕСТ ЗАГРУЗКИ 50 МОНЕТ НА СЕРВЕРЕ")
    print("=" * 60)
    
    # Проверить API ключ
    api_key = os.environ.get('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')
    print(f"API ключ: {api_key[:20]}..." if len(api_key) > 20 else f"API ключ: {api_key}")
    
    # Получить данные напрямую с сервера
    print("\nЗапрос к серверу http://91.132.58.97:5000/test-telegram-message...")
    print("Ожидание реальных данных...")
    
    try:
        # Увеличиваем таймаут для полной загрузки 50 монет
        response = requests.get('http://91.132.58.97:5000/test-telegram-message', timeout=300)
        
        if response.status_code == 200:
            result = response.text
            print(f"Статус: {response.status_code} OK")
            print(f"Размер ответа: {len(result)} байт")
            
            # Найти информацию о количестве монет
            lines = result.split('\n')
            for line in lines:
                if 'монет' in line.lower() or 'coins' in line.lower():
                    print(f"Информация о монетах: {line.strip()}")
                elif 'market by 200ma' in line.lower():
                    print(f"Market Breadth: {line.strip()}")
                elif 'fear' in line.lower() and 'greed' in line.lower():
                    print(f"Fear & Greed: {line.strip()}")
                elif 'altcoin season' in line.lower():
                    print(f"Altcoin Season: {line.strip()}")
            
            # Показать первые 500 символов ответа
            print(f"\nПервые 500 символов ответа:")
            print(result[:500])
            
        else:
            print(f"Ошибка HTTP: {response.status_code}")
            print(f"Ответ: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("Таймаут запроса (300 сек) - сервер долго обрабатывает данные")
    except Exception as e:
        print(f"Ошибка запроса: {e}")

if __name__ == "__main__":
    test_real_server_coins()