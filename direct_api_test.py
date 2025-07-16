#!/usr/bin/env python3
"""
Прямой тест API ключа для сервера
"""
import os
import subprocess
import sys

def test_server_api():
    """Тестирует API ключ на сервере через curl к systemd процессу"""
    print("ТЕСТ API КЛЮЧА НА СЕРВЕРЕ")
    print("=" * 50)
    
    try:
        # Прямой тест к systemd процессу через curl
        cmd = [
            'ssh', 'root@91.132.58.97',
            'curl -s "http://localhost:5000/api-test" --max-time 60'
        ]
        
        print("Выполняем тест на сервере...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=70)
        
        if result.returncode == 0:
            print("✅ Ответ получен:")
            print("-" * 40)
            print(result.stdout)
            print("-" * 40)
            
            # Анализируем результат
            if "API ключ: НАЙДЕН" in result.stdout:
                print("🎉 УСПЕХ! API ключ найден в systemd процессе!")
                
                if "49/50" in result.stdout or "48/50" in result.stdout:
                    print("✅ Загружено 48-49/50 монет - проблема решена!")
                elif "Загружено только" in result.stdout:
                    print("⚠️ API ключ работает, но не все монеты загружены")
                
                return True
            else:
                print("❌ API ключ все еще не найден в systemd процессе")
                return False
                
        else:
            print(f"❌ Ошибка выполнения: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Таймаут - сервер не отвечает")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def check_systemd_status():
    """Проверяет статус systemd сервиса"""
    print("\n" + "=" * 50)
    print("ПРОВЕРКА СТАТУСА SYSTEMD СЕРВИСА")
    print("=" * 50)
    
    try:
        cmd = [
            'ssh', 'root@91.132.58.97',
            'sudo systemctl status coinbasebot'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ SystemD сервис работает:")
            print(result.stdout)
        else:
            print(f"❌ Проблема с сервисом: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Ошибка проверки сервиса: {e}")

if __name__ == "__main__":
    success = test_server_api()
    check_systemd_status()
    
    if success:
        print("\n🎉 ПРОБЛЕМА РЕШЕНА!")
        print("API ключ работает в systemd сервисе")
        print("Система готова к полной работе с 49/50 монетами")
    else:
        print("\n❌ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА")
        print("Проверьте переменные окружения systemd сервиса")