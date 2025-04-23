# Руководство по интеграции Telethon для бота Coinbase Rank

## Общая информация

Telethon позволит значительно улучшить надежность сбора данных из Telegram канала, так как использует официальный API вместо парсинга веб-версии. Это сократит количество ошибок и улучшит стабильность бота.

## Шаги интеграции

### 1. Получение API ключей Telegram

Перед использованием Telethon, вам необходимо получить `API_ID` и `API_HASH`:

1. Перейдите на https://my.telegram.org/
2. Войдите в свой аккаунт Telegram
3. Перейдите в раздел "API development tools"
4. Создайте новое приложение, заполнив необходимые поля
5. Запишите полученные `api_id` и `api_hash`

### 2. Добавление переменных окружения

Добавьте новые переменные окружения на вашем сервере:

```bash
export TELEGRAM_API_ID="ваш_api_id"
export TELEGRAM_API_HASH="ваш_api_hash"
```

Эти переменные лучше добавить в файл системного сервиса:

```bash
sudo nano /etc/systemd/system/coinbasebot.service
```

Добавьте строки в секцию `[Service]`:

```
Environment=TELEGRAM_API_ID=ваш_api_id
Environment=TELEGRAM_API_HASH=ваш_api_hash
```

### 3. Установка зависимостей

Установите библиотеку Telethon:

```bash
pip install telethon
```

### 4. Замена файла скрапера

Замените существующий файл `scraper.py` новой версией `scraper_telethon.py` или создайте новый файл и обновите импорты в других файлах.

### 5. Модификация scheduler.py

Требуются небольшие изменения в файле `scheduler.py` для поддержки асинхронных вызовов Telethon:

1. Импортируйте asyncio:
   ```python
   import asyncio
   ```

2. Модифицируйте метод `run_scraping_job`:
   ```python
   def run_scraping_job(self):
       """
       Выполняет задание по скрапингу: получает данные SensorTower и отправляет в Telegram
       только если рейтинг изменился или это первый запуск
       """
       logger.info(f"Выполняется запланированное задание скрапинга в {datetime.now()}")
       
       try:
           # Проверяем соединение с Telegram
           if not self.telegram_bot.test_connection():
               logger.error("Ошибка соединения с Telegram. Задание прервано.")
               return False
           
           # Получаем данные о рейтинге (асинхронно)
           rankings_data = asyncio.run(self.scraper.scrape_category_rankings())
           
           # Остальной код без изменений
           ...
   ```

### 6. Обработка первой аутентификации

При первом запуске Telethon создаст файл сессии и может потребовать аутентификацию с помощью кода подтверждения. Рекомендуется запустить простой скрипт для первичной аутентификации:

```python
from telethon import TelegramClient
import os

api_id = int(os.environ.get('TELEGRAM_API_ID'))
api_hash = os.environ.get('TELEGRAM_API_HASH')

# Создаем клиент
client = TelegramClient('sensortower_session', api_id, api_hash)

async def main():
    # Подключаемся к Telegram
    await client.start()
    
    # Получаем канал
    channel = await client.get_entity("@coinbaseappstore")
    print(f"Successfully connected to channel: {channel.title}")
    
    # Получаем последние сообщения
    messages = await client.get_messages(channel, limit=5)
    
    for msg in messages:
        print(f"Message ID: {msg.id}, Text: {msg.text[:30]}...")

# Запускаем асинхронную функцию
import asyncio
asyncio.run(main())
```

Запустите этот скрипт на сервере, следуйте инструкциям для аутентификации, и после успешного выполнения будет создан файл `sensortower_session.session`, который будет использоваться для автоматической аутентификации в будущем.

### 7. Протестируйте и перезапустите службу

После всех изменений перезапустите службу:

```bash
sudo systemctl daemon-reload
sudo systemctl restart coinbasebot
```

## Преимущества использования Telethon

1. **Надёжность**: Официальный API более стабилен, чем парсинг веб-интерфейса
2. **Скорость**: API-запросы выполняются быстрее
3. **Отсутствие блокировок**: Официальный API не ограничивает доступ так жестко, как веб-интерфейс
4. **Больше возможностей**: Можно получать больше информации о сообщениях, участниках и т.д.
5. **Обновления в реальном времени**: Возможность подписки на новые сообщения через обработчики событий

## Возможные проблемы и решения

1. **Ошибка аутентификации**: Убедитесь, что переменные окружения установлены правильно и файл сессии создан
2. **FloodWaitError**: Если вы делаете слишком много запросов, Telegram может временно ограничить доступ. Добавьте задержки между запросами.
3. **Права доступа**: Убедитесь, что ваш аккаунт Telegram имеет доступ к нужному каналу