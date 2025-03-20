import logging
import os
from typing import Dict, Any, Optional

def setup_logger(config: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """Настройка логгера
    
    Args:
        config: Опциональный словарь с настройками логгера
            {
                'logging': {
                    'level': 'INFO|DEBUG|WARNING|ERROR',
                    'format': 'строка форматирования'
                }
            }
    Returns:
        logging.Logger: Настроенный логгер
    """
    try:
        # Создаем директорию для логов если её нет
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"Создана директория для логов: {log_dir}")
        
        # Получаем корневой логгер
        logger = logging.getLogger()
        
        # Очищаем существующие обработчики
        logger.handlers.clear()
        
        # Настройки из конфига или по умолчанию
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        log_level = 'INFO'
        
        if config and 'logging' in config:
            log_level = config['logging'].get('level', log_level)
            log_format = config['logging'].get('format', log_format)
        
        # Создаем форматтер
        formatter = logging.Formatter(log_format)
        
        # Добавляем обработчик для файла
        try:
            file_handler = logging.FileHandler(
                os.path.join(log_dir, "bot.log"),
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            print("Добавлен файловый обработчик логов")
        except Exception as e:
            print(f"Ошибка при создании файлового обработчика: {str(e)}")
        
        # Добавляем обработчик для консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        print("Добавлен консольный обработчик логов")
        
        # Устанавливаем уровень логирования
        try:
            level = getattr(logging, log_level.upper())
            logger.setLevel(level)
            print(f"Установлен уровень логирования: {log_level}")
        except (AttributeError, TypeError):
            logger.setLevel(logging.INFO)
            print(f"Некорректный уровень логирования: {log_level}, используется INFO")
        
        logger.info("Логгер успешно настроен")
        return logger
        
    except Exception as e:
        # В случае ошибки создаем базовый логгер
        basic_logger = logging.getLogger()
        basic_logger.setLevel(logging.INFO)
        
        if not basic_logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            basic_logger.addHandler(console_handler)
        
        basic_logger.warning(f"Ошибка при настройке логгера: {str(e)}. Используется базовая конфигурация.")
        return basic_logger 