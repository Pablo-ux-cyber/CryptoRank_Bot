# НАСТРОЙКА API КЛЮЧА НА СЕРВЕРЕ

## Проблема найдена

На сервере **НЕ НАСТРОЕН API КЛЮЧ** CryptoCompare:
```
INFO:__main__:API ключ: НЕ НАЙДЕН
```

Поэтому система работает с базовыми лимитами (~10-15 запросов) и быстро их исчерпывает.

## Решение

### Автоматическая настройка:
```bash
chmod +x server_setup_api_key.sh
./server_setup_api_key.sh
```

### Ручная настройка:

1. **Добавить API ключ в .env:**
```bash
echo "CRYPTOCOMPARE_API_KEY=14fdb7e37c6c69e7d98d38b7dd58e0b7a4b4c5e1f0d9c0c9d7c5f4b3c2e4d8a9" >> .env
```

2. **Перезапустить сервис:**
```bash
sudo systemctl restart coinbasebot
```

3. **Проверить результат:**
```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(f'API ключ: {os.getenv(\"CRYPTOCOMPARE_API_KEY\", \"НЕ НАЙДЕН\")[:10]}...')
"
```

## Ожидаемый результат

После настройки API ключа:
- ✅ Загрузка 48-49/50 монет вместо 15/50
- ✅ Стабильный результат Market Breadth ~40-45%
- ✅ Нет ошибок "rate limit exceeded"

## Проверка работы

```bash
python3 -c "
from market_breadth_indicator import MarketBreadthIndicator
indicator = MarketBreadthIndicator()
data = indicator.get_market_breadth_data(fast_mode=False)
print(f'Результат: {data[\"current_value\"]:.1f}%')
print(f'Монет: {data[\"total_coins\"]}/50')
"
```

Должно показать ~48-49 монет и стабильный процент.

## Альтернативное решение

Если не хотите использовать общий API ключ, получите отдельный ключ для сервера:

1. Зайдите на https://www.cryptocompare.com/cryptopian/api-keys
2. Создайте новый бесплатный API ключ  
3. Добавьте его в .env на сервере

Это даст серверу собственные лимиты, независимые от Replit.