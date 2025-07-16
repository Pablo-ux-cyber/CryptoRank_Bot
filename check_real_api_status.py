#!/usr/bin/env python3
"""
Проверка реального статуса API и загрузки монет
"""
import os
import sys
import requests
import json
from datetime import datetime
import time

def check_api_key_status():
    """Проверяет статус API ключа"""
    print("ПРОВЕРКА СТАТУСА API КЛЮЧА")
    print("=" * 50)
    
    # Проверить переменную окружения
    api_key = os.environ.get('CRYPTOCOMPARE_API_KEY')
    if not api_key:
        print("❌ API ключ не найден в переменных окружения")
        return False
    
    print(f"✅ API ключ найден: {api_key[:20]}...")
    
    # Тест простого запроса
    try:
        url = "https://min-api.cryptocompare.com/data/v2/histoday"
        params = {
            'fsym': 'BTC',
            'tsym': 'USD',
            'limit': 10,
            'api_key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('Response') == 'Success':
                records = len(data.get('Data', {}).get('Data', []))
                print(f"✅ API работает! Получено {records} записей для BTC")
                return True
            else:
                print(f"❌ API ошибка: {data.get('Message', 'Неизвестная ошибка')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

def test_market_breadth_loading():
    """Тестирует загрузку данных Market Breadth"""
    print("\nТЕСТ ЗАГРУЗКИ MARKET BREADTH")
    print("=" * 50)
    
    try:
        from market_breadth_indicator import MarketBreadthIndicator
        
        indicator = MarketBreadthIndicator()
        
        print("Начинаем загрузку данных для 50 монет...")
        print("Это может занять несколько минут...")
        
        start_time = time.time()
        data = indicator.get_market_breadth_data(fast_mode=False)
        end_time = time.time()
        
        duration = end_time - start_time
        
        print(f"✅ Загрузка завершена за {duration:.1f} секунд")
        print(f"📊 Загружено монет: {data['total_coins']}/50")
        print(f"📈 Market Breadth: {data['current_value']:.1f}%")
        print(f"🎯 Статус: {data.get('status', 'Неизвестно')}")
        
        if data['total_coins'] >= 45:
            print("✅ Загружено достаточно монет для точного анализа")
        else:
            print("⚠️ Загружено недостаточно монет - возможны неточности")
            
        return data
        
    except Exception as e:
        print(f"❌ Ошибка загрузки Market Breadth: {e}")
        return None

def main():
    """Основная функция"""
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Проверить API ключ
    if not check_api_key_status():
        print("\n❌ API ключ не работает. Проверьте конфигурацию.")
        sys.exit(1)
    
    # Тест загрузки Market Breadth
    data = test_market_breadth_loading()
    
    if data:
        print(f"\n✅ УСПЕШНО: {data['total_coins']}/50 монет загружено")
        print(f"   Market Breadth: {data['current_value']:.1f}%")
    else:
        print("\n❌ ОШИБКА: Не удалось загрузить данные")

if __name__ == "__main__":
    main()