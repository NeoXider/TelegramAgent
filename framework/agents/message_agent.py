import json
import logging
from typing import Dict, Any, Optional
from framework.agents.base import BaseAgent

logger = logging.getLogger(__name__)

class MessageAgent(BaseAgent):
    """Агент для обработки сообщений"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_name = config["bot"]["name"]
        self.bot_username = config["bot"]["username"]
        
    async def process_message(self, message: str, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Обработка сообщения от пользователя"""
        try:
            # Парсим входящее сообщение как JSON
            if isinstance(message, str):
                message_data = json.loads(message)
                message_text = message_data.get("text", "")
            else:
                message_text = message
            
            # Анализируем сообщение
            analysis = await self.think(message_text)
            
            # Определяем действие
            action = analysis.get("action")
            
            if action == "answer":
                response = await self.get_response(message_text)
                return {
                    "action": "send_message",
                    "text": response.get("text", "Не удалось сгенерировать ответ")
                }
                
            elif action == "analyze_image":
                return {
                    "action": "request_image",
                    "text": "Пожалуйста, отправьте изображение для анализа."
                }
                
            elif action == "analyze_file":
                return {
                    "action": "request_file",
                    "text": "Пожалуйста, отправьте файл для анализа."
                }
                
            elif action == "web_search":
                return {
                    "action": "web_search",
                    "query": message_text
                }
                
            elif action == "ask_info":
                return {
                    "action": "send_message",
                    "text": analysis.get("additional_info", "Пожалуйста, уточните детали.")
                }
                
            elif action == "error":
                return {
                    "action": "send_message",
                    "text": f"Произошла ошибка: {analysis.get('error', 'Неизвестная ошибка')}"
                }
                
            else:
                return {
                    "action": "send_message",
                    "text": "Извините, я не смог определить, как обработать ваш запрос."
                }
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {str(e)}")
            return {
                "action": "send_message",
                "text": f"Произошла ошибка при обработке сообщения: {str(e)}"
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