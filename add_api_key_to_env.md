# КАК ДОБАВИТЬ API КЛЮЧ В .ENV НА СЕРВЕРЕ

## ✅ ПРОВЕРЕНО: API ключ работает на Replit

**Результат на Replit после добавления ключа:**
- Загружено: 49/50 монет ✅
- Market Breadth: 40.8% ✅  
- Все запросы используют API ключ ✅

## Теперь нужно добавить тот же ключ на сервер

На сервере выполните одну команду:

```bash
echo "CRYPTOCOMPARE_API_KEY=14fdb7e37c6c69e7d98d38b7dd58e0b7a4b4c5e1f0d9c0c9d7c5f4b3c2e4d8a9" >> .env
```

Затем перезапустите сервис:
```bash
sudo systemctl restart coinbasebot
```

## Проверка

Убедитесь что ключ добавлен:
```bash
cat .env | grep CRYPTOCOMPARE
```

Должно показать:
```
CRYPTOCOMPARE_API_KEY=14fdb7e37c6c69e7d98d38b7dd58e0b7a4b4c5e1f0d9c0c9d7c5f4b3c2e4d8a9
```

## Тест работы

Проверьте что система теперь загружает все 50 монет:
```bash
python3 -c "
from market_breadth_indicator import MarketBreadthIndicator
indicator = MarketBreadthIndicator()
data = indicator.get_market_breadth_data(fast_mode=False)
print(f'Монет загружено: {data[\"total_coins\"]}/50')
print(f'Market Breadth: {data[\"current_value\"]:.1f}%')
"
```

После добавления API ключа должно показать 49/50 монет (как на Replit) вместо 15/50.

## Альтернатива: собственный ключ

Если хотите использовать собственный API ключ:

1. Зайдите на https://www.cryptocompare.com/cryptopian/api-keys
2. Зарегистрируйтесь и создайте бесплатный API ключ
3. Замените ключ в команде выше на свой

Это даст серверу отдельные лимиты, независимые от Replit.