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
        
    async def process_message(self, text: str, user_id: int) -> str:
        """Обработка текстового сообщения"""
        try:
            # Формируем промпт для анализа сообщения
            prompt = f"""Проанализируй сообщение пользователя и сформируй ответ на русском языке.
            Сообщение: {text}
            
            Требования к ответу:
            1. Ответ должен быть кратким и по существу
            2. Используй дружелюбный тон
            3. Если это приветствие, ответь приветствием
            4. Если это вопрос, дай краткий ответ
            5. Если это прощание, попрощайся
            6. Не используй эмодзи в ответе
            7. Не добавляй лишних деталей
            8. Не используй оценочные суждения
            9. Не используй технические термины
            10. Не используй сленг или неформальные выражения
            
            Ответ:"""
            
            # Получаем ответ от модели
            response = await self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False
            )
            
            if not response:
                self.logger.error("Пустой ответ от модели")
                return "Извините, я не смог обработать ваше сообщение. Попробуйте еще раз."
                
            if not isinstance(response, dict) or 'response' not in response:
                self.logger.error(f"Некорректный формат ответа от модели: {response}")
                return "Извините, произошла ошибка при обработке ответа. Попробуйте еще раз."
                
            return response['response'].strip()
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке сообщения: {str(e)}", exc_info=True)
            return "Извините, произошла ошибка при обработке сообщения. Попробуйте еще раз."

    async def get_response(self, message: str) -> str:
        """Получает ответ от модели"""
        try:
            # Генерируем ответ
            response = await self.ollama_client.generate(
                model=self.model_name,
                prompt=message,
                stream=False
            )
            
            if not response:
                self.logger.error("Пустой ответ от модели")
                return "Извините, я не смог обработать ваше сообщение. Попробуйте еще раз."
                
            if not isinstance(response, dict) or 'response' not in response:
                self.logger.error(f"Некорректный формат ответа от модели: {response}")
                return "Извините, произошла ошибка при обработке ответа. Попробуйте еще раз."
                
            return response['response'].strip()
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации ответа: {str(e)}", exc_info=True)
            return "Извините, произошла ошибка при обработке сообщения. Попробуйте еще раз."
        
    def is_bot_mentioned(self, message: str) -> bool:
        """Проверка, упомянут ли бот в сообщении"""
        return (
            f"@{self.bot_username}" in message or
            self.bot_name.lower() in message.lower()
        )
        
    def is_private_chat(self, chat_id: int) -> bool:
        """Проверка, является ли чат приватным"""
        return chat_id > 0  # В Telegram приватные чаты имеют положительный ID 