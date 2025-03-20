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
        """Обрабатывает входящее сообщение и возвращает ответ"""
        try:
            self.logger.info(f"Обработка сообщения: {message}")
            self._add_to_memory(chat_id, "user", message)
            try:
                response = await self.think(message, chat_id, message_id)
                if response is None or not isinstance(response, dict):
                    self.logger.error(f"Некорректный ответ от агента: {response}")
                    return {"action": "send_message", "text": "Произошла ошибка при генерации ответа. Попробуйте еще раз."}
                if response.get("needs_image") == True:
                    response["action"] = "request_image"
                else:
                    if response.get("action") == "send_message":
                        self._add_to_memory(chat_id, "assistant", response.get("text", ""))
                return response
            except Exception as e:
                self.logger.error(f"Ошибка при получении ответа: {str(e)}")
                return {"action": "send_message", "text": f"Произошла ошибка при обработке сообщения: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Ошибка при обработке сообщения: {str(e)}")
            return {"action": "send_message", "text": "Произошла непредвиденная ошибка. Попробуйте позже."}

    async def get_response(self, message: str) -> str:
        """Получает ответ от модели"""
        try:
            # Генерируем ответ
            response = await self.ollama_client.generate(message)
            if not response:
                raise ValueError("Пустой ответ от модели")
            return response
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации ответа: {str(e)}")
            raise
        
    def is_bot_mentioned(self, message: str) -> bool:
        """Проверка, упомянут ли бот в сообщении"""
        return (
            f"@{self.bot_username}" in message or
            self.bot_name.lower() in message.lower()
        )
        
    def is_private_chat(self, chat_id: int) -> bool:
        """Проверка, является ли чат приватным"""
        return chat_id > 0  # В Telegram приватные чаты имеют положительный ID 