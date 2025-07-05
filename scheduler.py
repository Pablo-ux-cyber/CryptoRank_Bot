import os
import threading
import time
import subprocess
from datetime import datetime, timedelta

from logger import logger
from scraper import SensorTowerScraper
from telegram_bot import TelegramBot
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
        self.telegram_bot = TelegramBot()
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
        - Проверяет рейтинг приложения, Fear & Greed Index и Altcoin Season Index один раз в день в 8:01
        - Все данные собираются за один раз и отправляются одним сообщением
        """
        # Переменные для отслеживания, когда последний раз обновлялись данные
        self.last_rank_update_date = None
        self.last_rnk_update_date = None
        
        # При запуске не будем загружать данные Google Trends - получим их вместе с общим обновлением
        logger.info("Планировщик запущен, rnk.py в 10:59 MSK, обновление данных в 11:01 MSK")
        
        while not self.stop_event.is_set():
            try:
                # Текущее время и дата
                now = datetime.now()
                today = now.date()
                update_rank = False
                run_rnk = False
                
                # Проверяем, не нужно ли запустить rnk.py (в 10:59 MSK = 7:59 UTC)
                if (now.hour == 7 and now.minute >= 59 and now.minute <= 59):
                    if self.last_rnk_update_date is None or self.last_rnk_update_date < today:
                        run_rnk = True
                        logger.info(f"Запланирован запуск rnk.py в {now} (UTC 7:59 = MSK 10:59)")
                
                # Проверяем, не нужно ли обновить данные о рейтинге Coinbase, 
                # Fear & Greed Index и Altcoin Season Index (в 11:01 MSK = 8:01 UTC)
                if (now.hour == 8 and now.minute >= 1 and now.minute <= 6):
                    if self.last_rank_update_date is None or self.last_rank_update_date < today:
                        update_rank = True
                        logger.info(f"Запланировано комплексное обновление данных в {now} (UTC 8:01 = MSK 11:01)")
                
                # Механизм проверки файла блокировки удален, так как он вызывал проблемы
                # и приводил к тому, что плановые задания не выполнялись
                
                # Запускаем rnk.py, если пришло время
                if run_rnk:
                    try:
                        logger.info(f"Запуск rnk.py в {now.hour}:{now.minute}")
                        self.run_rnk_script()
                        self.last_rnk_update_date = today
                        logger.info(f"rnk.py успешно выполнен: {now}")
                    except Exception as e:
                        logger.error(f"Ошибка при запуске rnk.py: {str(e)}")
                
                # Обновляем все данные, если пришло время
                if update_rank:
                    try:
                        time_type = "основное"
                        logger.info(f"Получение данных о рейтинге Coinbase ({time_type} обновление в {now.hour}:{now.minute})")
                        self.run_scraping_job()
                        self.last_rank_update_date = today
                        logger.info(f"Данные о рейтинге Coinbase успешно обновлены: {now}")
                    except Exception as e:
                        logger.error(f"Ошибка при получении данных о рейтинге Coinbase: {str(e)}")
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
            
            # Sleep for 5 minutes
            seconds_to_sleep = 5 * 60  # 5 minutes in seconds
            logger.info(f"Scheduler sleeping for {seconds_to_sleep} seconds (5 minutes)")
            
            # Wait with checking for stop event
            for _ in range(seconds_to_sleep):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
    
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
            
            # Рассчитываем время следующего запуска (5:01 UTC = 8:01 MSK)
            now = datetime.now()
            next_run = now.replace(hour=5, minute=1, second=0, microsecond=0)
            
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
    
    def _send_combined_message(self, rankings_data, fear_greed_data=None, altseason_data=None, market_breadth_data=None):
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
                
            # Используем метод scraper для форматирования сообщения о рейтинге
            formatted_rankings = self.scraper.format_rankings_message(rankings_data)
            combined_message = formatted_rankings
            
            # Затем добавляем данные индекса страха и жадности, если доступны
            if fear_greed_data:
                # Используем метод fear_greed_tracker для форматирования сообщения
                fear_greed_message = self.fear_greed_tracker.format_fear_greed_message(fear_greed_data)
                combined_message += f"\n\n{fear_greed_message}"
            
            # Добавляем данные индикатора ширины рынка, если доступны
            if market_breadth_data:
                market_breadth_message = self.market_breadth.format_breadth_message(market_breadth_data)
                if market_breadth_message:
                    combined_message += f"\n\n{market_breadth_message}"
                    logger.info(f"Добавлены данные ширины рынка в сообщение: {market_breadth_data['signal']} - {market_breadth_data['condition']}")
            else:
                logger.info("Данные индикатора ширины рынка недоступны")
            
            # Altcoin Season Index удален из сообщений по запросу пользователя
            # Данные по-прежнему собираются для веб-интерфейса, но не отправляются в Telegram
            if altseason_data:
                logger.info(f"Altcoin Season Index data collected but not included in message: {altseason_data['signal']} - {altseason_data['status']}")
            else:
                logger.info("Altcoin Season Index данные недоступны")
            
            # Добавляем ссылку на график к основному сообщению
            try:
                # Создаем ссылку на график
                chart_url = "https://89570994-1faf-4430-9046-75d67078f252-00-s6f04tuxdmc.riker.replit.dev/chart-view"
                
                # Добавляем ссылку на график к основному сообщению
                chart_message = f"\n\n📈 Chart: {chart_url}"
                extended_message = combined_message + chart_message
                
                # Отправляем единое сообщение со ссылкой на график
                if not self.telegram_bot.send_message(extended_message):
                    logger.error("Не удалось отправить сообщение со ссылкой на график в Telegram.")
                    return False
                
                logger.info("Сообщение со ссылкой на график успешно отправлено в Telegram")
                    
            except Exception as e:
                logger.error(f"Ошибка при отправке ссылки на график: {str(e)}")
                return False
            
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
        Altcoin Season Index и отправляет в Telegram только если рейтинг изменился или это первый запуск
        
        Args:
            force_refresh (bool): Если True, отправить сообщение даже если рейтинг не изменился
        """
        logger.info(f"Выполняется запланированное задание скрапинга в {datetime.now()}")
        
        try:
            # Проверяем соединение с Telegram
            if not self.telegram_bot.test_connection():
                logger.error("Ошибка соединения с Telegram. Задание прервано.")
                return False
            
            # Получаем данные о рейтинге
            rankings_data = self.scraper.scrape_category_rankings()
            
            if not rankings_data:
                logger.info("SensorTower API не вернул данные, создаем сообщение с None")
                # Создаем структуру данных с None вместо рейтинга
                rankings_data = {
                    "app_name": "Coinbase",
                    "app_id": "886427730",
                    "date": time.strftime("%Y-%m-%d"),
                    "categories": [
                        {"category": "US - iPhone - Top Free", "rank": "None"}
                    ],
                    "trend": {"direction": "same", "previous": None}
                }
            
            # Проверяем наличие данных о категориях и рейтинге
            if not rankings_data.get("categories") or not rankings_data["categories"]:
                logger.error("Не найдены данные о категориях в полученных данных")
                return False
                
            # Получаем текущий рейтинг
            rank_value = rankings_data["categories"][0]["rank"]
            if rank_value == "None":
                current_rank = None
                logger.info("Текущий рейтинг: None (нет данных от SensorTower API)")
            else:
                current_rank = int(rank_value)
            
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
            
            # Получаем данные о ширине рынка
            market_breadth_data = None
            try:
                logger.info("Получение данных индикатора ширины рынка")
                market_breadth_data = self.market_breadth.get_market_breadth_data()
                if market_breadth_data:
                    logger.info(f"Успешно получены данные ширины рынка: {market_breadth_data['signal']} - {market_breadth_data['condition']} ({market_breadth_data['current_value']:.1f}%)")
                else:
                    logger.warning("Не удалось получить данные индикатора ширины рынка")
            except Exception as e:
                logger.error(f"Ошибка при получении данных ширины рынка: {str(e)}")
            
            # Подробная проверка на изменение рейтинга
            if self.last_sent_rank is None:
                logger.info(f"Первый запуск, предыдущее значение отсутствует. Текущий рейтинг: {current_rank}")
                need_to_send = True
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
                need_to_send = True
            else:
                logger.info(f"Рейтинг не изменился ({current_rank} = {self.last_sent_rank}). Сообщение не отправлено.")
                need_to_send = False
            
            # Отправляем сообщение только если нужно
            if need_to_send:
                # Отправляем сообщение только если рейтинг изменился или это первый запуск
                result = self._send_combined_message(rankings_data, fear_greed_data, altseason_data, market_breadth_data)
                
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
            else:
                return True  # Работа выполнена успешно, сообщение не требовалось отправлять
                
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
