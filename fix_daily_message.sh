#!/bin/bash
# Скрипт для исправления проблемы с отправкой ежедневных сообщений
# Сохраните этот файл как fix_daily_message.sh и запустите на сервере

set -e
echo "Начало исправления проблемы с отправкой ежедневных сообщений..."

# Переходим в директорию с проектом
cd /root/coinbaserank_bot

# Создаем резервную копию файла scheduler.py
echo "Создание резервной копии scheduler.py..."
cp scheduler.py scheduler.py.backup_$(date +"%Y%m%d%H%M%S")

# Исправление 1: Добавляем обработку force_refresh в scheduler.py
echo "Исправление 1: Добавляем проверку force_refresh в scheduler.py..."
# Более безопасный подход - применим исправления с помощью файла с патчем
cat > force_refresh.patch << 'EOL'
--- scheduler.py.old    2025-05-09 12:00:00.000000000 +0000
+++ scheduler.py        2025-05-09 12:00:01.000000000 +0000
@@ -345,6 +345,12 @@
                     # Добавляем информацию о тренде в данные для отображения стрелки вниз
                     rankings_data["trend"] = {"direction": "down", "previous": self.last_sent_rank}
                 need_to_send = True
+            elif force_refresh:
+                # Если force_refresh=True, отправляем сообщение даже если рейтинг не изменился
+                logger.info(f"Рейтинг не изменился ({current_rank} = {self.last_sent_rank}), но отправляем сообщение принудительно (force_refresh=True).")
+                # Используем нейтральный тренд
+                rankings_data["trend"] = {"direction": "same", "previous": self.last_sent_rank}
+                need_to_send = True
             else:
                 logger.info(f"Рейтинг не изменился ({current_rank} = {self.last_sent_rank}). Сообщение не отправлено.")
                 need_to_send = False
EOL

# Применяем патч
echo "Применяем патч для добавления обработки force_refresh в scheduler.py..."
patch scheduler.py < force_refresh.patch

# Исправление 2: Изменение вызова run_scraping_job() с force_refresh=True
echo "Исправление 2: Добавляем force_refresh=True в планировщик..."
# Создаем второй патч для изменения вызова run_scraping_job
cat > force_refresh_schedule.patch << 'EOL'
--- scheduler.py.old    2025-05-09 12:00:00.000000000 +0000
+++ scheduler.py        2025-05-09 12:00:01.000000000 +0000
@@ -92,7 +92,8 @@
                 if update_rank:
                     try:
                         logger.info("Получение данных о рейтинге Coinbase (ежедневное обновление в 11:10)")
-                        self.run_scraping_job()
+                        # Принудительно отправляем сообщение при плановой проверке в 11:10, даже если рейтинг не изменился
+                        self.run_scraping_job(force_refresh=True)
                         self.last_rank_update_date = today
                         logger.info(f"Данные о рейтинге Coinbase успешно обновлены: {now}")
                     except Exception as e:
EOL

echo "Применяем второй патч для обновления планировщика..."
patch scheduler.py < force_refresh_schedule.patch

echo "Исправления успешно применены!"
echo "Перезапуск сервиса coinbasebot..."
sudo systemctl restart coinbasebot

echo "Готово! Теперь сообщения будут отправляться в 11:10 MSK ежедневно, даже если рейтинг не изменился."
echo "Проверьте логи: tail -f /root/coinbaserank_bot/sensortower_bot.log"