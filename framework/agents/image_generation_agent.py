from aiogram.types import Message
from framework.models.image_generation.stable_diffusion import StableDiffusionHandler
import logging
import asyncio

logger = logging.getLogger(__name__)

class ImageGenerationAgent:
    def __init__(self, bot, model_id: str = "D:\\SD3\\Data\\Models\\StableDiffusion\\waiNSFWIllustrious_v110.safetensors"):
        """Initialize the image generation agent.
        
        Args:
            bot: The Telegram bot instance
            model_id (str): Путь к локальной модели или ID модели с Hugging Face
        """
        self.bot = bot
        self.sd_handler = StableDiffusionHandler(model_id)
        
    async def handle_generate_command(self, message: Message):
        """Handle the /generate command.
        
        Args:
            message (Message): The Telegram message
        """
        try:
            # Get the prompt from the message
            prompt = message.text.replace("/generate", "").strip()
            
            if not prompt:
                await message.answer(
                    "Пожалуйста, укажите описание изображения после команды /generate\n"
                    "Например: /generate красивая кошка на закате"
                )
                return
            
            # Send "generating" message
            status_message = await message.answer("🎨 Генерирую изображение... Это может занять несколько минут.")
            
            try:
                # Generate the image in a separate thread to avoid blocking
                image_bytes = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.sd_handler.generate_image,
                    prompt
                )
                
                # Send the generated image
                await message.answer_photo(
                    photo=image_bytes,
                    caption=f"🎨 Сгенерировано по запросу: {prompt}"
                )
                
            except Exception as e:
                logger.error(f"Error generating image: {str(e)}")
                await message.answer(
                    "Произошла ошибка при генерации изображения. "
                    "Пожалуйста, попробуйте позже или измените запрос."
                )
            finally:
                # Delete the status message
                await status_message.delete()
            
        except Exception as e:
            logger.error(f"Error in handle_generate_command: {str(e)}")
            await message.answer(
                "Произошла ошибка при обработке команды. "
                "Пожалуйста, попробуйте позже."
            ) 