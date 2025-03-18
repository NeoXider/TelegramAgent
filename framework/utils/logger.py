import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Dict, Any

def setup_logger(config: Dict[str, Any]) -> logging.Logger:
    """Настройка логгера"""
    logger = logging.getLogger('bot')
    logger.setLevel(config['logging']['level'])
    
    # Создаем директорию для логов, если её нет
    log_dir = os.path.dirname(config['logging']['file'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Настраиваем файловый обработчик
    file_handler = RotatingFileHandler(
        config['logging']['file'],
        maxBytes=config['logging']['max_size'],
        backupCount=config['logging']['backup_count'],
        encoding='utf-8'
    )
    
    # Настраиваем консольный обработчик
    console_handler = logging.StreamHandler()
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Применяем форматтер к обработчикам
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 