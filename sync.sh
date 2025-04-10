#!/bin/bash

# Скрипт для ручной синхронизации репозитория между Replit и сервером через SSH
# Путь: /root/coinbaserank_bot/sync.sh
# Использование: 
#   ./sync.sh push - отправить изменения с сервера в GitHub
#   ./sync.sh pull - получить изменения с GitHub на сервер
#   ./sync.sh - вывести справку

# Настройки
PROJECT_DIR="/root/coinbaserank_bot"
REPLIT_GIT_URL="git@github.com:replicrank/coinbaserank_bot.git" # Используем SSH URL для безопасного подключения
GIT_BRANCH="main"
COMMIT_MESSAGE="Manual sync from server $(date '+%Y-%m-%d %H:%M:%S')"

# Файлы, которые не нужно синхронизировать (логи, временные файлы и т.д.)
EXCLUDE_FILES=(
  "sensortower_bot.log"
  "*.pyc"
  "__pycache__"
  ".env"
  ".venv"
  "venv"
  "*.log"
)

# Создаем .gitignore, если его нет
create_gitignore() {
  if [ ! -f "$PROJECT_DIR/.gitignore" ]; then
    echo "Creating .gitignore file..."
    for file in "${EXCLUDE_FILES[@]}"; do
      echo "$file" >> "$PROJECT_DIR/.gitignore"
    done
    echo "/tmp/coinbasebot_rank_history.txt" >> "$PROJECT_DIR/.gitignore"
    echo "/tmp/coinbasebot.lock" >> "$PROJECT_DIR/.gitignore"
    echo ".gitignore created successfully."
  fi
}

# Функция для проверки конфигурации SSH
check_ssh_config() {
  if [ ! -f ~/.ssh/id_rsa ]; then
    echo "SSH key not found. Creating SSH key..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    echo "SSH key created. Please add this public key to your GitHub account:"
    cat ~/.ssh/id_rsa.pub
    echo ""
    echo "After adding the key to GitHub, press Enter to continue..."
    read -r
  fi
  
  # Проверяем соединение с GitHub
  if ! ssh -T git@github.com -o StrictHostKeyChecking=no 2>&1 | grep -q "successfully authenticated"; then
    echo "Failed to authenticate with GitHub. Please make sure your SSH key is added to GitHub."
    exit 1
  fi
}

# Функция для извлечения изменений из GitHub на сервер
pull_changes() {
  echo "Pulling changes from GitHub to server..."
  cd "$PROJECT_DIR" || exit
  create_gitignore
  
  # Проверка наличия локальных изменений
  if ! git diff --quiet; then
    echo "Local changes detected. Stashing changes..."
    git stash save "Temporary save before pull $(date '+%Y-%m-%d %H:%M:%S')"
    local_changes=true
  else
    local_changes=false
  fi
  
  # Извлечение изменений
  git pull origin "$GIT_BRANCH"
  
  # Возвращаем локальные изменения, если они есть
  if [ "$local_changes" = true ]; then
    echo "Reapplying local changes..."
    git stash pop || echo "Could not reapply changes. Please resolve conflicts manually."
  fi
  
  echo "Pull completed. Current branch is now at $(git rev-parse --short HEAD)"
  
  read -p "Do you want to restart the coinbasebot service? (y/n): " restart
  if [ "$restart" = "y" ] || [ "$restart" = "Y" ]; then
    echo "Restarting coinbasebot service..."
    sudo systemctl restart coinbasebot
    echo "Service restarted."
  fi
}

# Функция для отправки изменений с сервера в GitHub
push_changes() {
  echo "Pushing changes from server to GitHub..."
  cd "$PROJECT_DIR" || exit
  create_gitignore
  
  # Добавляем все файлы, кроме исключенных в .gitignore
  git add .
  
  # Проверяем, есть ли изменения для коммита
  if git diff --staged --quiet; then
    echo "No changes to commit"
    return
  fi
  
  # Запрашиваем описание коммита
  read -p "Enter commit message (or press Enter to use default): " custom_message
  if [ -n "$custom_message" ]; then
    COMMIT_MESSAGE="$custom_message"
  fi
  
  # Создаем коммит и отправляем изменения
  git commit -m "$COMMIT_MESSAGE"
  git push origin "$GIT_BRANCH"
  
  echo "Changes pushed to GitHub successfully."
}

# Функция для вывода справки
show_help() {
  echo "Usage: ./sync.sh [command]"
  echo ""
  echo "Commands:"
  echo "  push    - Push changes from server to GitHub"
  echo "  pull    - Pull changes from GitHub to server"
  echo "  setup   - Initialize Git repository and SSH keys"
  echo "  help    - Show this help message"
  echo ""
  echo "If no command is specified, this help message is displayed."
}

# Функция для первоначальной настройки Git и SSH
setup_repository() {
  echo "Setting up Git repository and SSH keys..."
  cd "$PROJECT_DIR" || exit
  
  # Создаем SSH ключи, если их нет
  check_ssh_config
  
  # Создаем .gitignore
  create_gitignore
  
  # Инициализируем Git, если нужно
  if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    git remote add origin "$REPLIT_GIT_URL"
  else
    echo "Git repository already initialized."
    # Проверяем, правильный ли remote URL
    current_url=$(git remote get-url origin 2>/dev/null || echo "")
    if [ "$current_url" != "$REPLIT_GIT_URL" ]; then
      echo "Updating remote URL..."
      git remote set-url origin "$REPLIT_GIT_URL" || git remote add origin "$REPLIT_GIT_URL"
    fi
  fi
  
  # Пробуем получить данные из репозитория
  echo "Fetching from remote repository..."
  if git fetch origin; then
    # Если ветка существует удаленно, настраиваем слежение
    if git show-ref --verify --quiet "refs/remotes/origin/$GIT_BRANCH"; then
      echo "Setting up tracking for branch $GIT_BRANCH..."
      git checkout "$GIT_BRANCH" || git checkout -b "$GIT_BRANCH"
      git branch --set-upstream-to="origin/$GIT_BRANCH" "$GIT_BRANCH"
    else
      # Если ветки нет, создаем ее
      echo "Creating new branch $GIT_BRANCH..."
      git checkout -b "$GIT_BRANCH"
    fi
    echo "Repository setup completed successfully."
  else
    echo "Failed to fetch from remote repository. Make sure your SSH key is added to GitHub and the repository exists."
    exit 1
  fi
}

# Главный скрипт
cd "$PROJECT_DIR" || exit

case "$1" in
  push)
    check_ssh_config
    push_changes
    ;;
  pull)
    check_ssh_config
    pull_changes
    ;;
  setup)
    setup_repository
    ;;
  help|"")
    show_help
    ;;
  *)
    echo "Unknown command: $1"
    show_help
    exit 1
    ;;
esac