# КОМАНДЫ ДЛЯ ДИАГНОСТИКИ ПРОБЛЕМЫ

## 1. Проверить systemd сервис
```bash
sudo systemctl cat coinbasebot
```

## 2. Проверить что запускается
```bash
ps aux | grep python
```

## 3. Проверить содержимое main.py на сервере
```bash
grep -A 10 -B 10 "Starting scheduler at app initialization" /root/coinbaserank_bot/main.py
```

## 4. Проверить содержимое конца main.py
```bash
tail -20 /root/coinbaserank_bot/main.py
```

## 5. Временное решение - убрать строку из main.py
```bash
sed -i 's/logger.info("Starting scheduler at app initialization")/# logger.info("Starting scheduler at app initialization")/' /root/coinbaserank_bot/main.py
```

## 6. Перезапустить сервис
```bash
sudo systemctl restart coinbasebot
```