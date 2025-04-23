import logging
import os
from logging.handlers import TimedRotatingFileHandler
from config import LOG_LEVEL, LOG_FILE

def setup_logger():
    """Set up and configure the logger with 7-day rotation"""
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create a logger
    logger = logging.getLogger('sensortower_bot')
    logger.setLevel(log_level)
    
    # Clear any existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create a rotating file handler that keeps logs for 7 days
    file_handler = TimedRotatingFileHandler(
        LOG_FILE,
        when='midnight',  # Rotate at midnight
        interval=1,       # One day per file
        backupCount=7,    # Keep logs for 7 days
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # Create a stream handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()
