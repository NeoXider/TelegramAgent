import json
import time
from pathlib import Path
from ..config import (
    ASSETS_DIR,
    MODEL_CACHE_DURATION,
    VISION_SUPPORT_CACHE_DURATION
)
from .logger import setup_logger

logger = setup_logger(__name__)

class ModelCache:
    def __init__(self):
        """Инициализация кэша моделей"""
        self.cache_file = ASSETS_DIR / "model_cache.json"
        self._ensure_cache_file()
        self._load_cache()
    
    def _ensure_cache_file(self):
        """Создает файл кэша, если он не существует"""
        if not ASSETS_DIR.exists():
            ASSETS_DIR.mkdir(parents=True)
        if not self.cache_file.exists():
            self._save_cache({
                "models": {},
                "vision_support": {}
            })
    
    def _load_cache(self) -> dict:
        """Загружает данные из файла кэша"""
        try:
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
            logger.info("Кэш моделей загружен")
        except Exception as e:
            logger.error(f"Ошибка при загрузке кэша: {e}")
            self.cache = {
                "models": {},
                "vision_support": {}
            }
    
    def _save_cache(self, data: dict = None):
        """Сохраняет данные в файл кэша"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data or self.cache, f, indent=2)
            logger.info("Кэш моделей сохранен")
        except Exception as e:
            logger.error(f"Ошибка при сохранении кэша: {e}")
    
    def get_model_timestamp(self, model_name: str) -> float:
        """Получает временную метку последней проверки модели"""
        return float(self.cache["models"].get(model_name, 0))
    
    def set_model_timestamp(self, model_name: str, timestamp: float):
        """Устанавливает временную метку проверки модели"""
        self.cache["models"][model_name] = timestamp
        self._save_cache()
    
    def get_vision_support(self, model_name: str) -> tuple[bool, float]:
        """Получает информацию о поддержке зрения и временную метку"""
        data = self.cache["vision_support"].get(model_name, {})
        return data.get("supported", False), float(data.get("timestamp", 0))
    
    def set_vision_support(self, model_name: str, supported: bool, timestamp: float):
        """Устанавливает информацию о поддержке зрения"""
        self.cache["vision_support"][model_name] = {
            "supported": supported,
            "timestamp": timestamp
        }
        self._save_cache()
    
    def is_model_valid(self, model_name: str) -> bool:
        """Проверяет, действителен ли кэш модели"""
        timestamp = self.get_model_timestamp(model_name)
        return time.time() - timestamp < MODEL_CACHE_DURATION
    
    def is_vision_support_valid(self, model_name: str) -> bool:
        """Проверяет, действителен ли кэш поддержки зрения"""
        _, timestamp = self.get_vision_support(model_name)
        return time.time() - timestamp < VISION_SUPPORT_CACHE_DURATION

# Создаем глобальный экземпляр кэша
model_cache = ModelCache() 