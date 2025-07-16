import os
import threading
import time
import subprocess
from datetime import datetime, timedelta

from logger import logger
from scraper import SensorTowerScraper
from telegram_bot import TelegramBot
from telegram_bot_sync import TelegramBotSync
from fear_greed_index import FearGreedIndexTracker
from altcoin_season_index import AltcoinSeasonIndex
from market_breadth_indicator import MarketBreadthIndicator

class SensorTowerScheduler:
    def __init__(self):
        # Instead of using APScheduler, create a simple threading-based scheduler
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        self.scraper = SensorTowerScraper()
        # ИСПРАВЛЕНИЕ: Используем синхронную версию для планировщика  
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
        self.telegram_bot = TelegramBotSync(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID)
        self.fear_greed_tracker = FearGreedIndexTracker()
        self.altcoin_season_index = AltcoinSeasonIndex()
        self.market_breadth = MarketBreadthIndicator()
        
        # Определяем пути для хранения данных непосредственно в директории бота вместо /tmp
        # Используем корневую директорию бота для файлов истории
        self.data_dir = os.path.dirname(os.path.abspath(__file__))
        self.rank_history_file = os.path.join(self.data_dir, "rank_history.txt")
        logger.info(f"Файл истории рейтинга будет храниться по пути: {self.rank_history_file}")
        
        # Пытаемся загрузить последний отправленный рейтинг из файла
        try:
            if os.path.exists(self.rank_history_file):
                with open(self.rank_history_file, "r") as f:
                    saved_rank = f.read().strip()
                    if saved_rank and saved_rank.isdigit():
                        self.last_sent_rank = int(saved_rank)
                        logger.info(f"Загружен предыдущий рейтинг из файла: {self.last_sent_rank}")
                    else:
                        self.last_sent_rank = None
            else:
                self.last_sent_rank = None
        except Exception as e:
            logger.error(f"Ошибка при чтении файла истории рейтинга: {str(e)}")
            self.last_sent_rank = None
            
        self.lockfile = None  # Для блокировки файла (предотвращения запуска нескольких экземпляров)
    
    def run_rnk_script(self):
        """
        Запускает файл rnk.py в 7:59 MSK (4:59 UTC)
        """
        try:
            logger.info("Запуск файла rnk.py...")
            
            # Запускаем rnk.py
            result = subprocess.run([
                "python3", "rnk.py"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info("rnk.py выполнен успешно")
                if result.stdout:
                    logger.info(f"Вывод rnk.py: {result.stdout.strip()}")
            else:
                logger.error(f"rnk.py завершился с ошибкой (код {result.returncode})")
                if result.stderr:
                    logger.error(f"Ошибка rnk.py: {result.stderr.strip()}")
                    
        except subprocess.TimeoutExpired:
            logger.error("rnk.py превысил время ожидания (120 секунд)")
        except Exception as e:
            logger.error(f"Ошибка при запуске rnk.py: {str(e)}")
    
    def _scheduler_loop(self):
        """
        The main scheduler loop that runs in a background thread.
        - ИСПРАВЛЕНО: Собирает ВСЕ данные включая рейтинг НЕПОСРЕДСТВЕННО в момент отправки в 8:01 UTC
        - Данные рейтинга загружаются через rnk.py прямо перед отправкой для максимальной актуальности
        - Все данные собираются за один раз и отправляются одним сообщением
        """
        # Переменные для отслеживания, когда последний раз обновлялись данные
        self.last_rank_update_date = None
        self.last_rnk_update_date = None
        
        # При запуске не будем загружать данные Google Trends - получим их вместе с общим обновлением
        logger.info("ИСПРАВЛЕНО: Планировщик запущен, ПОЛНЫЙ сбор данных + отправка в 11:01 MSK (без предварительного сбора в 10:59)")
        
        while not self.stop_event.is_set():
            try:
                # Текущее время и дата
                now = datetime.now()
                today = now.date()
                
                # Вычисляем время до следующего запуска (08:01 UTC = 11:01 MSK)
                target_hour = 8
                target_minute = 1
                
                # Создаем целевое время на сегодня
                target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                
                # Если целевое время уже прошло сегодня, планируем на завтра
                if now >= target_time:
                    target_time = target_time.replace(day=target_time.day + 1)
                
                # Вычисляем количество секунд до целевого времени
                time_diff = (target_time - now).total_seconds()
                
                logger.info(f"Следующий запуск запланирован на: {target_time} (через {int(time_diff/3600)} часов {int((time_diff%3600)/60)} минут)")
                
                # ИСПРАВЛЕНО: Проверяем точное время или окно в 1 минуту
                is_exact_time = (now.hour == target_hour and now.minute == target_minute)
                is_time_window = time_diff <= 60
                not_sent_today = (self.last_rank_update_date is None or self.last_rank_update_date < today)
                
                if (is_exact_time or is_time_window) and not_sent_today:
                    logger.info(f"ВРЕМЯ ОТПРАВКИ: Запуск полного сбора данных и отправки в {now}")
                    try:
                        self.run_scraping_job()
                        self.last_rank_update_date = today
                        logger.info(f"Данные успешно собраны и отправлены: {now}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке данных: {str(e)}")
                    
                    # После отправки спим до следующего дня
                    time_diff = 24 * 60 * 60  # 24 часа
                
                # ИСПРАВЛЕНО: В критический период проверяем каждые 30 секунд
                if time_diff <= 300:  # Если до запуска меньше 5 минут
                    sleep_time = 30  # Проверяем каждые 30 секунд
                    logger.info(f"Планировщик в режиме точной проверки, спит 30 секунд")
                else:
                    # Обычный режим - спим до нужного времени, но не больше 1 часа
                    sleep_time = min(time_diff - 300, 3600)  # Оставляем 5 минут запаса
                    logger.info(f"Планировщик спит {int(sleep_time/60)} минут до следующей проверки")
                
                # Спим с возможностью прерывания
                for _ in range(int(sleep_time)):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Ошибка в циле планировщика: {str(e)}")
                # При ошибке спим 5 минут перед повтором
                time.sleep(300)
    
    def start(self):
        """Start the scheduler"""
        try:
            # Проверка на наличие уже запущенного экземпляра
            import fcntl
            import os
            
            # Перемещаем файл блокировки также в директорию данных
            lockfile_path = os.path.join(self.data_dir, "coinbasebot.lock")
            logger.info(f"Файл блокировки будет храниться по пути: {lockfile_path}")
            
            # Если файл блокировки существует, но стар (> 30 минут), удаляем его
            if os.path.exists(lockfile_path):
                try:
                    file_time = os.path.getmtime(lockfile_path)
                    current_time = time.time()
                    # Если файл старше 30 минут
                    if current_time - file_time > 30 * 60:
                        os.remove(lockfile_path)
                        logger.info(f"Удален устаревший файл блокировки (возраст: {(current_time - file_time)/60:.1f} минут)")
                except Exception as e:
                    logger.warning(f"Ошибка при проверке старого файла блокировки: {str(e)}")
                    
            # Проверяем и удаляем старый файл блокировки ручной операции
            manual_lock_file = os.path.join(self.data_dir, "manual_operation.lock")
            if os.path.exists(manual_lock_file):
                try:
                    file_time = os.path.getmtime(manual_lock_file)
                    current_time = time.time()
                    # Если файл старше 10 минут или при запуске системы - удаляем его
                    if current_time - file_time > 10 * 60:
                        os.remove(manual_lock_file)
                        logger.info(f"При запуске удален файл блокировки ручной операции (возраст: {(current_time - file_time)/60:.1f} минут)")
                    else:
                        logger.warning(f"При запуске обнаружен недавний файл блокировки ручной операции (возраст: {(current_time - file_time)/60:.1f} минут)")
                except Exception as e:
                    logger.warning(f"Ошибка при проверке файла блокировки ручной операции: {str(e)}")
            
            try:
                self.lockfile = open(lockfile_path, "w")
                fcntl.lockf(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.info("Получена блокировка файла. Этот экземпляр бота будет единственным запущенным.")
            except IOError:
                logger.error("Другой экземпляр бота уже запущен. Завершение работы.")
                self.lockfile = None
                return False
                
            if self.running:
                logger.warning("Scheduler is already running")
                return True
                
            self.running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._scheduler_loop)
            self.thread.daemon = True
            self.thread.start()
            
            # Рассчитываем время следующего запуска (8:01 UTC = 11:01 MSK)
            now = datetime.now()
            next_run = now.replace(hour=8, minute=1, second=0, microsecond=0)
            
            # Если время уже прошло сегодня, планируем на завтра
            if next_run <= now:
                next_run += timedelta(days=1)
                
            logger.info(f"Scheduler started. Next run at: {next_run}")
            
            # Uncomment to run immediately for testing
            # self.run_scraping_job()
            
            return True
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            return False
    
    def stop(self):
        """Stop the scheduler"""
        if self.running:
            self.running = False
            self.stop_event.set()
            if self.thread:
                self.thread.join(timeout=1)
            # Освобождаем блокировку файла при остановке
            if hasattr(self, 'lockfile') and self.lockfile is not None:
                import fcntl
                try:
                    fcntl.lockf(self.lockfile, fcntl.LOCK_UN)
                    self.lockfile.close()
                    logger.info("Блокировка файла освобождена")
                except Exception as e:
                    logger.error(f"Ошибка при освобождении блокировки файла: {str(e)}")
            logger.info("Scheduler stopped")
    
    def _send_combined_message(self, rankings_data, fear_greed_data=None, altseason_data=None, market_breadth_data=None, chart_data=None):
        """
        Отправляет комбинированное сообщение с данными о рейтинге, индексе страха и жадности,
        Altcoin Season Index и ширине рынка в упрощенном формате
        
        Args:
            rankings_data (dict): Данные о рейтинге приложения
            fear_greed_data (dict, optional): Данные индекса страха и жадности
            altseason_data (dict, optional): Данные индекса сезона альткоинов
            market_breadth_data (dict, optional): Данные индикатора ширины рынка
            
        Returns:
            bool: True если сообщение успешно отправлено, False в противном случае
        """
        try:
            # Убедимся, что телеграм-бот правильно инициализирован
            if not self.telegram_bot.test_connection():
                logger.error("Ошибка соединения с Telegram. Сообщение не отправлено.")
                return False
                
            # Извлекаем рейтинг из данных
            if not rankings_data or "categories" not in rankings_data or not rankings_data["categories"]:
                logger.error("Неверный формат данных о рейтинге")
                return False
                
            # ИСПРАВЛЕНИЕ: Копируем ТОЧНУЮ логику из рабочего test-message
            rankings_message = self.scraper.format_rankings_message(rankings_data)
            combined_message = rankings_message
            
            # Затем добавляем данные индекса страха и жадности, если доступны
            if fear_greed_data:
                # Используем метод fear_greed_tracker для форматирования сообщения
                fear_greed_message = self.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
                combined_message += f"\n\n{fear_greed_message}"
            
            # ИСПРАВЛЕНИЕ: ТОЧНАЯ копия логики из РАБОЧЕГО /test-message
            if market_breadth_data:
                try:
                    from main import create_quick_chart
                    from image_uploader import image_uploader
                    
                    png_data = create_quick_chart()
                    if png_data:
                        external_url = image_uploader.upload_chart(png_data)
                        if external_url:
                            # ТОЧНО как в рабочем test-message - ссылка встроена в статус
                            market_breadth_message = f"Market by 200MA: {market_breadth_data['signal']} [{market_breadth_data['condition']}]({external_url}): {market_breadth_data['current_value']:.1f}%"
                            combined_message += f"\n\n{market_breadth_message}"
                        else:
                            # Fallback как в рабочем test-message
                            market_breadth_message = f"Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['current_value']:.1f}%"
                            combined_message += f"\n\n{market_breadth_message}"
                    else:
                        # Fallback как в рабочем test-message
                        market_breadth_message = f"Market by 200MA: {market_breadth_data['signal']} {market_breadth_data['condition']}: {market_breadth_data['current_value']:.1f}%"
                        combined_message += f"\n\n{market_breadth_message}"
                except Exception as e:
                    logger.error(f"Ошибка при создании графика для планировщика: {str(e)}")
                    # Fallback как в рабочем test-message
                    market_breadth_message = self.market_breadth.format_breadth_message(market_breadth_data)
                    if market_breadth_message:
                        combined_message += f"\n\n{market_breadth_message}"
            else:
                logger.info("Данные Market Breadth недоступны")
            
            # Altcoin Season Index удален из сообщений по запросу пользователя
            # Данные по-прежнему собираются для веб-интерфейса, но не отправляются в Telegram
            if altseason_data:
                logger.info(f"Altcoin Season Index data collected but not included in message: {altseason_data['signal']} - {altseason_data['status']}")
            else:
                logger.info("Altcoin Season Index данные недоступны")
            
            # Отправляем основное сообщение (теперь включает встроенную ссылку на график)
            if not self.telegram_bot.send_message(combined_message):
                logger.error("Не удалось отправить комбинированное сообщение в Telegram.")
                return False
                
            return True
            
            logger.info("Комбинированное сообщение успешно отправлено")
            return True
            
        except Exception as e:
            error_message = f"❌ Произошла ошибка при отправке сообщения: {str(e)}"
            logger.error(error_message)
            try:
                self.telegram_bot.send_message(error_message)
            except:
                pass
            return False
    
    def run_scraping_job(self, force_refresh=False):
        """
        Выполняет задание по скрапингу: получает данные SensorTower, Fear & Greed Index, 
        Altcoin Season Index и отправляет в Telegram КАЖДЫЙ ДЕНЬ независимо от изменения рейтинга
        
        Args:
            force_refresh (bool): Параметр больше не используется, сообщения отправляются всегда
        """
        logger.info(f"Выполняется запланированное задание скрапинга в {datetime.now()}")
        
        try:
            # Проверяем соединение с Telegram
            if not self.telegram_bot.test_connection():
                logger.error("Ошибка соединения с Telegram. Задание прервано.")
                return False
            
            # ИСПРАВЛЕНИЕ: Собираем СВЕЖИЕ данные рейтинга НЕПОСРЕДСТВЕННО в момент отправки
            logger.info("ИСПРАВЛЕНИЕ: Собираем СВЕЖИЕ данные рейтинга через rnk.py прямо сейчас")
            
            # Сначала запускаем rnk.py для получения свежих данных
            try:
                logger.info("Запуск rnk.py для получения актуальных данных...")
                self.run_rnk_script()
                logger.info("rnk.py выполнен успешно, данные обновлены")
                
                # Небольшая пауза чтобы данные успели записаться
                import time
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Ошибка при запуске rnk.py: {str(e)}")
            
            # Теперь читаем свежие данные из JSON файла
            from json_rank_reader import get_rank_from_json, get_latest_rank_date
            
            current_rank = get_rank_from_json()
            current_date = get_latest_rank_date()
            
            logger.info(f"ИСПРАВЛЕНИЕ: Получен СВЕЖИЙ рейтинг {current_rank} на дату {current_date}")
            
            # Создаем структуру данных совместимую с остальным кодом
            rankings_data = {
                "app_name": "Coinbase",
                "app_id": "886427730",
                "date": current_date or time.strftime("%Y-%m-%d"),
                "categories": [
                    {"category": "US - iPhone - Top Free", "rank": str(current_rank) if current_rank is not None else "None"}
                ],
                "trend": {"direction": "same", "previous": None}
            }
            
            logger.info(f"ИСПРАВЛЕНИЕ: Текущий рейтинг из JSON: {current_rank} на дату {current_date}")
            
            # Получаем данные индекса страха и жадности
            fear_greed_data = None
            try:
                fear_greed_data = self.fear_greed_tracker.get_fear_greed_index()
                if fear_greed_data:
                    logger.info(f"Успешно получены данные Fear & Greed Index: {fear_greed_data['value']} ({fear_greed_data['classification']})")
                else:
                    logger.warning("Не удалось получить данные Fear & Greed Index")
            except Exception as e:
                logger.error(f"Ошибка при получении данных Fear & Greed Index: {str(e)}")
                
            # Получаем свежие данные Altcoin Season Index
            # Это всегда происходит при отправке сообщения, чтобы данные были актуальными
            altseason_data = None
            try:
                logger.info("Получение данных Altcoin Season Index для комбинированного сообщения")
                altseason_data = self.altcoin_season_index.get_altseason_index()
                if altseason_data:
                    logger.info(f"Успешно получены данные Altcoin Season Index: {altseason_data['signal']} - {altseason_data['status']} (Индекс: {altseason_data['index']})")
                else:
                    logger.warning("Не удалось получить данные Altcoin Season Index")
            except Exception as e:
                logger.error(f"Ошибка при получении данных Altcoin Season Index: {str(e)}")
            
            # ИСПРАВЛЕНИЕ: Загружаем данные ОДИН РАЗ и используем для расчета и графика
            market_breadth_data = None
            chart_data = None
            try:
                logger.info("ИСПРАВЛЕНИЕ: Загружаем свежие данные ОДИН РАЗ для Market Breadth и графика")
                from crypto_analyzer_cryptocompare import CryptoAnalyzer
                
                analyzer = CryptoAnalyzer(cache=None)
                top_coins = analyzer.get_top_coins(50)
                
                if top_coins:
                    stablecoins = ['USDT', 'USDC', 'DAI']
                    filtered_coins = [coin for coin in top_coins if coin['symbol'] not in stablecoins]
                    
                    # Загружаем исторические данные ОДИН РАЗ
                    historical_data = analyzer.load_historical_data(filtered_coins, 1400)
                    
                    if historical_data:
                        # Рассчитываем индикатор ОДИН РАЗ
                        indicator_data = analyzer.calculate_market_breadth(historical_data, 200, 1095)
                        
                        if not indicator_data.empty:
                            latest_percentage = indicator_data['percentage'].iloc[-1]
                            
                            # Определяем сигнал и условие
                            if latest_percentage >= 80:
                                signal = "🔴"
                                condition = "Overbought"
                            elif latest_percentage <= 20:
                                signal = "🟢"  
                                condition = "Oversold"
                            else:
                                signal = "🟡"
                                condition = "Neutral"
                            
                            market_breadth_data = {
                                'signal': signal,
                                'condition': condition,
                                'current_value': latest_percentage,
                                'percentage': round(latest_percentage, 1)
                            }
                            
                            # Сохраняем данные для создания графика БЕЗ ПОВТОРНОЙ ЗАГРУЗКИ
                            chart_data = {
                                'historical_data': historical_data,
                                'indicator_data': indicator_data
                            }
                            
                            logger.info(f"ИСПРАВЛЕНИЕ: Market Breadth рассчитан ОДИН РАЗ: {signal} - {condition} ({latest_percentage:.1f}%)")
                        else:
                            logger.warning("ИСПРАВЛЕНИЕ: Пустые данные индикатора")
                    else:
                        logger.warning("ИСПРАВЛЕНИЕ: Не удалось загрузить исторические данные")
                else:
                    logger.warning("ИСПРАВЛЕНИЕ: Не удалось получить топ монет")
                        
            except Exception as e:
                logger.error(f"ИСПРАВЛЕНИЕ: Ошибка загрузки данных: {str(e)}")
            
            # ИЗМЕНЕНО: Отправляем сообщение каждый день независимо от изменения рейтинга
            if self.last_sent_rank is None:
                logger.info(f"Первый запуск, предыдущее значение отсутствует. Текущий рейтинг: {current_rank}")
                # Для тестирования добавляем искусственный тренд, если есть числовое значение
                if current_rank is not None:
                    rankings_data["trend"] = {"direction": "up", "previous": current_rank + 5}
                    logger.info(f"Добавлен искусственный тренд для тестирования отображения индикаторов: {current_rank + 5} → {current_rank}")
                else:
                    rankings_data["trend"] = {"direction": "same", "previous": None}
            elif current_rank != self.last_sent_rank:
                logger.info(f"Обнаружено изменение рейтинга: {current_rank} (предыдущий: {self.last_sent_rank})")
                # Добавляем префикс для понимания, улучшение или ухудшение (только для числовых значений)
                if current_rank is not None and self.last_sent_rank is not None:
                    if current_rank < self.last_sent_rank:
                        logger.info(f"Улучшение рейтинга: {self.last_sent_rank} → {current_rank}")
                        rankings_data["trend"] = {"direction": "up", "previous": self.last_sent_rank}
                    else:
                        logger.info(f"Ухудшение рейтинга: {self.last_sent_rank} → {current_rank}")
                        rankings_data["trend"] = {"direction": "down", "previous": self.last_sent_rank}
                else:
                    # Если один из рейтингов None, просто показываем изменение
                    rankings_data["trend"] = {"direction": "same", "previous": self.last_sent_rank}
            else:
                logger.info(f"Рейтинг не изменился ({current_rank} = {self.last_sent_rank}), но сообщение будет отправлено согласно ежедневному расписанию.")
                # Сохраняем последний рейтинг для показа тренда
                rankings_data["trend"] = {"direction": "same", "previous": self.last_sent_rank}
            
            # ИЗМЕНЕНО: Отправляем сообщение ВСЕГДА (каждый день в назначенное время)
            logger.info("ИЗМЕНЕНО: Отправляем ежедневное сообщение независимо от изменения рейтинга")
            
            # ИЗМЕНЕНО: Отправляем ежедневное сообщение независимо от изменения рейтинга
            result = self._send_combined_message(rankings_data, fear_greed_data, altseason_data, market_breadth_data, chart_data)
            
            # Обновляем последний отправленный рейтинг независимо от результата отправки
            # Это поможет избежать множественных сообщений при сбоях отправки
            previous_rank = self.last_sent_rank
            self.last_sent_rank = current_rank
            logger.info(f"Обновлен последний отправленный рейтинг: {previous_rank} → {self.last_sent_rank}")
            
            # Сохраняем рейтинг в файл для восстановления при перезапуске
            # Делаем это синхронно с обновлением переменной, чтобы избежать рассинхронизации
            try:
                with open(self.rank_history_file, "w") as f:
                    f.write(str(current_rank) if current_rank is not None else "None")
                logger.info(f"Рейтинг {current_rank} сохранен в файл {self.rank_history_file}")
                
                # Проверка записи в файл
                if os.path.exists(self.rank_history_file):
                    with open(self.rank_history_file, "r") as check_file:
                        saved_value = check_file.read().strip()
                        if saved_value != str(current_rank):
                            logger.error(f"Ошибка записи: в файле {saved_value}, должно быть {current_rank}")
                            
                # Дополнительно, сохраняем в JSON-историю через HistoryAPI
                try:
                    # Импортируем API истории
                    from history_api import HistoryAPI
                    
                    # Создаем экземпляр API и сохраняем данные
                    history_api = HistoryAPI(self.data_dir)
                    
                    # Сохраняем рейтинг в историю с предыдущим значением для подсчета изменения
                    history_api.save_rank_history(
                        rank=current_rank, 
                        previous_rank=previous_rank
                    )
                    
                    # Если доступны данные индекса страха и жадности, сохраняем и их
                    if fear_greed_data and 'value' in fear_greed_data and 'classification' in fear_greed_data:
                        history_api.save_fear_greed_history(
                            value=int(fear_greed_data['value']), 
                            classification=fear_greed_data['classification']
                        )
                        
                    # Если доступны данные Altcoin Season Index, сохраняем их
                    if (altseason_data and 
                        'signal' in altseason_data and 
                        'description' in altseason_data and 
                        'status' in altseason_data and 
                        'index' in altseason_data and 
                        'btc_performance' in altseason_data and
                        altseason_data['signal'] is not None):
                        # Сохраняем данные Altcoin Season Index в историю
                        try:
                            history_api.save_altseason_index_history(
                                signal=altseason_data['signal'],
                                description=altseason_data['description'],
                                status=altseason_data['status'],
                                index=altseason_data['index'],
                                btc_performance=altseason_data['btc_performance']
                            )
                            logger.info(f"Сохранены данные Altcoin Season Index в историю: {altseason_data['signal']} - {altseason_data['status']}")
                        except Exception as e:
                            logger.warning(f"Ошибка при сохранении Altcoin Season Index в историю: {str(e)}")
                        
                    logger.info(f"История данных успешно сохранена в JSON-файлы")
                except ImportError:
                    # API истории недоступен, пропускаем сохранение в историю
                    logger.debug("API истории недоступен. История рейтинга сохранена только в файл.")
                except Exception as history_error:
                    logger.error(f"Ошибка при сохранении истории в JSON-файлы: {str(history_error)}")
                    
            except Exception as e:
                logger.error(f"Ошибка при сохранении рейтинга в файл: {str(e)}")
            
            return result
                
        except Exception as e:
            error_message = f"❌ Произошла ошибка во время задания скрапинга: {str(e)}"
            logger.error(error_message)
            try:
                self.telegram_bot.send_message(error_message)
            except:
                pass
            return False
            
    def get_current_fear_greed_index(self):
        """
        Get current Fear & Greed Index data for testing/manual triggering
        
        Returns:
            dict: Fear & Greed Index data or None in case of error
        """
        try:
            return self.fear_greed_tracker.get_fear_greed_index()
        except Exception as e:
            logger.error(f"Error getting Fear & Greed Index: {str(e)}")
            return None
    
    def get_current_altseason_index(self):
        """
        Get current Altcoin Season Index data for testing/manual triggering
        
        Returns:
            dict: Altcoin Season Index data or None in case of error
        """
        try:
            return self.altcoin_season_index.get_altseason_index()
        except Exception as e:
            logger.error(f"Error getting Altcoin Season Index: {str(e)}")
            return None
            
    def run_now(self, force_send=False):
        """
        Manually trigger a scraping job immediately
        
        Args:
            force_send (bool): If True, send message even if rank hasn't changed
            
        Returns:
            bool: True if job ran successfully, False otherwise
        """
        logger.info("Manual scraping job triggered")
        
        # Выполняем операцию без использования файла блокировки
        # Примечание: Механизм файловой блокировки отключен, так как он вызывал проблемы
        # с плановым запуском задач и создавал permanent файл блокировки
        
        if force_send:
            # Temporarily save the old value
            old_last_sent_rank = self.last_sent_rank
            # Reset to force sending
            self.last_sent_rank = None
            
            result = self.run_scraping_job(force_refresh=True)
            
            # If job failed, restore the old value
            if not result:
                self.last_sent_rank = old_last_sent_rank
                # Также восстановим значение в файле истории
                try:
                    with open(self.rank_history_file, "w") as f:
                        f.write(str(old_last_sent_rank))
                    logger.info(f"Восстановлен рейтинг в файле: {old_last_sent_rank}")
                except Exception as e:
                    logger.error(f"Ошибка при восстановлении рейтинга в файле: {str(e)}")
        else:
            result = self.run_scraping_job(force_refresh=False)
            
        return result
