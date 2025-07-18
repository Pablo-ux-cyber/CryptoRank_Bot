# Варианты запуска в Replit

## Текущая настройка (рекомендуется оставить)
```
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

**Преимущества gunicorn:**
- ✅ Более стабильный в production
- ✅ Лучше обрабатывает множественные запросы
- ✅ Автоматический перезапуск при изменениях (--reload)
- ✅ Reuse-port для лучшей производительности

## Альтернатива: простой Python запуск

### Вариант 1: Создать отдельный workflow
Можно создать новый workflow для простого запуска через интерфейс Replit:
- В Replit IDE: Tools → Workflows → Create Workflow
- Назвать "Simple Python"
- Команда: `python main.py`

### Вариант 2: Ручной запуск из терминала
```bash
# Остановить текущий workflow и запустить вручную
python main.py
```

### Вариант 3: Изменить main.py для прямого запуска
```python
# В конце main.py добавить:
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

## Проверка текущего процесса

### Текущие процессы:
```bash
ps aux | grep -E "gunicorn|python|flask" | grep -v grep
```

### Убить текущий процесс (если нужно):
```bash
pkill -f gunicorn
# или
pkill -f "python main.py"
```

## Рекомендация

**Оставьте gunicorn** - он лучше подходит для production использования:
1. Более стабильный
2. Лучше обрабатывает нагрузку
3. Автоматически перезапускается при ошибках
4. Имеет встроенный reload при изменениях кода

Если нужен простой запуск для отладки, используйте терминал:
```bash
python main.py
```

## Для cron использования

Независимо от способа запуска веб-сервера, ваши cron скрипты будут работать одинаково:
```bash
# Обращаются к серверу по HTTP
curl http://IP:5000/test-telegram-message
```

Тип сервера (gunicorn или python) не влияет на HTTP API.