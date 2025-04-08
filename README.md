# SensorTower Rankings Bot

Телеграм-бот, который собирает данные о категориях рейтингов приложения из SensorTower и отправляет их в канал Telegram.

## Описание

Этот проект представляет собой автоматизированный скрипт, который:

1. Ежедневно собирает данные о рейтингах приложения в категориях из SensorTower
2. Форматирует их в удобный для чтения формат
3. Отправляет сообщение в указанный Telegram-канал

По умолчанию настроен для отслеживания рейтингов приложения Coinbase (App ID: 886427730) в США.

## Технические детали

Проект использует следующие технологии:

- Python 3.10+
- Flask для веб-интерфейса
- Selenium и Trafilatura для скрапинга данных
- python-telegram-bot для отправки сообщений
- Многопоточность для параллельного запуска планировщика

## Настройка

Для работы проекта необходимо настроить следующие переменные окружения:

- `TELEGRAM_BOT_TOKEN` - токен вашего Telegram-бота, полученный от @BotFather
- `TELEGRAM_CHANNEL_ID` - идентификатор канала, куда будут отправляться сообщения (например: `@yourchannel` или численный ID)
- `SESSION_SECRET` - секретный ключ для Flask-сессий (любая случайная строка)

## Запуск

Проект запускается автоматически при запуске сервера. Для ручного управления используйте веб-интерфейс, доступный по адресу:

```
http://localhost:5000
```

## Веб-интерфейс

Веб-интерфейс предоставляет следующие возможности:

- Просмотр текущего статуса бота
- Ручной запуск скрапинга данных
- Просмотр логов
- Тестирование подключения к Telegram

## Логи

Логи сохраняются в файл `sensortower_bot.log` и доступны через веб-интерфейс.

## Расписание

По умолчанию бот запускается ежедневно. Время запуска можно настроить в файле `config.py`, изменив параметры `SCHEDULE_HOUR` и `SCHEDULE_MINUTE`.

## Тестирование

Чтобы проверить, правильно ли настроен бот:

1. Откройте веб-интерфейс
2. Нажмите кнопку "Test Telegram Connection"
3. Проверьте, получили ли вы тестовое сообщение в вашем Telegram-канале

## Примечания

- Если у бота нет доступа к каналу, он попытается отправить сообщение напрямую администратору бота (первому пользователю, который отправил сообщение боту)
- Для скрапинга используется комбинация Selenium и Trafilatura, с несколькими резервными методами для повышения надежности
- В случае, если не удается получить данные с SensorTower, бот сгенерирует тестовые данные