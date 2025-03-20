import logging
import json
import base64
from typing import Dict, Any, Optional
from framework.agents.base import BaseAgent
from framework.agents.message_agent import MessageAgent
from framework.ollama_client import ollama_client

logger = logging.getLogger(__name__)

class ImageAgent(BaseAgent):
    """Агент для обработки изображений"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_name = config.get('models', {}).get('image', config.get('models', {}).get('default', 'gemma3:12b'))
        self.message_agent = MessageAgent(config)
        self.max_retries = 3  # Максимальное количество попыток генерации на русском
        
    def _is_russian(self, text: str) -> bool:
        """Проверяет, содержит ли текст хотя бы одну кириллическую букву"""
        return any('а' <= char.lower() <= 'я' for char in text)
        
    async def process_image(self, image_content: bytes, user_id: int, message_id: int) -> Dict[str, Any]:
        """Обработка изображения"""
        try:
            logger.info(f"Начало обработки изображения от пользователя {user_id}")
            
            # Проверяем содержимое изображения
            if not image_content:
                logger.error("Получено пустое содержимое изображения")
                return {
                    "action": "send_message",
                    "text": "Ой-ой! 😢 Слайм не может найти изображение. Может быть, попробуем другое? 🎨"
                }
            
            # Сохраняем исходное изображение для повторных попыток
            original_image = image_content
            
            logger.info("Начало анализа изображения")
            # Анализируем изображение с несколькими попытками
            for attempt in range(self.max_retries):
                analysis = await self.think(original_image)
                
                if not analysis:
                    continue
                
                if analysis:
                    self._add_to_memory(0, "user", "Пользователь отправил изображение")
                    self._add_to_memory(0, "assistant", analysis)
                    logger.info("Изображение успешно проанализировано")
                    logger.debug(f"Ответ для пользователя:\n{analysis}")
                    return {"action": "send_message", "text": analysis}
            
            # Если все попытки исчерпаны
            logger.error("Исчерпаны все попытки получить ответ на русском языке")
            return {
                "action": "send_message",
                "text": "Извините, у меня возникли проблемы с описанием изображения на русском языке. Давайте попробуем еще раз! 🌟"
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке изображения: {str(e)}", exc_info=True)
            return {
                "action": "send_message",
                "text": "Ой-ой! 😱 Что-то пошло не так при анализе картинки. Давай попробуем еще раз! 🌟"
            }
            
    async def think(self, image_content: bytes) -> Optional[str]:
        """Анализ изображения с помощью модели"""
        try:
            logger.info("Начало анализа изображения")
            
            # Читаем содержимое из BytesIO если необходимо
            if hasattr(image_content, 'read'):
                image_bytes = image_content.read()
            else:
                image_bytes = image_content
            
            # Проверяем размер изображения
            content_size = len(image_bytes)
            logger.info(f"Размер изображения: {content_size} байт")
            
            if content_size > 1024 * 1024:  # Если больше 1MB
                logger.warning("Изображение слишком большое, попытка сжатия")
                # TODO: Добавить сжатие изображения
            
            # Конвертируем изображение в base64
            try:
                image_base64 = base64.b64encode(image_bytes).decode('utf-8').replace('\n', '').replace('\r', '').strip()
                logger.info(f"Изображение успешно конвертировано в base64, размер: {len(image_base64)}")
            except Exception as e:
                logger.error(f"Ошибка при конвертации в base64: {str(e)}")
                return None
            
            prompt_text ="\nИспользуя изображение, переданное через параметр 'image', опиши, что на нем изображено. Ответ должен содержать уникальное и подробное описание изображения, без шаблонных фраз. Обязательно отвечай только на русском языке!"
            response = await ollama_client.generate_with_image(
                prompt=prompt_text,
                image=image_base64
            )
            
            if not response:
                logger.error("Получен пустой ответ от модели")
                return None
            
            # Очищаем ответ от HTML-тегов и специальных символов
            cleaned_response = response.replace("<br>", "\n").replace("</br>", "\n")
            cleaned_response = cleaned_response.replace("<br/>", "\n").replace("<br />", "\n")
            
            # Логируем часть ответа (первые 200 символов)
            preview = cleaned_response[:200] + "..." if len(cleaned_response) > 200 else cleaned_response
            logger.info(f"Предпросмотр ответа модели:\n{preview}")
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения: {str(e)}", exc_info=True)
            return None 