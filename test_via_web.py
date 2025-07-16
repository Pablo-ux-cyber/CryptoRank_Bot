#!/usr/bin/env python3
"""
Тест API через веб-интерфейс бота (который работает в systemd)
"""
import requests
import time

def test_via_web_interface():
    """Тестирует API через веб-интерфейс бота"""
    print("ТЕСТ API ЧЕРЕЗ ВЕБ-ИНТЕРФЕЙС SYSTEMD СЕРВИСА")
    print("=" * 60)
    
    # URL веб-интерфейса (порт 5000 как в systemd)
    base_url = "http://localhost:5000"
    
    print(f"Подключение к {base_url}...")
    
    try:
        # Проверить что сервер доступен
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ Веб-сервер доступен")
        else:
            print(f"❌ Веб-сервер недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    
    # Запустить тест Market Breadth через веб-интерфейс
    print("\nЗапуск теста Market Breadth через systemd процесс...")
    
    try:
        test_url = f"{base_url}/test-market-breadth"
        print(f"Отправка запроса: {test_url}")
        
        response = requests.get(test_url, timeout=120)  # 2 минуты на загрузку 50 монет
        
        if response.status_code == 200:
            result = response.text
            print("✅ Ответ получен:")
            print("-" * 40)
            print(result)
            print("-" * 40)
            
            # Проверить результат
            if "49/50" in result or "48/50" in result:
                print("🎉 УСПЕХ! API ключ работает в systemd процессе!")
                print("✅ Загружено 48-49/50 монет")
                
                if "40.8%" in result or "40." in result:
                    print("✅ Результат стабильный (~40.8%)")
                
                return True
            elif "API ключ: НЕ НАЙДЕН" in result:
                print("❌ API ключ все еще не найден в systemd процессе")
                return False
            else:
                print("⚠️ Результат неопределенный - требует анализа")
                return False
                
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            print(f"Ответ: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут - загрузка заняла более 2 минут")
        return False
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

def check_api_endpoint():
    """Проверяет эндпоинт для диагностики API"""
    print("\n" + "=" * 60)
    print("ПРОВЕРКА ДИАГНОСТИЧЕСКОГО ЭНДПОИНТА")
    print("=" * 60)
    
    try:
        # Проверить есть ли диагностический эндпоинт
        diag_url = "http://localhost:5000/api-diagnostic"
        response = requests.get(diag_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Диагностический эндпоинт доступен:")
            print(response.text)
        else:
            print(f"⚠️ Диагностический эндпоинт недоступен: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Диагностический эндпоинт недоступен: {e}")

if __name__ == "__main__":
    success = test_via_web_interface()
    check_api_endpoint()
    
    if success:
        print("\n🎉 РЕШЕНИЕ НАЙДЕНО!")
        print("API ключ работает в systemd сервисе")
        print("Система готова к работе с 49/50 монетами")
    else:
        print("\n❌ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА")
        print("Проверьте логи systemd сервиса:")
        print("sudo journalctl -u coinbasebot -f")