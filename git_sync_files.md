# ФАЙЛЫ ДЛЯ СИНХРОНИЗАЦИИ С GIT

## Основные исправленные файлы

### 1. scheduler.py
**Что изменено:** Эффективный планировщик который спит до точного времени 08:01 UTC
```bash
# Скопировать на сервер:
cp scheduler.py /root/coinbaserank_bot/scheduler.py
```

### 2. main.py  
**Что изменено:** Убран автоматический запуск планировщика из Flask приложения
```bash
# Скопировать на сервер:
cp main.py /root/coinbaserank_bot/main.py
```

## Вспомогательные файлы (опционально)

### 3. server_update_instructions.md
**Для чего:** Инструкции по обновлению на сервере

### 4. server_fix_scheduler_timing.py  
**Для чего:** Автоматический скрипт исправления планировщика

### 5. fix_main_py_manually.txt
**Для чего:** Ручные инструкции для изменения main.py

## Команды для Git синхронизации

### На вашем локальном компьютере:
```bash
git add scheduler.py main.py
git commit -m "Fix scheduler timing and remove double scheduler startup"
git push origin main
```

### На сервере:
```bash
cd /root/coinbaserank_bot
git pull origin main
sudo systemctl restart coinbasebot
```

## Альтернативный способ (без Git)

Если Git не настроен, скопируйте файлы вручную:

```bash
# Скачать файлы с этого Replit проекта
wget https://replit.com/your-project/scheduler.py -O /root/coinbaserank_bot/scheduler.py
wget https://replit.com/your-project/main.py -O /root/coinbaserank_bot/main.py

# Перезапустить сервис
sudo systemctl restart coinbasebot
```

## Проверка после обновления

```bash
# Проверить статус
sudo systemctl status coinbasebot

# Проверить логи  
tail -f /root/coinbaserank_bot/sensortower_bot.log
```

**Ожидаемый результат в логах:**
```
Следующий запуск запланирован на: 2025-07-16 08:01:00 (через X часов Y минут)
Планировщик спит 60 минут до следующей проверки
Flask app initialized without starting scheduler - scheduler should be started externally
```

**БЕЗ ошибок:** "Другой экземпляр бота уже запущен"