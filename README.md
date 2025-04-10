# Coinbase Rank Telegram Bot

Телеграм-бот для автоматического отслеживания рейтинга приложения Coinbase в App Store, индекса страха и жадности криптовалютного рынка, и пульса Google Trends.

## Функциональность

- 📊 Мониторинг рейтинга приложения Coinbase в App Store из Telegram-канала @coinbaseappstore
- 📈 Отслеживание индекса страха и жадности (Fear & Greed Index) криптовалютного рынка
- 🔍 Анализ Google Trends для определения тенденций интереса к криптовалютам
- 📱 Отправка уведомлений в Telegram-канал @cryptorankbase при изменении рейтинга
- 🌐 Веб-интерфейс для управления ботом и ручного запуска задач

## Технические особенности

- 🔄 Периодические проверки каждые 5 минут
- 🔔 Отправка уведомлений только при изменении рейтинга (предотвращение спама)
- 🚀 Возможность принудительной отправки сообщений через веб-интерфейс
- 🔒 Поддержка файловой блокировки для предотвращения параллельного запуска нескольких экземпляров
- 📋 Хранение истории рейтингов между перезапусками
- ⚙️ Интеграция с systemd для автоматического запуска и перезапуска

## Установка и настройка

### Зависимости

```bash
pip install flask telegram python-telegram-bot requests pytrends apscheduler
```

### Переменные окружения

Создайте файл `.env` в корневой директории проекта:

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=@your_channel_id_or_group_id
SESSION_SECRET=your_secret_key
```

### Настройка systemd-сервиса

```bash
sudo nano /etc/systemd/system/coinbasebot.service

[Unit]
Description=Coinbase Rank Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/coinbaserank_bot
ExecStart=/root/coinbaserank_bot/venv/bin/python /root/coinbaserank_bot/main.py
Restart=always
RestartSec=10
Environment=TELEGRAM_BOT_TOKEN=your_bot_token
Environment=TELEGRAM_CHANNEL_ID=@your_channel_id
Environment=SESSION_SECRET=your_secret_key

[Install]
WantedBy=multi-user.target
```

### Активация и запуск сервиса

```bash
sudo systemctl daemon-reload
sudo systemctl enable coinbasebot
sudo systemctl start coinbasebot
```

## Использование

### Веб-интерфейс

Веб-интерфейс доступен по адресу `http://your_server_ip:5000/`

### Проверка статуса

```bash
sudo systemctl status coinbasebot
```

### Просмотр логов

```bash
tail -f /var/log/coinbasebot.log
```

### Синхронизация с GitHub

Проект поддерживает автоматическую синхронизацию с GitHub. При обновлении кода в репозитории, выполните:

```bash
cd /root/coinbaserank_bot
./sync.sh
```

## Обновления от 10 апреля 2025

- ✅ Исправлено отображение статуса бота в веб-интерфейсе
- ✅ Улучшена визуализация данных Google Trends Pulse
- ✅ Отправка комбинированных сообщений с рейтингом, FGI и Google Trends
- ✅ Все сообщения и комментарии переведены на английский язык