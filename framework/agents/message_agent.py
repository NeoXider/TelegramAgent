import json
import logging
from typing import Dict, Any, Optional
from framework.agents.base import BaseAgent

class MessageAgent(BaseAgent):
    """Агент для обработки текстовых сообщений"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_name = config["bot"]["name"]
        self.bot_username = config["bot"]["username"]
        self.logger = logging.getLogger(__name__)
        
    async def process_message(self, message: str, chat_id: int, message_id: int) -> dict:
        """Обработка текстового сообщения"""
        try:
            # Анализируем сообщение
            analysis = await self.think(message, chat_id, message_id)
            
            # Если нужно изображение
            if analysis.get("needs_image"):
                return {
                    "action": "request_image",
                    "text": "Пожалуйста, отправьте изображение для анализа"
                }
                
            # Если нужна дополнительная информация
            if analysis.get("needs_additional_info"):
                return {
                    "action": "request_info",
                    "text": analysis.get("additional_info", "Нужна дополнительная информация")
                }
                
            # Генерируем ответ
            response = await self.get_response(message, chat_id, message_id)
            return response
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке сообщения: {str(e)}")
            return {
                "action": "send_message",
                "text": "Произошла ошибка при обработке сообщения"
            }
            
    def is_bot_mentioned(self, message: str) -> bool:
        """Проверка, упомянут ли бот в сообщении"""
        return (
            f"@{self.bot_username}" in message or
            self.bot_name.lower() in message.lower()
        )
        
    def is_private_chat(self, chat_id: int) -> bool:
        """Проверка, является ли чат приватным"""
        return chat_id > 0  # В Telegram приватные чаты имеют положительный ID 