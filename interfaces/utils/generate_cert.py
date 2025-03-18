import os
import subprocess
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from interfaces.config import WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV, ASSETS_DIR
from interfaces.utils.logger import setup_logger

logger = setup_logger(__name__)

def generate_ssl_cert():
    """Генерирует SSL сертификат для вебхука"""
    try:
        # Создаем директорию для сертификатов, если её нет
        os.makedirs(ASSETS_DIR, exist_ok=True)
        
        # Генерируем приватный ключ и сертификат
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-keyout", WEBHOOK_SSL_PRIV,
            "-out", WEBHOOK_SSL_CERT, "-days", "365", "-nodes",
            "-subj", "/CN=localhost"
        ], check=True)
        
        logger.info(f"SSL сертификат успешно сгенерирован в {ASSETS_DIR}")
        logger.info(f"  - Сертификат: {WEBHOOK_SSL_CERT}")
        logger.info(f"  - Приватный ключ: {WEBHOOK_SSL_PRIV}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при генерации сертификата: {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        raise

if __name__ == "__main__":
    generate_ssl_cert()
    logger.info("Для запуска бота с webhook используйте: python -m interfaces.run_bot_webhook")
    logger.info("Убедитесь, что порт 8443 открыт и доступен извне") 