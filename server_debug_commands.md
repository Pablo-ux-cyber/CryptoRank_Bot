# Команды для диагностики сервера

Выполните эти команды на сервере для диагностики проблемы:

## 1. Проверка отсутствия кеша
```bash
ls -la cache/ 2>/dev/null || echo "Папка cache отсутствует (правильно)"
```

## 2. Проверка версии кода
```bash
grep -n "cache=None" crypto_analyzer_cryptocompare.py market_breadth_indicator.py
```

## 3. Прямой тест Market Breadth
```bash
python3 -c "
from market_breadth_indicator import MarketBreadthIndicator
from datetime import datetime
print(f'Время: {datetime.now()}')
indicator = MarketBreadthIndicator()
data = indicator.get_market_breadth_data(fast_mode=False)
if data:
    print(f'Результат: {data[\"current_value\"]:.1f}%')
    print(f'Монет: {data[\"total_coins\"]}')
    print(f'Статус: {data[\"condition\"]}')
else:
    print('Ошибка')
"
```

## 4. Проверка консистентности (2 запроса подряд)
```bash
python3 -c "
from market_breadth_indicator import MarketBreadthIndicator
indicator = MarketBreadthIndicator()

print('Тест 1:')
data1 = indicator.get_market_breadth_data(fast_mode=False)
print(f'Результат 1: {data1[\"current_value\"]:.1f}%' if data1 else 'Ошибка')

print('\nТест 2:')
data2 = indicator.get_market_breadth_data(fast_mode=False)
print(f'Результат 2: {data2[\"current_value\"]:.1f}%' if data2 else 'Ошибка')

if data1 and data2:
    diff = abs(data1['current_value'] - data2['current_value'])
    print(f'Разница: {diff:.1f}%')
    if diff > 5:
        print('❌ ПРОБЛЕМА: Большой разброс!')
    else:
        print('✅ Данные консистентны')
"
```

## 5. Проверка API ключа
```bash
python3 -c "
import os
key = os.getenv('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')
print(f'API ключ: {key[:10]}...' if len(key) > 10 else f'API ключ: {key}')
"
```

## 6. Проверка гита и последнего коммита
```bash
git log --oneline -5
git status
```

Результаты покажут где именно проблема на сервере.