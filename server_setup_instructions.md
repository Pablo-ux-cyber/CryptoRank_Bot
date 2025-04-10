# Инструкция по настройке Git синхронизации на сервере

Ниже приведены шаги для настройки автоматической синхронизации кода между Replit и вашим сервером.

## 1. Настройка репозитория на сервере

```bash
# Переходим в директорию приложения на сервере
cd /path/to/coinbasebot

# Инициализируем Git, если он еще не инициализирован
git init

# Добавляем удаленный репозиторий (замените URL на ваш)
git remote add origin https://github.com/your-username/coinbasebot.git

# Создаем начальный коммит, если репозиторий новый
touch .gitignore
git add .gitignore
git commit -m "Initial commit"

# Настраиваем ветку по умолчанию
git branch -M main

# Получаем код из репозитория
git pull origin main
```

## 2. Настройка учетных данных Git

```bash
# Настройка глобальных параметров Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Для сохранения учетных данных (не требует повторного ввода пароля)
git config --global credential.helper store
```

## 3. Настройка запуска скрипта синхронизации по расписанию

```bash
# Скопируйте скрипт git_sync.sh в директорию проекта на сервере
scp git_sync.sh user@your-server:/path/to/coinbasebot/

# Сделайте скрипт исполняемым
ssh user@your-server "chmod +x /path/to/coinbasebot/git_sync.sh"

# Добавьте задание в crontab для запуска каждый час
ssh user@your-server "crontab -l > mycron"
ssh user@your-server "echo '0 * * * * /path/to/coinbasebot/git_sync.sh' >> mycron"
ssh user@your-server "crontab mycron"
ssh user@your-server "rm mycron"
```

## 4. Ручной запуск синхронизации

```bash
# Для ручного запуска синхронизации
ssh user@your-server "/path/to/coinbasebot/git_sync.sh"
```

## 5. Проверка статуса синхронизации

```bash
# Просмотр журнала синхронизации
ssh user@your-server "tail -n 20 /path/to/coinbasebot/git_sync.log"
```

## 6. Интеграция с systemd-сервисом

Убедитесь, что ваш systemd-сервис корректно настроен. Пример файла `/etc/systemd/system/coinbasebot.service`:

```ini
[Unit]
Description=Coinbase AppStore Rank Bot
After=network.target

[Service]
User=your-username
WorkingDirectory=/path/to/coinbasebot
ExecStart=/usr/bin/python3 /path/to/coinbasebot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Применение изменений в systemd:

```bash
sudo systemctl daemon-reload
sudo systemctl restart coinbasebot
```

## 7. Настройка хуков Git (опционально)

Для более продвинутой настройки вы можете использовать хуки Git:

```bash
# Создайте скрипт post-merge для автоматического перезапуска после git pull
cat > /path/to/coinbasebot/.git/hooks/post-merge << 'EOF'
#!/bin/bash
sudo systemctl restart coinbasebot
EOF

# Сделайте скрипт исполняемым
chmod +x /path/to/coinbasebot/.git/hooks/post-merge
```

## 8. Настройка на стороне Replit

1. Каждый раз после внесения изменений в Replit, делайте коммит и пуш:
   ```bash
   git add .
   git commit -m "Ваше описание изменений"
   git push origin main
   ```

2. Сервер автоматически получит эти изменения при следующем запуске скрипта синхронизации.