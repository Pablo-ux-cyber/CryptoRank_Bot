# Диагностика проблемы с main.py на сервере

## Проблема
Сервер http://91.132.58.97:5000 недоступен после перехода на main.py

## Возможные причины

### 1. main.py не запускает веб-сервер
В отличие от scheduler_standalone.py, main.py может не содержать код запуска Flask сервера.

### 2. Порт 5000 не слушается
main.py может запускать только планировщик без веб-интерфейса.

### 3. Ошибка в main.py
Возможна ошибка при запуске, которая приводит к краху приложения.

## Команды для диагностики на сервере

```bash
# 1. Проверить статус службы
sudo systemctl status coinbasebot

# 2. Посмотреть логи службы
sudo journalctl -u coinbasebot -n 50

# 3. Проверить процессы Python
ps aux | grep python

# 4. Проверить что слушает порт 5000
sudo netstat -tlnp | grep :5000
# или
sudo ss -tlnp | grep :5000

# 5. Проверить содержимое main.py
head -20 /root/coinbaserank_bot/main.py
tail -20 /root/coinbaserank_bot/main.py

# 6. Попробовать запустить main.py вручную для диагностики
cd /root/coinbaserank_bot
source venv/bin/activate
python main.py
```

## Вероятное решение

Скорее всего нужно:

### Вариант 1: Использовать gunicorn с main.py
```ini
[Service]
ExecStart=/root/coinbaserank_bot/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 1 main:app
```

### Вариант 2: Убедиться что main.py запускает Flask
Добавить в конец main.py:
```python
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
```

### Вариант 3: Вернуться к scheduler_standalone.py если main.py только планировщик
```ini
[Service]
ExecStart=/root/coinbaserank_bot/venv/bin/python /root/coinbaserank_bot/scheduler_standalone.py
```

## Быстрая проверка
1. Посмотрите логи: `sudo journalctl -u coinbasebot -n 20`
2. Проверьте процессы: `ps aux | grep python`
3. Проверьте порт: `sudo netstat -tlnp | grep :5000`