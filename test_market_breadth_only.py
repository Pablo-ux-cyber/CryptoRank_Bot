#!/usr/bin/env python3
"""
Тест только Market Breadth данных без графика
"""
import os
import requests
import json
from datetime import datetime

def test_market_breadth_data():
    """Тестирует только данные Market Breadth без создания графика"""
    print("ТЕСТ MARKET BREADTH ДАННЫХ (БЕЗ ГРАФИКА)")
    print("=" * 50)
    
    # Проверить API ключ
    api_key = os.environ.get('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')
    print(f"API ключ: {api_key[:20]}..." if len(api_key) > 20 else f"API ключ: {api_key}")
    
    # Запрос данных Market Breadth
    print("\nЗапрос данных Market Breadth с сервера...")
    try:
        response = requests.get('http://91.132.58.97:5000/market-breadth-data', timeout=180)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Данные получены успешно")
                
                # Показать ключевые данные
                if 'total_coins' in data:
                    print(f"📊 Загружено монет: {data['total_coins']}/50")
                
                if 'current_value' in data:
                    print(f"📈 Market Breadth: {data['current_value']:.1f}%")
                
                if 'status' in data:
                    print(f"🎯 Статус: {data['status']}")
                
                # Показать все данные
                print(f"\nВсе данные:")
                for key, value in data.items():
                    if key not in ['indicator_data', 'historical_data']:
                        print(f"  {key}: {value}")
                
            except json.JSONDecodeError:
                print("❌ Ошибка парсинга JSON")
                print(f"Ответ: {response.text[:200]}...")
                
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            print(f"Ответ: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса (180 сек)")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    test_market_breadth_data()