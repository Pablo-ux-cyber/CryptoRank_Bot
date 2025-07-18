# ОБЕСПЕЧЕНИЕ КОНСИСТЕНТНОСТИ ДАННЫХ

## Проблема решена: API лимиты на сервере

### ✅ Replit - работает идеально
- **Результат**: 40.8% (стабильно)
- **Монет загружено**: 49/50 
- **API лимиты**: В норме
- **Кеширование**: Отключено

### ❌ Сервер - отсутствует API ключ
- **Проблема**: "API ключ: НЕ НАЙДЕН" + "You are over your rate limit please upgrade your account!"
- **Результат**: Нестабильный (45% → 60%)
- **Монет загружено**: Только 15/50 из-за отсутствия API ключа
- **Причина скачков**: Система работает с базовыми лимитами без API ключа

## Решение проблемы на сервере

### Краткосрочные решения:

1. **НЕМЕДЛЕННО: Настроить API ключ на сервере**
```bash
chmod +x server_setup_api_key.sh
./server_setup_api_key.sh
```

2. **Проверить текущий статус API**
```bash
python3 -c "
from crypto_analyzer_cryptocompare import CryptoAnalyzer
analyzer = CryptoAnalyzer(cache=None)
data = analyzer.get_coin_history('BTC', 30)
print('API работает' if data is not None else 'API заблокирован')
"
```

### Долгосрочные решения:

1. **Обновить план CryptoCompare API**
   - Перейти на платный план с большими лимитами
   - Или получить дополнительный API ключ

2. **Добавить обработку лимитов в код**
   - Детектировать ошибки лимитов
   - Автоматически переключаться на резервные ключи
   - Добавлять задержки между запросами

3. **Краткосрочное кеширование**
   - TTL кеш на 1-2 часа для экономии запросов
   - Только при критическом исчерпании лимитов

## Код обработки лимитов

```python
# В crypto_analyzer_cryptocompare.py добавить:
def _handle_rate_limit_error(self, response_text):
    if "rate limit" in response_text.lower():
        logger.error("API лимит исчерпан - нужно подождать или обновить план")
        return "RATE_LIMIT_EXCEEDED"
    return None

# В market_breadth_indicator.py добавить проверку:
def get_market_breadth_data(self, fast_mode=False):
    # ... существующий код ...
    
    if total_loaded_coins < 40:  # Минимум для надежного анализа
        logger.error(f"Критически мало данных: {total_loaded_coins}/50 монет")
        logger.error("Возможная причина: исчерпаны API лимиты")
        return None
```

## Мониторинг проблемы

Добавить в daily сообщения информацию о количестве загруженных монет:
```
Market by 200MA: 🟡 Neutral: 45.2% (49/50 coins)
```

Это поможет сразу видеть когда API лимиты влияют на результаты.

## Статус

- [x] Проблема диагностирована - API лимиты на сервере
- [x] Создан скрипт диагностики `server_api_limit_fix.py`
- [ ] Ждать восстановления лимитов (24 часа)
- [ ] Или обновить план CryptoCompare API
- [ ] Добавить обработку лимитов в production код