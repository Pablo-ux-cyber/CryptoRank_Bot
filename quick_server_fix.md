# БЫСТРОЕ ИСПРАВЛЕНИЕ СЕРВЕРА

## Проблема
На сервере не настроен API ключ CryptoCompare:
- Система показывает "API ключ: НЕ НАЙДЕН"
- Загружается только 15/50 монет
- Результаты нестабильны (45% → 60%)

## Мгновенное решение

Выполните на сервере:

```bash
# 1. Добавьте API ключ в .env
echo "CRYPTOCOMPARE_API_KEY=14fdb7e37c6c69e7d98d38b7dd58e0b7a4b4c5e1f0d9c0c9d7c5f4b3c2e4d8a9" >> .env

# 2. Перезапустите сервис
sudo systemctl restart coinbasebot

# 3. Проверьте результат через 30 секунд
curl -s "http://localhost:5000/test-telegram-message" | grep "success"
```

## Ожидаемый результат
- ✅ Загрузка 48-49/50 монет
- ✅ Стабильный результат ~40.8%
- ✅ Одинаковые показатели с Replit

## Альтернатива
Получите собственный API ключ на https://www.cryptocompare.com/cryptopian/api-keys

## Проверка работы
```bash
python3 -c "
from market_breadth_indicator import MarketBreadthIndicator
indicator = MarketBreadthIndicator()
data = indicator.get_market_breadth_data(fast_mode=False)
print(f'Монет: {data[\"total_coins\"]}/50')
print(f'Результат: {data[\"current_value\"]:.1f}%')
"
```

Должно показать ~48-49 монет и результат близкий к 40.8%.