def _scheduler_loop(self):
    """
    The main scheduler loop that runs in a background thread.
    Sleeps for 5 minutes between executions.
    """
    while not self.stop_event.is_set():
        try:
            # Проверяем, не выполняется ли ручная операция скрапинга
            manual_lock_file = os.path.join(self.data_dir, "manual_operation.lock")
            
            if os.path.exists(manual_lock_file):
                try:
                    import fcntl
                    with open(manual_lock_file, "r") as manual_lock:
                        try:
                            # Пытаемся получить блокировку без ожидания
                            fcntl.lockf(manual_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            # Если получили блокировку, значит никто ее не держит
                            fcntl.lockf(manual_lock, fcntl.LOCK_UN)
                            # Запускаем задание
                            self.run_scraping_job()
                        except IOError:
                            # Блокировка занята - пропускаем текущий запуск
                            logger.info("Пропуск планового запуска из-за выполнения ручной операции")
                except Exception as e:
                    logger.error(f"Ошибка при проверке блокировки ручной операции: {str(e)}")
                    # В случае ошибки работы с блокировкой все равно выполняем задание
                    self.run_scraping_job()
            else:
                # Файла блокировки нет, запускаем задание как обычно
                self.run_scraping_job()
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