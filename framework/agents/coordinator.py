import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from framework.agents.image_agent import ImageAgent
from framework.agents.message_agent import MessageAgent
from framework.agents.think_agent import ThinkAgent
from aiogram import Bot

logger = logging.getLogger(__name__)

class AgentCoordinator:
    """Координатор для управления агентами"""
    
    def __init__(self, config: Dict[str, Any], bot: Optional[Bot] = None):
        self.config = config
        self.bot = bot
        self.image_agent = ImageAgent(config)
        self.message_agent = MessageAgent(config)
        self.think_agent = ThinkAgent(config)
        self.logger = logging.getLogger(__name__)
        self.response_callbacks = []
        
    def add_response_callback(self, callback: Callable[[int, str], None]):
        """Добавление callback для отправки ответов"""
        self.response_callbacks.append(callback)
        
    async def send_response(self, user_id: int, text: str):
        """Отправка ответа через все доступные интерфейсы"""
        if self.bot:
            try:
                await self.bot.send_message(user_id, text)
            except Exception as e:
                self.logger.error(f"Ошибка при отправке через бот: {str(e)}")
        
        for callback in self.response_callbacks:
            try:
                callback(user_id, text)
            except Exception as e:
                self.logger.error(f"Ошибка в callback: {str(e)}")
        
    async def process_image(self, image_content: bytes, user_id: int, message_id: int, caption: str = "") -> Dict[str, Any]:
        """Обработка изображения: ImageAgent получает описание изображения. Далее это описание комбинируется с текстом от пользователя и системными промптами, и передается в ThinkAgent для формирования финального ответа."""
        try:
            image_result = await self.image_agent.process_image(
                image_content=image_content,
                user_id=user_id,
                message_id=message_id
            )
            if image_result.get("action") != "send_message":
                self.logger.error("Неожиданный результат от ImageAgent")
                await self.send_response(user_id, "Извините, произошла ошибка при обработке изображения. Попробуйте еще раз! 🌟")
                return {"action": "send_message", "text": "Ошибка при обработке изображения."}

            # Извлекаем описание, полученное от ImageAgent
            analysis = image_result.get("text", "")
            if not analysis:
                self.logger.error("Пустой ответ от ImageAgent")
                await self.send_response(user_id, "Извините, не удалось получить описание изображения. Попробуйте еще раз! 🌟")
                return {"action": "send_message", "text": "Ошибка при обработке изображения."}

            # Формируем комбинированный prompt для ThinkAgent
            combined_prompt = "Описание изображения: " + analysis
            if caption:
                combined_prompt += "\nСообщение пользователя: " + caption
            combined_prompt += "\nПожалуйста, сначала проверь полученное описание изображения. Если оно выглядит неструктурированным, содержит лишние или случайные символы, отфильтруй его, оставив только осмысленное описание. Затем, используя очищенное описание, сформируй краткий и понятный финальный ответ на русском языке, без лишних деталей и оценочных суждений."

            think_result = await self.think_agent.think(combined_prompt)
            if not think_result:
                self.logger.error("ThinkAgent не смог сформировать финальный ответ")
                await self.send_response(user_id, "Извините, у меня возникли проблемы с анализом изображения. Попробуйте еще раз! 🌟")
                return {"action": "send_message", "text": "Проблемы с анализом изображения."}

            await self.send_response(user_id, think_result)
            return {"action": "send_message", "text": think_result}
        except Exception as e:
            self.logger.error(f"Ошибка при обработке изображения: {str(e)}", exc_info=True)
            await self.send_response(user_id, "Ой-ой! 😢 Что-то пошло не так при обработке изображения. Давайте попробуем еще раз! 🎨")
            return {"action": "send_message", "text": "Ошибка при обработке изображения."}
        
    async def process_message(self, message: str, user_id: int, message_id: int) -> Dict[str, Any]:
        """Обработка текстового сообщения напрямую с использованием результата ThinkAgent"""
        try:
            think_result = await self.think_agent.think(message)
            if not think_result:
                self.logger.error("ThinkAgent не смог проанализировать сообщение")
                await self.send_response(user_id, "Извините, у меня возникли проблемы с анализом сообщения. Попробуйте еще раз! 🌟")
                return {"action": "send_message", "text": "Проблемы с анализом сообщения."}
                
            await self.send_response(user_id, think_result)
            return {"action": "send_message", "text": think_result}
        except Exception as e:
            self.logger.error(f"Ошибка при обработке сообщения: {str(e)}", exc_info=True)
            await self.send_response(user_id, "Ой-ой! 😢 Что-то пошло не так при обработке сообщения. Давайте попробуем еще раз! 🌟")
            return {"action": "send_message", "text": "Ошибка при обработке сообщения."}
        
    async def start(self):
        """Запуск координатора агентов (минимальный)"""
        self.logger.info("Координатор агентов запущен.") 