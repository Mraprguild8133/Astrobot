"""
Logging configuration for AstroGeminiBot
Sets up structured logging with appropriate levels and formatting
"""

import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(log_level: str = None, log_file: str = None):
    """
    Setup logging configuration for the bot
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Log file path (optional)
    """
    
    # Get log level from environment or use default
    if not log_level:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Get log file from environment or use default
    if not log_file:
        log_file = os.getenv("LOG_FILE", "bot.log")
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
    logger.info(f"AstroGeminiBot logging started at {datetime.now()}")
