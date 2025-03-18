import logging
import pathlib
from typing import Dict, List
from dotenv import load_dotenv
import os
from pathlib import Path
import json

# Загружаем переменные из .env
load_dotenv()

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Пути
BASE_DIR = pathlib.Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / "assets"
CONFIG_DIR = BASE_DIR / "config"

# Создаем директории если их нет
ASSETS_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# Настройки приветствия
WELCOME_CONFIG = {
    "enabled": True,
    "message": """Привет! 👋 Я ваш AI-ассистент.
    
Я могу помочь вам с различными задачами, включая анализ изображений и ответы на вопросы.

Доступные команды:
/help - Показать это сообщение
/models - Посмотреть текущие модели
/auth - Авторизация администратора
/set_model - Установить модель (только для админов)""",
    "image_path": "assets/welcome.jpg",  # Относительный путь от корня проекта
    "show_commands": True,
}

# Загружаем пользовательские настройки приветствия если есть
welcome_config_path = CONFIG_DIR / "welcome_config.json"
if welcome_config_path.exists():
    try:
        with open(welcome_config_path, "r", encoding='utf-8') as f:
            custom_welcome = json.load(f)
            WELCOME_CONFIG.update(custom_welcome)
    except Exception as e:
        print(f"Ошибка при загрузке настроек приветствия: {e}")

# Системные настройки бота
SYSTEM_CONFIG = {
    "system_prompt": """Вы - полезный AI-ассистент. Ваша задача - помогать пользователям с их вопросами и задачами.

Правила общения:
1. Всегда будьте вежливы и профессиональны
2. Давайте четкие и понятные ответы
3. Если вы не уверены в ответе, так и скажите
4. При работе с кодом используйте форматирование
5. При анализе изображений описывайте то, что видите детально""",
    
    "rules": [
        "Не используйте нецензурную лексику",
        "Не распространяйте личную информацию пользователей",
        "Не генерируйте вредоносный код",
        "Не давайте медицинских или юридических советов",
        "При неясности запроса уточняйте детали"
    ],
    
    "max_message_length": 4096,  # Максимальная длина сообщения в Telegram
    "image_size_limit": 5242880,  # Максимальный размер изображения (5MB)
    "allowed_image_formats": ["jpg", "jpeg", "png", "webp"],
    
    # Настройки стриминга
    "streaming": {
        "enabled": True,  # Включен ли режим стриминга по умолчанию
        "chunk_size": 50,  # Количество символов для отправки в одном чанке
        "update_interval": 0.5,  # Интервал между обновлениями сообщения в секундах
        "max_chunks_before_update": 10  # Максимальное количество чанков перед обновлением сообщения
    }
}

# Загружаем пользовательские системные настройки если есть
system_config_path = CONFIG_DIR / "system_config.json"
if system_config_path.exists():
    try:
        with open(system_config_path, "r", encoding='utf-8') as f:
            custom_system = json.load(f)
            SYSTEM_CONFIG.update(custom_system)
    except Exception as e:
        print(f"Ошибка при загрузке системных настроек: {e}")

# Получаем значения из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'default_password')

# Настройки логирования
LOG_FORMAT = "%(asctime)s - %(name)s - INFO - [%(filename)s:%(lineno)d] - %(message)s"
LOG_FILE = BASE_DIR / "bot.log"

# Настройки Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))
VISION_MODEL_TIMEOUT = int(os.getenv("VISION_MODEL_TIMEOUT", "120"))

# Настройки кэширования
MODEL_CACHE_DURATION = int(os.getenv("MODEL_CACHE_DURATION", "3600"))
VISION_SUPPORT_CACHE_DURATION = int(os.getenv("VISION_SUPPORT_CACHE_DURATION", "3600"))

# Проверяем обязательные переменные
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Не указан TELEGRAM_BOT_TOKEN в .env файле")

if ADMIN_PASSWORD == 'default_password':
    print("Внимание: Используется пароль администратора по умолчанию. Рекомендуется изменить его в .env файле")

# Настройки webhook
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "localhost")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8443"))
WEBHOOK_URL_BASE = os.getenv("WEBHOOK_URL_BASE", f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}/webhook")
WEBHOOK_SSL_CERT = ASSETS_DIR / "webhook_cert.pem"
WEBHOOK_SSL_PRIV = ASSETS_DIR / "webhook_pkey.pem"

# Настройки моделей по умолчанию
DEFAULT_MODELS: Dict[str, str] = {
    "основная": os.getenv("DEFAULT_MODEL_MAIN", "gemma3:latest"),
    "зрение": os.getenv("DEFAULT_MODEL_VISION", "gemma3:latest")
}

# Настройки тестового изображения
TEST_IMAGE_PATH = ASSETS_DIR / "test_image.jpg"

# Настройки моделей по умолчанию
DEFAULT_MODEL = "gemma3:latest"
DEFAULT_VISION_MODEL = "gemma3:latest" 