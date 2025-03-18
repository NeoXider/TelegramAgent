import json
import aiohttp
from typing import Optional, Dict, Any
from .utils.logger import setup_logger
from .utils.model_manager import model_manager
import base64

logger = setup_logger(__name__)

class AgentBase:
    def __init__(self, main_model: str, vision_model: str):
        """Инициализация агента"""
        self.main_model = main_model
        self.vision_model = vision_model
        self.context: Dict[int, list] = {}  # chat_id -> messages
        logger.info(f"Агент создан с моделями: основная={main_model}, зрение={vision_model}")
    
    def set_main_model(self, model_name: str):
        """Установка основной модели"""
        self.main_model = model_name
        logger.info(f"Установлена основная модель: {model_name}")
    
    def set_vision_model(self, model_name: str):
        """Установка модели для работы с изображениями"""
        self.vision_model = model_name
        logger.info(f"Установлена модель для работы с изображениями: {model_name}")
    
    async def get_response(self, chat_id: int, message: str, image_path: Optional[str] = None) -> str:
        """Получение ответа от модели"""
        try:
            # Если есть изображение, используем модель с поддержкой зрения
            if image_path:
                logger.info(f"Запрос к модели {self.vision_model} с изображением")
                return await self._get_vision_response(message, image_path)
            
            # Иначе используем основную модель
            logger.info(f"Запрос к модели {self.main_model}")
            return await self._get_text_response(message)
            
        except Exception as e:
            logger.error(f"Ошибка при получении ответа: {e}")
            return "Произошла ошибка при обработке запроса. Попробуйте позже."
    
    async def _get_text_response(self, message: str) -> str:
        """Получение ответа на текстовый запрос"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.main_model,
                    "prompt": message,
                    "stream": True
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["response"]
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка API: {error_text}")
                    raise Exception(f"API вернул статус {response.status}")
    
    async def _get_vision_response(self, message: str, image_path: str) -> str:
        """Получение ответа на запрос с изображением"""
        # Проверяем поддержку изображений
        if not await model_manager.check_model_vision_support(self.vision_model):
            return "Эта модель не поддерживает работу с изображениями"
        
        # Формируем запрос с изображением
        with open(image_path, "rb") as img:
            image_base64 = base64.b64encode(img.read()).decode("utf-8")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.vision_model,
                    "prompt": message,
                    "images": [image_base64],
                    "stream": False
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["response"]
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка API: {error_text}")
                    raise Exception(f"API вернул статус {response.status}")
    
    def clear_context(self, chat_id: int):
        """Очистка контекста для указанного чата"""
        if chat_id in self.context:
            del self.context[chat_id]
            logger.info(f"Контекст для чата {chat_id} очищен") 