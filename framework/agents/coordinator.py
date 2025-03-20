import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from framework.agents.image_agent import ImageAgent
from framework.agents.message_agent import MessageAgent
from framework.agents.think_agent import ThinkAgent
from framework.models.image_generation.stable_diffusion import StableDiffusionHandler
from aiogram import Bot
from aiogram.types import Message, InputFile
from aiogram.types import FSInputFile
from io import BytesIO
from aiogram.types import BufferedInputFile
import os

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
        
        # Инициализируем ollama_client
        from framework.ollama_client import ollama_client
        self.ollama_client = ollama_client
        
        # Инициализируем генератор изображений
        self.image_generator = StableDiffusionHandler()
        
        # Устанавливаем модели из конфига
        self._update_models()
        
    def _update_models(self):
        """Обновляет модели у всех агентов"""
        default_model = self.config.get('models', {}).get('default', 'gemma3:latest')
        self.image_agent.model_name = default_model
        self.message_agent.model_name = default_model
        self.think_agent.model_name = default_model
        
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
            # Сохраняем информацию о последнем обработанном сообщении
            self.last_processed_message = {
                'message_id': message_id,
                'user_id': user_id
            }
            
            image_result = await self.image_agent.process_image(
                image_content=image_content,
                user_id=user_id,
                message_id=message_id
            )
            if image_result.get("action") != "send_message":
                self.logger.error("Неожиданный результат от ImageAgent")
                return {"action": "send_message", "text": "Извините, произошла ошибка при обработке изображения. Попробуйте еще раз! 🌟"}

            # Извлекаем описание, полученное от ImageAgent
            analysis = image_result.get("text", "")
            if not analysis:
                self.logger.error("Пустой ответ от ImageAgent")
                return {"action": "send_message", "text": "Извините, не удалось получить описание изображения. Попробуйте еще раз! 🌟"}

            # Формируем комбинированный prompt для ThinkAgent
            combined_prompt = "Описание изображения: " + analysis
            if caption:
                combined_prompt += "\nСообщение пользователя: " + caption
            combined_prompt += "\nПожалуйста, сначала проверь полученное описание изображения. Если оно выглядит неструктурированным, содержит лишние или случайные символы, отфильтруй его, оставив только осмысленное описание. Затем, используя очищенное описание, сформируй краткий и понятный финальный ответ на русском языке, без лишних деталей и оценочных суждений."

            think_result = await self.think_agent.think(combined_prompt)
            if not think_result:
                self.logger.error("ThinkAgent не смог сформировать финальный ответ")
                return {"action": "send_message", "text": "Извините, у меня возникли проблемы с анализом изображения. Попробуйте еще раз! 🌟"}

            return {"action": "send_message", "text": think_result}
        except Exception as e:
            self.logger.error(f"Ошибка при обработке изображения: {str(e)}", exc_info=True)
            return {"action": "send_message", "text": "Ой-ой! 😢 Что-то пошло не так при обработке изображения. Давайте попробуем еще раз! 🎨"}
        finally:
            # Очищаем информацию о последнем обработанном сообщении
            self.last_processed_message = None
        
    async def process_message(self, text: str, user_id: int, message_id: int) -> Dict[str, Any]:
        """Обработка текстового сообщения"""
        try:
            # Пропускаем обработку, если сообщение уже обработано как изображение
            if hasattr(self, 'last_processed_message') and self.last_processed_message.get('message_id') == message_id:
                return {"action": "none"}
                
            # Обрабатываем сообщение через ThinkAgent
            think_result = await self.think_agent.think(text)
            if not think_result:
                self.logger.error("ThinkAgent не смог сформировать ответ")
                error_message = "Извините, у меня возникли проблемы с анализом сообщения. Попробуйте еще раз! 🌟"
                return {"action": "send_message", "text": error_message}
                
            return {
                "action": "send_message",
                "text": think_result
            }
            
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            error_message = "Произошла ошибка при обработке сообщения. Попробуйте позже."
            return {
                "action": "send_message",
                "text": error_message
            }

    async def process_document(self, message: Message, user_id: int, message_id: int) -> Dict[str, Any]:
        """Обработка документа"""
        try:
            # Проверяем, является ли документ изображением
            if not message.document.mime_type.startswith('image/'):
                await self.send_response(user_id, "Извините, я могу обрабатывать только изображения. Пожалуйста, отправьте файл в формате изображения (jpg, png, gif и т.д.).")
                return {"action": "send_message", "text": "Неподдерживаемый формат файла."}

            # Получаем содержимое документа
            file = await self.bot.get_file(message.document.file_id)
            if not file:
                self.logger.error("Не удалось получить информацию о файле")
                await self.send_response(user_id, "Ой-ой! 😢 Не удалось получить файл. Попробуйте отправить документ еще раз!")
                return {"action": "send_message", "text": "Ошибка при получении файла."}

            # Скачиваем содержимое файла
            file_content = await self.bot.download_file(file.file_path)
            if not file_content:
                self.logger.error("Не удалось скачать файл")
                await self.send_response(user_id, "Ой-ой! 😢 Не удалось скачать файл. Попробуйте отправить документ еще раз!")
                return {"action": "send_message", "text": "Ошибка при скачивании файла."}

            # Обрабатываем изображение через ImageAgent
            return await self.process_image(
                image_content=file_content,
                user_id=user_id,
                message_id=message_id
            )

        except Exception as e:
            self.logger.error(f"Ошибка при обработке документа: {str(e)}", exc_info=True)
            await self.send_response(user_id, "Ой-ой! 😢 Что-то пошло не так при обработке документа. Давайте попробуем еще раз! 📄")
            return {"action": "send_message", "text": "Ошибка при обработке документа."}
        
    async def generate_image(self, message: Message, prompt: str, negative_prompt: str = None, width: int = None, height: int = None) -> None:
        """Generate and send an image based on the prompt."""
        try:
            # Отправляем сообщение о начале генерации
            status_message = await self.bot.send_message(
                chat_id=message.chat.id,
                text="🎨 Начинаю генерацию изображения... Это может занять некоторое время."
            )

            # Генерируем изображение
            image_path = await self.image_generator.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height
            )
            
            # Удаляем статусное сообщение
            try:
                await status_message.delete()
            except Exception as e:
                logger.error(f"Error deleting status message: {str(e)}")
            
            if image_path and os.path.exists(image_path):
                # Отправляем изображение
                try:
                    await self.bot.send_photo(
                        chat_id=message.chat.id,
                        photo=FSInputFile(image_path),
                        caption=f"🎨 Сгенерировано по запросу: {prompt}"
                    )
                    # Удаляем временный файл после отправки
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        logger.error(f"Error removing temporary file: {str(e)}")
                except Exception as e:
                    logger.error(f"Error sending photo: {str(e)}")
                    await self.bot.send_message(
                        chat_id=message.chat.id,
                        text="Не удалось отправить сгенерированное изображение. Попробуйте еще раз."
                    )
            else:
                await self.bot.send_message(
                    chat_id=message.chat.id,
                    text="Не удалось сгенерировать изображение. Попробуйте изменить запрос."
                )
                
        except Exception as e:
            logger.error(f"Error in generate_image: {str(e)}")
            await self.bot.send_message(
                chat_id=message.chat.id,
                text="Произошла ошибка при генерации изображения. Попробуйте позже или измените запрос."
            )
        
    async def start(self):
        """Запуск координатора агентов (минимальный)"""
        self.logger.info("Координатор агентов запущен.") 