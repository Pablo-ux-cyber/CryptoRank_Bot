# Руководство по синхронизации через SSH

Это руководство объясняет, как настроить и использовать SSH для синхронизации кода между вашей локальной машиной/Replit и удаленным сервером.

## Предварительные требования

1. **SSH-доступ к серверу** - Вам нужен пользователь с SSH-доступом и правами на запуск `sudo` команд
2. **rsync** - Установлен на локальной машине (обычно предустановлен на Linux/Mac, для Windows используйте WSL или Git Bash)
3. **systemd** - На сервере для управления сервисом бота

## Базовая синхронизация (ssh_sync.sh)

### Шаг 1: Настройка SSH-ключей (рекомендуется, но необязательно)

```bash
# Сгенерировать SSH ключ, если у вас его еще нет
ssh-keygen -t rsa -b 4096

# Скопировать ключ на сервер для беспарольного входа
ssh-copy-id user@your-server
```

### Шаг 2: Сделайте скрипт исполняемым

```bash
chmod +x ssh_sync.sh
```

### Шаг 3: Запустите синхронизацию

```bash
./ssh_sync.sh user@your-server /path/to/coinbasebot
```

Этот скрипт:
1. Проверит, есть ли несохраненные изменения в Git
2. Скопирует файлы проекта на сервер с помощью rsync
3. Перезапустит сервис coinbasebot на сервере

## Продвинутая синхронизация (ssh_sync_advanced.sh)

Продвинутый скрипт предлагает больше опций и более удобный интерфейс.

### Сделайте скрипт исполняемым

```bash
chmod +x ssh_sync_advanced.sh
```

### Использование с разными параметрами

#### Базовое использование:

```bash
./ssh_sync_advanced.sh -s user@your-server -p /path/to/coinbasebot
```

#### С указанием SSH-ключа:

```bash
./ssh_sync_advanced.sh -s user@your-server -p /path/to/coinbasebot -k ~/.ssh/id_rsa
```

#### Без перезапуска сервиса:

```bash
./ssh_sync_advanced.sh -s user@your-server -p /path/to/coinbasebot -r no
```

#### Полный пример:

```bash
./ssh_sync_advanced.sh -s root@123.45.67.89 -p /home/user/coinbasebot -k ~/.ssh/my_server_key -r yes
```

## Настройка сервера для приема синхронизации

### 1. Настройка каталога проекта

На сервере выполните:

```bash
# Создайте директорию для проекта
mkdir -p /path/to/coinbasebot

# Установите корректные права
chown -R your-user:your-group /path/to/coinbasebot
chmod -R 755 /path/to/coinbasebot
```

### 2. Первоначальная настройка systemd

```bash
# Копируем файл сервиса
sudo cp /path/to/coinbasebot/coinbasebot.service /etc/systemd/system/

# Редактируем файл сервиса, указывая правильные пути и переменные окружения
sudo nano /etc/systemd/system/coinbasebot.service

# Применяем изменения
sudo systemctl daemon-reload
sudo systemctl enable coinbasebot
```

### 3. Установка зависимостей

После первой синхронизации установите необходимые зависимости:

```bash
cd /path/to/coinbasebot
pip install -r requirements.txt
```

## Решение проблем

### Ошибка доступа SSH

Если вы получаете ошибку доступа:

```bash
# Проверьте SSH соединение
ssh user@your-server

# Установите правильные права для SSH ключа
chmod 600 ~/.ssh/id_rsa
```

### Ошибка при перезапуске сервиса

Если вы получаете ошибку при перезапуске сервиса, проверьте:

```bash
# Проверьте статус сервиса
sudo systemctl status coinbasebot

# Проверьте журнал systemd
sudo journalctl -u coinbasebot -n 50

# Проверьте права пользователя на запуск sudo без пароля
sudo visudo
```

Добавьте в файл sudoers:
```
your-user ALL=(ALL) NOPASSWD: /bin/systemctl restart coinbasebot
```

## Автоматизация синхронизации в Replit

Вы можете запускать скрипт синхронизации прямо из Replit:

1. Убедитесь, что у вас есть доступ к приватному SSH-ключу в Replit
2. Используйте секреты Replit для хранения пароля или ключа
3. Вызывайте `./ssh_sync.sh` или `./ssh_sync_advanced.sh` для синхронизации

## Заключение

SSH-синхронизация обеспечивает безопасный и эффективный способ обновления кода на вашем сервере. Вы можете настроить ее под ваши конкретные потребности, изменяя параметры rsync или добавляя дополнительные шаги в скрипт синхронизации.