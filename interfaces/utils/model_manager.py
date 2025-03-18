import subprocess
import time
import asyncio
from typing import List, Dict, Optional
from ..config import (
    OLLAMA_TIMEOUT,
    VISION_MODEL_TIMEOUT,
    MODEL_CACHE_DURATION,
    VISION_SUPPORT_CACHE_DURATION,
    TEST_IMAGE_PATH
)
from .logger import setup_logger
from .model_cache import model_cache

logger = setup_logger(__name__)

class ModelManager:
    def __init__(self):
        self._model_lock: Dict[str, bool] = {}

    async def get_available_models(self) -> List[str]:
        """Получает список доступных моделей из Ollama"""
        logger.info("Запрос списка доступных моделей")
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=OLLAMA_TIMEOUT
            )
            if result.returncode == 0:
                models = []
                for line in result.stdout.split('\n')[1:]:
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                logger.info(f"Получен список моделей: {models}")
                return models
            else:
                logger.error(f"Ошибка при получении списка моделей. Код возврата: {result.returncode}, stderr: {result.stderr}")
                return []
        except Exception as e:
            logger.error(f"Исключение при выполнении команды ollama list: {e}")
            return []

    async def check_model_vision_support(self, model_name: str) -> bool:
        """Проверяет, поддерживает ли модель работу с изображениями"""
        current_time = time.time()
        
        # Проверяем кэш
        if model_cache.is_vision_support_valid(model_name):
            supported, _ = model_cache.get_vision_support(model_name)
            logger.info(f"Используем кэшированный результат для модели {model_name}: {'поддерживает' if supported else 'не поддерживает'} изображения")
            return supported
        
        # Если модель уже проверяется, ждем результата
        if model_name in self._model_lock and self._model_lock[model_name]:
            logger.info(f"Модель {model_name} уже проверяется, ожидаем результат")
            while model_name in self._model_lock and self._model_lock[model_name]:
                await asyncio.sleep(1)
            if model_cache.is_vision_support_valid(model_name):
                supported, _ = model_cache.get_vision_support(model_name)
                return supported
            return False
        
        # Начинаем проверку
        self._model_lock[model_name] = True
        logger.info(f"Проверка поддержки изображений для модели {model_name}")
        
        try:
            # Пытаемся выполнить запрос с тестовым изображением
            result = subprocess.run(
                ["ollama", "run", model_name, f"describe this image: {TEST_IMAGE_PATH}"],
                capture_output=True,
                text=True,
                timeout=VISION_MODEL_TIMEOUT
            )
            
            # Проверяем результат
            supported = result.returncode == 0 and not any(
                error in result.stderr.lower() 
                for error in [
                    "no image data found",
                    "unsupported media type",
                    "invalid image format",
                    "cannot process image",
                    "model does not support images"
                ]
            )
            
            # Сохраняем результат в кэш
            model_cache.set_vision_support(model_name, supported, current_time)
            
            logger.info(f"Модель {model_name} {'поддерживает' if supported else 'не поддерживает'} работу с изображениями")
            if not supported and result.stderr:
                logger.debug(f"Причина: {result.stderr}")
                
            return supported
            
        except subprocess.TimeoutExpired:
            logger.error(f"Превышено время ожидания при проверке поддержки изображений для {model_name}")
            model_cache.set_vision_support(model_name, False, current_time)
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при проверке поддержки изображений для {model_name}: {e}")
            model_cache.set_vision_support(model_name, False, current_time)
            return False
            
        finally:
            self._model_lock[model_name] = False

    async def ensure_model_loaded(self, model_name: str) -> bool:
        """Проверяет, загружена ли модель, и загружает её при необходимости"""
        current_time = time.time()
        
        # Проверяем кэш
        if model_cache.is_model_valid(model_name):
            logger.info(f"Модель {model_name} уже загружена (кэш)")
            return True
        
        # Если модель уже загружается, ждем
        if model_name in self._model_lock and self._model_lock[model_name]:
            logger.info(f"Модель {model_name} уже загружается, ожидаем")
            while model_name in self._model_lock and self._model_lock[model_name]:
                await asyncio.sleep(1)
            return model_cache.is_model_valid(model_name)
        
        # Начинаем загрузку
        self._model_lock[model_name] = True
        logger.info(f"Загрузка модели {model_name}...")
        
        try:
            process = await asyncio.create_subprocess_exec(
                "ollama", "pull", model_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode == 0:
                model_cache.set_model_timestamp(model_name, current_time)
                logger.info(f"Модель {model_name} успешно загружена")
                return True
            else:
                logger.error(f"Ошибка при загрузке модели {model_name}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели {model_name}: {e}")
            return False
        finally:
            self._model_lock[model_name] = False

# Создаем глобальный экземпляр менеджера моделей
model_manager = ModelManager() 