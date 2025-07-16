#!/usr/bin/env python3
"""
Диагностический скрипт для проверки доступности всех монет
"""

import requests
import os
import time
from datetime import datetime

def test_coin_availability():
    """Тестирует доступность всех монет из списка"""
    
    # Список монет для тестирования
    coins = [
        'BTC', 'ETH', 'BNB', 'XRP', 'SOL', 'ADA', 'DOGE', 'TRX', 'HYPE', 'XLM', 
        'SUI', 'LINK', 'HBAR', 'BCH', 'AVAX', 'SHIB', 'TON', 'LTC', 'DOT', 'XMR',
        'UNI', 'PEPE', 'AAVE', 'APT', 'NEAR', 'ONDO', 'MNT'
    ]
    
    api_key = os.environ.get('CRYPTOCOMPARE_API_KEY')
    base_url = "https://min-api.cryptocompare.com/data/v2/histoday"
    
    print(f"🔍 Тестирование доступности {len(coins)} монет...")
    print(f"🔑 API ключ: {'✅ Найден' if api_key else '❌ Отсутствует'}")
    print("-" * 70)
    
    available_coins = []
    unavailable_coins = []
    
    for i, coin in enumerate(coins, 1):
        print(f"[{i:2d}/27] Тестирую {coin}...", end=" ")
        
        try:
            params = {
                'fsym': coin,
                'tsym': 'USD',
                'limit': 100,  # Тестовый запрос на 100 дней
                'aggregate': 1
            }
            
            if api_key:
                params['api_key'] = api_key
            
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('Response') == 'Error':
                    error_msg = data.get('Message', 'Unknown error')
                    print(f"❌ API Error: {error_msg}")
                    unavailable_coins.append((coin, f"API Error: {error_msg}"))
                elif 'Data' in data and 'Data' in data['Data']:
                    records = len(data['Data']['Data'])
                    print(f"✅ {records} записей")
                    available_coins.append(coin)
                else:
                    print(f"❌ Неправильный формат данных")
                    unavailable_coins.append((coin, "Неправильный формат данных"))
            else:
                print(f"❌ HTTP {response.status_code}")
                unavailable_coins.append((coin, f"HTTP {response.status_code}"))
                
        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")
            unavailable_coins.append((coin, str(e)))
        
        # Небольшая задержка между запросами
        time.sleep(0.1)
    
    # Итоговый отчет
    print("\n" + "="*70)
    print(f"📊 ИТОГОВЫЙ ОТЧЕТ:")
    print(f"✅ Доступных монет: {len(available_coins)}/27")
    print(f"❌ Недоступных монет: {len(unavailable_coins)}/27")
    
    if available_coins:
        print(f"\n✅ ДОСТУПНЫЕ МОНЕТЫ ({len(available_coins)}):")
        for coin in available_coins:
            print(f"   • {coin}")
    
    if unavailable_coins:
        print(f"\n❌ НЕДОСТУПНЫЕ МОНЕТЫ ({len(unavailable_coins)}):")
        for coin, reason in unavailable_coins:
            print(f"   • {coin}: {reason}")
    
    # Предложения по исправлению
    print(f"\n🔧 ПРЕДЛОЖЕНИЯ ПО ИСПРАВЛЕНИЮ:")
    if unavailable_coins:
        print("1. Удалить недоступные монеты из списка")
        print("2. Заменить недоступные монеты на альтернативные")
        print("3. Использовать альтернативный API для недоступных монет")
    
    return available_coins, unavailable_coins

if __name__ == "__main__":
    available, unavailable = test_coin_availability()
    
    if unavailable:
        print(f"\n⚠️  ВНИМАНИЕ: {len(unavailable)} монет недоступны!")
        print("Рекомендуется обновить список для стабильной работы.")
    else:
        print(f"\n🎉 ВСЕ МОНЕТЫ ДОСТУПНЫ!")