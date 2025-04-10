# Инструкция по синхронизации через SSH

## Настройка на сервере (разовая)

1. Скопируйте файл `sync.sh` в директорию `/root/coinbaserank_bot/` на сервере:

```bash
scp sync.sh root@your-server:/root/coinbaserank_bot/
```

2. Сделайте скрипт исполняемым:

```bash
ssh root@your-server "chmod +x /root/coinbaserank_bot/sync.sh"
```

3. Убедитесь, что на сервере настроен Git и указан правильный репозиторий:

```bash
ssh root@your-server "cd /root/coinbaserank_bot && git remote -v"
```

Если репозиторий не настроен, выполните:

```bash
ssh root@your-server "cd /root/coinbaserank_bot && git init && git remote add origin https://github.com/your-username/coinbasebot.git"
```

## Использование

### Синхронизация с GitHub через SSH (одной командой)

Просто выполните:

```bash
ssh root@your-server "/root/coinbaserank_bot/sync.sh"
```

Эта команда:
1. Подключится к серверу по SSH
2. Запустит скрипт синхронизации в директории `/root/coinbaserank_bot/`
3. Выполнит `git pull` для получения последних изменений
4. Перезапустит сервис coinbasebot, если были изменения

### Просмотр журнала синхронизации

```bash
ssh root@your-server "cat /root/coinbaserank_bot/sync.log | tail -n 30"
```

## Ручной запуск из Replit

Если вы хотите запускать синхронизацию прямо из Replit, вы можете создать скрипт:

```bash
# Создайте и выполните:
ssh root@your-server "/root/coinbaserank_bot/sync.sh"
```

## Советы по безопасности

1. Используйте SSH-ключи вместо паролей для безопасного доступа
2. Ограничьте права доступа к скрипту синхронизации
3. Рассмотрите возможность использования расширенных опций безопасности SSH