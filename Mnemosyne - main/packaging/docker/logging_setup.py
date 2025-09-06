"""
Logging configuration for MnemosyneOS.
Sets up logging to file and console with appropriate format and permissions.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
import stat

from app.config import settings

# Configure logger name
LOGGER_NAME = "mnemosyneos"
LOG_FILE = os.path.join(settings.LOG_DIR, "mnemo.log")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

def setup_logger():
    """Set up and configure the logger"""
    # Create logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(LOG_LEVEL)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    
    # Create file handler
    try:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        
        # Create or check log file
        if not os.path.exists(LOG_FILE):
            open(LOG_FILE, 'a').close()
            os.chmod(LOG_FILE, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 0644
        
        # Set up rotating file handler
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT
        )
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        logger.info(f"Logger initialized. Logging to {LOG_FILE}")
    except Exception as e:
        # Fall back to console-only logging
        logger.addHandler(console_handler)
        logger.error(f"Error setting up file logging: {str(e)}. Falling back to console logging only.")
    
    return logger

def get_logger():
    """Get or create the logger instance"""
    logger = logging.getLogger(LOGGER_NAME)
    
    # If logger doesn't have handlers, set it up
    if not logger.handlers:
        logger = setup_logger()
    
    return logger
