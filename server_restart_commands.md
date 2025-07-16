# КОМАНДЫ ДЛЯ ПЕРЕЗАПУСКА СЕРВЕРА

## Проблема
Вы добавили API ключ в .env, но система все еще показывает "API ключ: НЕ НАЙДЕН".

## Решение - перезапустить SystemD сервис

На сервере выполните:

```bash
# 1. Остановить сервис
sudo systemctl stop coinbasebot

# 2. Перезагрузить конфигурацию systemd (если изменялся .service файл)
sudo systemctl daemon-reload

# 3. Запустить сервис снова
sudo systemctl start coinbasebot

# 4. Проверить статус
sudo systemctl status coinbasebot

# 5. Проверить что API ключ теперь найден
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('CRYPTOCOMPARE_API_KEY', 'НЕ НАЙДЕН')
print(f'API ключ: {key[:10]}...' if len(key) > 10 else f'API ключ: {key}')
"
```

## Альтернативные команды

Если простой restart не помогает:

```bash
# Полная перезагрузка сервиса
sudo systemctl stop coinbasebot
sudo systemctl disable coinbasebot
sudo systemctl enable coinbasebot
sudo systemctl start coinbasebot
```

## Проверка результата

После перезапуска повторите тест:
```bash
python3 server_api_limit_fix.py
```

Должно показать:
- "API ключ: 14fdb7e37c..." вместо "НЕ НАЙДЕН"
- 48-49/50 монет вместо 11/50
- Нет ошибок "rate limit exceeded"

## Если все еще не работает

Проверьте переменные окружения напрямую:
```bash
# Проверить .env файл
cat .env | grep CRYPTOCOMPARE

# Проверить переменные окружения процесса
sudo systemctl show coinbasebot --property=Environment
```