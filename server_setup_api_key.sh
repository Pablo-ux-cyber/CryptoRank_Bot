#!/bin/bash
# Настройка API ключа CryptoCompare на сервере

echo "=== НАСТРОЙКА API КЛЮЧА CRYPTOCOMPARE ==="

# Проверяем текущий статус
echo "Текущий API ключ:"
python3 -c "import os; print('Найден:', os.getenv('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')[:10] + '...' if os.getenv('CRYPTOCOMPARE_API_KEY') else 'НЕ НАЙДЕН')"

echo ""
echo "Добавляем API ключ в .env файл..."

# Создаем или обновляем .env файл
if [ ! -f .env ]; then
    echo "Создаем новый .env файл..."
    touch .env
fi

# Проверяем есть ли уже ключ в .env
if grep -q "CRYPTOCOMPARE_API_KEY" .env; then
    echo "API ключ уже есть в .env"
    grep "CRYPTOCOMPARE_API_KEY" .env
else
    echo "Добавляем API ключ в .env..."
    # Запрашиваем API ключ у пользователя
    echo "Введите ваш API ключ CryptoCompare:"
    read -r api_key
    if [ -n "$api_key" ]; then
        echo "CRYPTOCOMPARE_API_KEY=$api_key" >> .env
    else
        echo "API ключ не введен, используем значение по умолчанию"
        echo "CRYPTOCOMPARE_API_KEY=your_api_key_here" >> .env
    fi
    echo "API ключ добавлен в .env"
fi

echo ""
echo "Перезапускаем сервис для применения изменений..."
sudo systemctl restart coinbasebot

echo ""
echo "Ждем 5 секунд для инициализации..."
sleep 5

echo ""
echo "Проверяем статус после настройки:"
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')
print(f'API ключ после настройки: {key[:10]}...' if len(key) > 10 else f'API ключ: {key}')
"

echo ""
echo "Тестируем API:"
python3 -c "
from crypto_analyzer_cryptocompare import CryptoAnalyzer
analyzer = CryptoAnalyzer(cache=None)
data = analyzer.get_coin_history('BTC', 10)
print('✅ API работает - BTC загружен' if data is not None else '❌ API не работает')
print(f'Записей: {len(data)}' if data is not None else 'Нет данных')
"

echo ""
echo "=== НАСТРОЙКА ЗАВЕРШЕНА ==="