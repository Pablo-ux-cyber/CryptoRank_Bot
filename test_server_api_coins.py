#!/usr/bin/env python3
"""
Тест загрузки монет через API на сервере
"""
import os
import requests
import json
from datetime import datetime

def test_server_api_coins():
    """Тестирует загрузку монет через API сервера"""
    print("ТЕСТ ЗАГРУЗКИ МОНЕТ НА СЕРВЕРЕ")
    print("=" * 50)
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверить API ключ в окружении
    api_key = os.environ.get('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')
    print(f"API ключ: {api_key[:20]}..." if len(api_key) > 20 else f"API ключ: {api_key}")
    
    # Тест через веб-интерфейс сервера
    print("\nТест через веб-интерфейс сервера:")
    try:
        response = requests.get('http://91.132.58.97:5000/test-telegram-message', timeout=180)
        
        if response.status_code == 200:
            result = response.text
            print(f"✅ Запрос успешен (код: {response.status_code})")
            
            # Найти информацию о монетах в ответе
            if "Market by 200MA" in result:
                print("✅ Market Breadth данные найдены")
                
                # Найти количество монет
                if "монет" in result.lower():
                    lines = result.split('\n')
                    for line in lines:
                        if 'монет' in line.lower():
                            print(f"📊 {line.strip()}")
                
                # Найти процент Market Breadth
                if "%" in result:
                    lines = result.split('\n')
                    for line in lines:
                        if "Market by 200MA" in line and "%" in line:
                            print(f"📈 {line.strip()}")
                            
            else:
                print("❌ Market Breadth данные не найдены")
                print(f"Ответ: {result[:200]}...")
                
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            print(f"Ответ: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса (180 сек)")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
    
    # Прямой тест Market Breadth
    print("\nПрямой тест Market Breadth:")
    try:
        from market_breadth_indicator import MarketBreadthIndicator
        
        indicator = MarketBreadthIndicator()
        data = indicator.get_market_breadth_data(fast_mode=False)
        
        print(f"📊 Загружено монет: {data['total_coins']}/50")
        print(f"📈 Market Breadth: {data['current_value']:.1f}%")
        print(f"🎯 Статус: {data.get('status', 'Неизвестно')}")
        
        if data['total_coins'] >= 45:
            print("✅ Достаточно монет для точного анализа")
        else:
            print("⚠️  Недостаточно монет - возможны неточности")
            
    except Exception as e:
        print(f"❌ Ошибка Market Breadth: {e}")

if __name__ == "__main__":
    test_server_api_coins()