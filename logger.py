import logging
import os
from logging.handlers import RotatingFileHandler
from config import LOG_LEVEL, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT, GOOGLE_TRENDS_LOG_FILE

def setup_logger():
    """Set up and configure the logger with rotation to limit file size"""
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Set up the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers to avoid duplication
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Create a rotating file handler for the main log file
    file_handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Add handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Create a separate logger for Google Trends with its own rotating file handler
    trends_logger = logging.getLogger('google_trends')
    trends_logger.setLevel(log_level)
    
    # Create a rotating file handler for Google Trends
    trends_file_handler = RotatingFileHandler(
        GOOGLE_TRENDS_LOG_FILE, 
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )
    trends_file_handler.setFormatter(formatter)
    trends_logger.addHandler(trends_file_handler)
    
    # Return the main application logger
    return logging.getLogger('sensortower_bot')

logger = setup_logger()
