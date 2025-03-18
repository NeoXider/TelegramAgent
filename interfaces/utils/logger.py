import logging
from ..config import LOG_FORMAT, LOG_FILE

def setup_logger(name: str) -> logging.Logger:
    """Настраивает и возвращает логгер с указанным именем"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Форматтер для логов
        formatter = logging.Formatter(LOG_FORMAT)
        
        # Хендлер для файла
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Хендлер для консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger 