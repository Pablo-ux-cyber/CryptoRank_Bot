#!/bin/bash

# Скрипт для автоматической замены YOUR_SERVER_IP на реальный IP адрес

# Получить текущий IP адрес сервера
SERVER_IP=$(hostname -I | awk '{print $1}')

if [ -z "$SERVER_IP" ]; then
    echo "❌ Не удалось определить IP адрес автоматически"
    echo "💡 Введите IP адрес вручную:"
    read -p "IP адрес сервера: " SERVER_IP
fi

echo "🔧 Настройка IP адреса: $SERVER_IP"
echo ""

# Заменить YOUR_SERVER_IP в файлах
files_to_update=(
    "run_test_message.sh"
    "quick_test.sh"
    "cron_setup_instructions.md"
)

for file in "${files_to_update[@]}"; do
    if [ -f "$file" ]; then
        sed -i "s/YOUR_SERVER_IP/$SERVER_IP/g" "$file"
        echo "✅ Обновлен $file"
    else
        echo "⚠️  Файл $file не найден"
    fi
done

echo ""
echo "🎉 Настройка завершена!"
echo "📍 URL для тестирования: http://$SERVER_IP:5000/test-telegram-message"
echo ""
echo "🚀 Теперь можете запустить:"
echo "   ./quick_test.sh"
echo "   или настроить cron согласно cron_setup_instructions.md"