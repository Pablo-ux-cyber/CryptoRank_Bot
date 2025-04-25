# Инструкции для решения проблемы с отправкой сообщений

Проблема: сообщения не отправляются в запланированное время (11:10) из-за файла блокировки `manual_operation.lock`.

## Немедленное решение

1. Удалите файл блокировки ручной операции:

```bash
rm /root/coinbaserank_bot/manual_operation.lock
```

2. Перезапустите сервис бота (если он запущен как systemd-сервис):

```bash
sudo systemctl restart coinbasebot
```

## Обновление кода

1. Скопируйте обновленные файлы на сервер:
   * `scheduler.py` - улучшенная обработка файлов блокировки
   * `check_and_remove_locks.py` - новый скрипт для проверки и удаления блокировок

2. Сделайте скрипт проверки блокировок исполняемым:

```bash
chmod +x /root/coinbaserank_bot/check_and_remove_locks.py
```

3. Запустите скрипт для проверки текущего состояния блокировок:

```bash
cd /root/coinbaserank_bot
./check_and_remove_locks.py
```

4. Для принудительного удаления всех блокировок используйте:

```bash
./check_and_remove_locks.py --force
```

## Автоматизация проверки

Чтобы предотвратить подобные проблемы в будущем, можно добавить задание cron, которое будет периодически проверять и удалять устаревшие блокировки:

```bash
# Открыть редактор cron
crontab -e

# Добавить строку для запуска скрипта каждый час
0 * * * * cd /root/coinbaserank_bot && ./check_and_remove_locks.py >> /root/coinbaserank_bot/lockcheck.log 2>&1
```

## Проверка работы планировщика

Для проверки, что планировщик правильно определяет время запуска, можно вручную выполнить задание:

```bash
cd /root/coinbaserank_bot
source venv/bin/activate
python3 -c "from scheduler import SensorTowerScheduler; scheduler = SensorTowerScheduler(); scheduler.start(); scheduler.run_now(force_send=True); scheduler.stop()"
```

## Проверка часового пояса

Убедитесь, что сервер использует правильный часовой пояс (MSK):

```bash
# Проверить текущее время
date

# Если нужно установить часовой пояс MSK
sudo timedatectl set-timezone Europe/Moscow
```