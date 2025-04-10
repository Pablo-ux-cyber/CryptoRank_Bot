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
  
  # Проверяем соединение с GitHub (более гибкий подход)
  echo "Testing connection to GitHub..."
  SSH_TEST=$(ssh -T git@github.com -o StrictHostKeyChecking=no 2>&1)
  
  if echo "$SSH_TEST" | grep -q "successfully authenticated" || echo "$SSH_TEST" | grep -q "You've successfully authenticated"; then
    echo "Successfully authenticated with GitHub!"
  else
    echo "Warning: Unable to verify GitHub authentication."
    echo "Output was: $SSH_TEST"
    echo ""
    echo "If you're sure your SSH key is added to GitHub, you can proceed anyway."
    read -p "Continue anyway? (y/n): " continue_anyway
    if [ "$continue_anyway" != "y" ] && [ "$continue_anyway" != "Y" ]; then
      exit 1
    fi
    echo "Continuing..."
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
  
  # Проверяем, существует ли репозиторий на GitHub
  echo "Would you like to create a new repository or use an existing one?"
  echo "1. Use existing repository (default)"
  echo "2. Create a new empty repository (will overwrite remote repository!)"
  read -p "Choose option (1/2): " repo_option
  
  if [ "$repo_option" = "2" ]; then
    echo "Creating new repository (this will overwrite any existing repository)..."
    
    # Создаем начальный коммит
    echo "Creating initial commit..."
    git add .
    git commit -m "Initial commit from server"
    
    # Используем force push для создания новой истории
    echo "Pushing to remote repository (force)..."
    git push -f origin "$GIT_BRANCH"
    
    echo "Repository created successfully."
  else
    # Пробуем получить данные из существующего репозитория
    echo "Fetching from remote repository..."
    if git fetch origin; then
      # Если ветка существует удаленно, настраиваем слежение
      if git show-ref --verify --quiet "refs/remotes/origin/$GIT_BRANCH"; then
        echo "Setting up tracking for branch $GIT_BRANCH..."
        git checkout "$GIT_BRANCH" 2>/dev/null || git checkout -b "$GIT_BRANCH"
        git branch --set-upstream-to="origin/$GIT_BRANCH" "$GIT_BRANCH" 2>/dev/null || true
        
        # Получаем изменения
        echo "Pulling latest changes..."
        git pull origin "$GIT_BRANCH" || echo "Warning: Could not pull changes. Repository might be empty."
      else
        # Если ветки нет, создаем ее
        echo "Creating new branch $GIT_BRANCH..."
        git checkout -b "$GIT_BRANCH"
      fi
      echo "Repository setup completed successfully."
    else
      echo "Warning: Failed to fetch from remote repository. Repository might be empty or not exist yet."
      echo "Would you like to initialize it? (y/n): "
      read -p "> " init_repo
      if [ "$init_repo" = "y" ] || [ "$init_repo" = "Y" ]; then
        echo "Creating initial commit..."
        git add .
        git commit -m "Initial commit from server"
        
        echo "Pushing to remote repository..."
        git push -u origin "$GIT_BRANCH" || {
          echo "Push failed. Trying force push..."
          git push -f -u origin "$GIT_BRANCH"
        }
        echo "Repository initialized successfully."
      else
        echo "Setup aborted. Please create the repository manually or try again."
        exit 1
      fi
    fi
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