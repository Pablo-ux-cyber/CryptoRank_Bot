#!/bin/bash

# Продвинутый скрипт для синхронизации кода с сервером через SSH
# Используйте: ./ssh_sync_advanced.sh -s user@your-server -p /path/to/coinbasebot [-k /path/to/ssh_key] [-r yes/no]

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Переменные по умолчанию
SERVER=""
REMOTE_PATH=""
SSH_KEY=""
RESTART_SERVICE="yes"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Функция вывода сообщений
log_message() {
    local level=$1
    local message=$2
    
    case "$level" in
        "info")
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        "success")
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        "warning")
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
        "error")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        *)
            echo "$message"
            ;;
    esac
}

# Функция вывода помощи
show_help() {
    echo "Использование: $0 [опции]"
    echo "Опции:"
    echo "  -s, --server     SSH-адрес сервера (например, user@123.45.67.89)"
    echo "  -p, --path       Путь к папке проекта на сервере"
    echo "  -k, --key        Путь к SSH-ключу (необязательно)"
    echo "  -r, --restart    Перезапускать сервис (yes/no, по умолчанию yes)"
    echo "  -h, --help       Показать эту справку"
    echo
    echo "Пример: $0 -s root@123.45.67.89 -p /home/user/coinbasebot -k ~/.ssh/id_rsa -r yes"
}

# Парсинг параметров
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -s|--server) SERVER="$2"; shift ;;
        -p|--path) REMOTE_PATH="$2"; shift ;;
        -k|--key) SSH_KEY="$2"; shift ;;
        -r|--restart) RESTART_SERVICE="$2"; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) log_message "error" "Неизвестный параметр: $1"; show_help; exit 1 ;;
    esac
    shift
done

# Проверка обязательных параметров
if [ -z "$SERVER" ]; then
    log_message "error" "Не указан сервер (параметр -s)"
    show_help
    exit 1
fi

if [ -z "$REMOTE_PATH" ]; then
    log_message "error" "Не указан путь на сервере (параметр -p)"
    show_help
    exit 1
fi

# Формируем SSH команду
SSH_CMD="ssh"
RSYNC_CMD="rsync -avz"

# Добавляем SSH-ключ, если он указан
if [ ! -z "$SSH_KEY" ]; then
    SSH_CMD="$SSH_CMD -i $SSH_KEY"
    RSYNC_CMD="$RSYNC_CMD -e 'ssh -i $SSH_KEY'"
fi

log_message "info" "[$TIMESTAMP] Начало синхронизации с сервером $SERVER"

# Проверяем, есть ли несохраненные изменения
if [ -n "$(git status --porcelain)" ]; then
    log_message "warning" "Обнаружены несохраненные изменения в локальном репозитории."
    echo "Рекомендуется сначала сделать коммит:"
    echo "  git add ."
    echo "  git commit -m \"Ваше сообщение\""
    echo "  git push origin main"
    
    read -p "Продолжить синхронизацию без коммита изменений? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_message "info" "[$TIMESTAMP] Синхронизация отменена."
        exit 1
    fi
fi

# Запускаем rsync для синхронизации файлов (исключая .git и другие служебные файлы)
log_message "info" "[$TIMESTAMP] Копирование файлов на сервер $SERVER..."

# Выполняем rsync
eval $RSYNC_CMD --exclude \'.git\' --exclude \'venv\' --exclude \'__pycache__\' \
       --exclude \'*.pyc\' --exclude \'*.log\' --exclude \'.DS_Store\' \
       --exclude \'manual_sync.sh\' --exclude \'ssh_sync*.sh\' \
       --exclude \'.replit\' --exclude \'replit.nix\' \
       . $SERVER:$REMOTE_PATH

# Проверяем результат rsync
if [ $? -eq 0 ]; then
    log_message "success" "[$TIMESTAMP] Файлы успешно скопированы на сервер."
    
    # Перезапускаем сервис на сервере, если требуется
    if [ "$RESTART_SERVICE" = "yes" ]; then
        log_message "info" "[$TIMESTAMP] Перезапуск сервиса coinbasebot..."
        $SSH_CMD $SERVER "cd $REMOTE_PATH && sudo systemctl restart coinbasebot"
        
        if [ $? -eq 0 ]; then
            log_message "success" "[$TIMESTAMP] Сервис успешно перезапущен."
        else
            log_message "error" "[$TIMESTAMP] Возникла ошибка при перезапуске сервиса."
        fi
    else
        log_message "info" "[$TIMESTAMP] Перезапуск сервиса пропущен по запросу пользователя."
    fi
else
    log_message "error" "[$TIMESTAMP] Ошибка при копировании файлов на сервер."
    exit 1
fi

log_message "success" "[$TIMESTAMP] Синхронизация завершена успешно."