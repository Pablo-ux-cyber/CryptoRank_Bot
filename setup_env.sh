#!/bin/bash
# Скрипт для настройки переменных окружения для бота
# Запускайте его перед запуском бота: source setup_env.sh

# Переменные для Telegram-бота
export TELEGRAM_BOT_TOKEN="7973595268:AAG_Pz_xZFnAXRHtVbTH5Juo8qtssPUof8E"
export TELEGRAM_CHANNEL_ID="@cryptorankbase" 
export TELEGRAM_SOURCE_CHANNEL="@coinbaseappstore"

# Настройки Altcoin Season Index
export ASI_VS_CURRENCY="usd"
export ASI_TOP_N="50"
export ASI_PERIOD="30d"

echo "Переменные окружения успешно настроены для бота"
echo "TELEGRAM_CHANNEL_ID установлен на: $TELEGRAM_CHANNEL_ID"