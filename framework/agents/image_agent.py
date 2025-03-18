import os
import json
import logging
from typing import Dict, Any
from framework.agents.base import BaseAgent

class ImageAgent(BaseAgent):
    """Агент для обработки изображений"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    async def process_image(self, image_path: str, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Обрабатывает изображение"""
        try:
            # Анализируем изображение
            try:
                analysis_data = await self.analyze_image(image_path)
            except Exception as e:
                self.logger.error(f"Ошибка при обработке изображения: {str(e)}")
                return {
                    "action": "send_message",
                    "text": "Произошла ошибка при обработке изображения"
                }
            
            if not analysis_data or analysis_data.get("action") == "send_message" and "Произошла ошибка" in analysis_data.get("text", ""):
                return {
                    "action": "send_message",
                    "text": "Произошла ошибка при обработке изображения"
                }
            
            # Проверяем, нужна ли дополнительная информация
            if analysis_data.get("needs_additional_info"):
                return {
                    "action": "request_info",
                    "text": analysis_data["additional_info"]
                }
                
            # Возвращаем результат анализа
            return analysis_data
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке изображения: {str(e)}")
            return {
                "action": "send_message",
                "text": "Произошла ошибка при обработке изображения"
            } 