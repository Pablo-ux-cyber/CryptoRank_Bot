#!/bin/bash

# Скрипт для настройки переменных окружения для бота
# Создает файл .env с нужными переменными

# Проверяем, что скрипт запущен с правами root
if [[ $EUID -ne 0 ]]; then
   echo "Этот скрипт должен быть запущен с правами root"
   exit 1
fi

# Определяем директорию скрипта
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ENV_FILE="$SCRIPT_DIR/.env"

# Проверяем, существует ли уже файл .env
if [ -f "$ENV_FILE" ]; then
    echo "Файл .env уже существует. Хотите перезаписать его? (y/n)"
    read -r answer
    if [[ "$answer" != "y" ]]; then
        echo "Операция отменена"
        exit 0
    fi
fi

# Запрашиваем токен бота
echo "Введите токен Telegram-бота (получите у @BotFather):"
read -r bot_token

# Запрашиваем ID канала для отправки
echo "Введите ID канала для отправки сообщений (например, @cryptorankbase):"
read -r channel_id

# Запрашиваем ID исходного канала (по умолчанию @coinbaseappstore)
echo "Введите ID исходного канала [по умолчанию: @coinbaseappstore]:"
read -r source_channel
source_channel=${source_channel:-"@coinbaseappstore"}

# Генерируем секретный ключ для сессий Flask
session_secret=$(openssl rand -hex 32)

# Создаем файл .env
cat > "$ENV_FILE" << EOF
# Файл с переменными окружения для бота
# Этот файл не должен быть добавлен в git (добавьте .env в .gitignore)

# Токен Telegram-бота
TELEGRAM_BOT_TOKEN=$bot_token

# Канал для отправки сообщений
TELEGRAM_CHANNEL_ID=$channel_id

# Канал, откуда бот получает данные о рейтинге
TELEGRAM_SOURCE_CHANNEL=$source_channel

# Секретный ключ для Flask-сессий
SESSION_SECRET=$session_secret

# Настройки Altcoin Season Index
ASI_VS_CURRENCY=usd
ASI_TOP_N=50
ASI_PERIOD=30d
EOF

# Устанавливаем правильные разрешения
chmod 600 "$ENV_FILE"

echo "Файл .env успешно создан в директории $SCRIPT_DIR"
echo "Рекомендуется перезапустить бота для применения новых настроек"