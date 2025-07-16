#!/usr/bin/env python3
"""
Проверка переменных окружения в SystemD сервисе
"""
import os
import subprocess
import sys

def check_systemd_environment():
    """Проверяет переменные окружения в SystemD сервисе"""
    print("ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ SYSTEMD")
    print("=" * 50)
    
    # Проверить переменные через systemctl
    try:
        result = subprocess.run(
            ['sudo', 'systemctl', 'show', 'coinbasebot', '--property=Environment'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"SystemD Environment: {result.stdout.strip()}")
        else:
            print(f"Ошибка получения Environment: {result.stderr}")
    except Exception as e:
        print(f"Ошибка systemctl: {e}")
    
    # Проверить прямо в Python процессе
    print("\nПеременные окружения Python процесса:")
    cryptocompare_key = os.environ.get('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')
    print(f"CRYPTOCOMPARE_API_KEY: {cryptocompare_key[:20]}..." if len(cryptocompare_key) > 20 else f"CRYPTOCOMPARE_API_KEY: {cryptocompare_key}")
    
    # Проверить через dotenv
    try:
        from dotenv import load_dotenv
        load_dotenv()
        dotenv_key = os.getenv('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')
        print(f"Через dotenv: {dotenv_key[:20]}..." if len(dotenv_key) > 20 else f"Через dotenv: {dotenv_key}")
    except ImportError:
        print("dotenv не установлен")
    
    # Проверить содержимое .env файла
    print("\nСодержимое .env файла:")
    try:
        with open('.env', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'CRYPTOCOMPARE_API_KEY' in line:
                    key_part = line.split('=')[1].strip()[:20]
                    print(f".env файл: {key_part}...")
    except FileNotFoundError:
        print(".env файл не найден")
    except Exception as e:
        print(f"Ошибка чтения .env: {e}")

def test_api_direct():
    """Тестирует API напрямую с ключом из SystemD"""
    print("\n" + "=" * 50)
    print("ТЕСТ API С КЛЮЧОМ ИЗ SYSTEMD")
    print("=" * 50)
    
    # Получить ключ из переменных окружения (как его видит SystemD процесс)
    api_key = os.environ.get('CRYPTOCOMPARE_API_KEY')
    
    if not api_key:
        print("❌ API ключ не найден в переменных окружения")
        print("Это означает, что SystemD сервис не передает переменную в Python процесс")
        return False
    
    print(f"✅ API ключ найден: {api_key[:20]}...")
    
    # Тест простого API запроса
    try:
        import requests
        
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
                print(f"✅ API работает! Получено {len(data.get('Data', {}).get('Data', []))} записей")
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

if __name__ == "__main__":
    check_systemd_environment()
    test_api_direct()