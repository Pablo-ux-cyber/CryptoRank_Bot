# Инструкция по ручной синхронизации Git на сервере

Эта инструкция описывает, как настроить и использовать ручную синхронизацию кода между Replit и вашим сервером.

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

## 3. Копирование скрипта для ручной синхронизации

```bash
# Скопируйте скрипт manual_sync.sh в директорию проекта на сервере
scp manual_sync.sh user@your-server:/path/to/coinbasebot/

# Сделайте скрипт исполняемым
ssh user@your-server "chmod +x /path/to/coinbasebot/manual_sync.sh"
```

## 4. Использование скрипта для ручного обновления

Каждый раз, когда вы хотите обновить код на сервере:

```bash
# Подключитесь к серверу
ssh user@your-server

# Перейдите в директорию проекта и запустите скрипт
cd /path/to/coinbasebot
./manual_sync.sh
```

Скрипт выполнит следующие действия:
1. Проверит, есть ли новые изменения в репозитории
2. Если обновления есть, загрузит их
3. Автоматически перезапустит сервис coinbasebot
4. Сохранит лог операции в git_sync.log

## 5. Проверка статуса синхронизации

```bash
# Просмотр журнала синхронизации
tail -n 20 /path/to/coinbasebot/git_sync.log
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

## 7. Настройка на стороне Replit

1. Каждый раз после внесения изменений в Replit, делайте коммит и пуш:
   ```bash
   git add .
   git commit -m "Ваше описание изменений"
   git push origin main
   ```

2. Затем вручную запустите скрипт синхронизации на сервере для получения изменений.