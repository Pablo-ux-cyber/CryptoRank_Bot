# Лучшие практики настройки cron для Telegram бота

## Рекомендуемый способ: Shell скрипт

### 1. Настройка cron через shell скрипт (РЕКОМЕНДУЕТСЯ)

```bash
# Открыть crontab
crontab -e

# Добавить задание с абсолютным путем
1 8 * * * /full/path/to/your/project/run_test_message.sh

# Или с переменными окружения
1 8 * * * cd /path/to/project && ./run_test_message.sh
```

**Преимущества:**
- ✅ Полное логирование в `/tmp/test_message_cron.log`
- ✅ Обработка ошибок и таймаутов
- ✅ Автоматическое определение IP
- ✅ Проверка доступности сервера
- ✅ Детальная диагностика

### 2. Альтернативный способ: Прямая ссылка

```bash
# НЕ рекомендуется, но возможно для простых случаев
1 8 * * * curl -s "http://$(hostname -I | awk '{print $1}'):5000/test-telegram-message" > /tmp/cron_simple.log 2>&1
```

**Недостатки:**
- ❌ Минимальные логи
- ❌ Нет обработки ошибок
- ❌ Сложно диагностировать проблемы

## Пример лучшей настройки cron

### 1. Сделать скрипт исполняемым
```bash
chmod +x /path/to/project/run_test_message.sh
```

### 2. Добавить в crontab с полным путем
```bash
crontab -e

# Добавить строку (замените путь на реальный):
1 8 * * * /home/user/coinbase-bot/run_test_message.sh

# Или с переходом в директорию:
1 8 * * * cd /home/user/coinbase-bot && ./run_test_message.sh
```

### 3. Проверить логи
```bash
# Просмотр логов cron
tail -f /tmp/test_message_cron.log

# Проверка системных логов cron
tail -f /var/log/cron
```

## Диагностика проблем

### Если cron не работает:

1. **Проверить синтаксис crontab:**
```bash
crontab -l
```

2. **Проверить права доступа:**
```bash
ls -la run_test_message.sh
# Должно быть: -rwxr-xr-x
```

3. **Тестировать скрипт вручную:**
```bash
./run_test_message.sh
```

4. **Проверить логи:**
```bash
tail -20 /tmp/test_message_cron.log
```

## Тестирование cron задач

### Временное задание для тестирования (каждые 2 минуты):
```bash
*/2 * * * * /path/to/project/run_test_message.sh
```

### После успешного теста вернуть на ежедневное выполнение:
```bash
1 8 * * * /path/to/project/run_test_message.sh
```

## Резервные варианты

### Если shell скрипт не работает, можно использовать прямой curl:
```bash
# Простой вариант с базовым логированием
1 8 * * * curl -s --max-time 300 "http://$(hostname -I | awk '{print $1}'):5000/test-telegram-message" >> /tmp/direct_cron.log 2>&1
```

Но shell скрипт остается предпочтительным вариантом для production использования.