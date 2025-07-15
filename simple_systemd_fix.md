# ПРОСТОЕ ИСПРАВЛЕНИЕ SYSTEMD

## Проблема
SystemD запускает `python main.py` → активируется `if __name__ == "__main__"` → запускается планировщик → конфликт

## Простое решение
Создать минимальный файл `run_scheduler.py` и изменить systemd на него

## Команды для сервера:

### 1. Создать простой файл планировщика
```bash
cat > /root/coinbaserank_bot/run_scheduler.py << 'EOF'
#!/usr/bin/env python3
import sys
import signal
import time

from load_dotenv import load_dotenv
load_dotenv()

from logger import logger
from scheduler import SensorTowerScheduler

scheduler = None

def signal_handler(sig, frame):
    logger.info("Stopping scheduler")
    if scheduler:
        scheduler.stop()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting scheduler via systemd")
    
    scheduler = SensorTowerScheduler()
    success = scheduler.start()
    
    if not success:
        logger.error("Failed to start scheduler")
        sys.exit(1)
    
    logger.info("Scheduler started successfully")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    logger.info("Scheduler stopped")
EOF
```

### 2. Сделать исполняемым
```bash
chmod +x /root/coinbaserank_bot/run_scheduler.py
```

### 3. Остановить сервис
```bash
sudo systemctl stop coinbasebot
```

### 4. Изменить systemd сервис
```bash
sudo sed -i 's|ExecStart=.*|ExecStart=/root/coinbaserank_bot/venv/bin/python /root/coinbaserank_bot/run_scheduler.py|' /etc/systemd/system/coinbasebot.service
```

### 5. Перезагрузить и запустить
```bash
sudo systemctl daemon-reload
sudo systemctl start coinbasebot
sudo systemctl status coinbasebot
```

### 6. Проверить логи
```bash
tail -f /root/coinbaserank_bot/sensortower_bot.log
```

## Результат
- SystemD запускает `run_scheduler.py` (ТОЛЬКО планировщик)
- main.py остается для Flask веб-интерфейса
- НЕТ конфликтов, НЕТ двойного запуска
- Один простой файл вместо сложной архитектуры