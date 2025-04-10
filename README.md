# Coinbase App Rank Tracker Bot

Telegram бот для отслеживания рейтинга приложения Coinbase в App Store, анализа индекса страха и жадности (Fear & Greed Index) и мониторинга настроений рынка с помощью Google Trends Pulse.

## Возможности

- 📊 Отслеживание позиции Coinbase в рейтинге App Store
- 📈 Анализ индекса страха и жадности криптовалютного рынка
- 🔍 Мониторинг трендов поиска в Google для выявления рыночных настроений
- 🔔 Отправка уведомлений в Telegram при изменении рейтинга
- 🌐 Веб-интерфейс для управления и мониторинга

## Цветовая схема сигналов

Бот использует единую цветовую схему для обоих индикаторов (Fear & Greed и Google Trends Pulse):

- 🔴 Красный: высокий страх на рынке - потенциальная точка входа
- 🟠 Оранжевый: снижающийся интерес, преобладание осторожности
- 🟡 Жёлтый: нейтральные рыночные настроения
- 🟢 Зелёный: высокий FOMO-фактор - возможный пик рынка
- 🔵 Синий: рынок в спячке - крайне низкий интерес

## Установка на сервер

### Требования

- Python 3.7+
- Systemd (для управления сервисом на Linux)
- Доступ к Git

### Первоначальная настройка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-username/coinbasebot.git
   cd coinbasebot
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Настройте переменные окружения:
   ```bash
   export TELEGRAM_BOT_TOKEN="ваш_токен_бота"
   export TELEGRAM_CHANNEL_ID="ваш_id_канала"
   export SESSION_SECRET="секретный_ключ_сессии"
   ```

4. Настройте сервис systemd:
   ```bash
   # Скопируйте файл сервиса
   sudo cp coinbasebot.service /etc/systemd/system/
   
   # Отредактируйте пути и переменные окружения
   sudo nano /etc/systemd/system/coinbasebot.service
   
   # Активируйте и запустите сервис
   sudo systemctl daemon-reload
   sudo systemctl enable coinbasebot
   sudo systemctl start coinbasebot
   ```

### Настройка ручной синхронизации с Git

1. Сделайте скрипт исполняемым:
   ```bash
   chmod +x manual_sync.sh
   ```

2. Настройте Git:
   ```bash
   ./initial_git_setup.sh https://github.com/your-username/coinbasebot.git
   ```

3. Для синхронизации кода после изменений в репозитории:
   ```bash
   ./manual_sync.sh
   ```

Более подробные инструкции доступны в файле `manual_sync_instructions.md`.

## Использование

### Веб-интерфейс

Веб-интерфейс доступен на порту 5000. Перейдите по адресу `http://ваш_сервер:5000/` для доступа к управлению ботом.

### Команды для управления

- `/start` - запустить бота в Telegram
- `/stats` - получить текущую статистику
- `/refresh` - принудительно обновить данные

## Разработка

Для разработки используйте:

```bash
# Запуск в режиме отладки
python main.py
```

## Git синхронизация

Инструкции по настройке Git синхронизации между Replit и вашим сервером смотрите в файле `server_setup_instructions.md`.

## Лицензия

MIT