#!/bin/bash

# Скрипт для настройки виртуального окружения Python
# Для использования: ./setup_venv.sh
# После выполнения скрипта активируйте окружение: source venv/bin/activate

# Определение директории проекта
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

echo "Настройка виртуального окружения для проекта в $PROJECT_DIR"

# Проверка наличия Python 3
if ! command -v python3 &> /dev/null; then
    echo "Python 3 не найден. Пожалуйста, установите Python 3."
    exit 1
fi

# Удаление существующего виртуального окружения (если есть)
if [ -d "venv" ]; then
    echo "Удаление существующего виртуального окружения..."
    rm -rf venv
fi

# Создание нового виртуального окружения
echo "Создание нового виртуального окружения..."
python3 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Обновление pip
echo "Обновление pip..."
pip install --upgrade pip

# Установка зависимостей из requirements.txt, если файл существует
if [ -f "requirements.txt" ]; then
    echo "Установка зависимостей из requirements.txt..."
    pip install -r requirements.txt
else
    echo "Файл requirements.txt не найден."
    echo "Установка основных зависимостей..."
    
    # Установка основных зависимостей
    pip install flask flask-sqlalchemy apscheduler trafilatura pytrends pandas requests pytz selenium email-validator python-telegram-bot gunicorn psycopg2-binary telegram
    
    # Сохранение списка установленных пакетов в requirements.txt
    echo "Создание файла requirements.txt..."
    pip freeze > requirements.txt
fi

echo "Настройка виртуального окружения завершена."
echo "Для активации виртуального окружения выполните:"
echo "source venv/bin/activate"

# Установка прав исполнения для скриптов
echo "Установка прав исполнения для скриптов..."
chmod +x *.sh

# Проверка установки
echo "Проверка установленных пакетов:"
pip list