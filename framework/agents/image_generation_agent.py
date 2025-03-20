from aiogram.types import Message
from framework.models.image_generation.stable_diffusion import StableDiffusionHandler
import logging
import asyncio
import os

logger = logging.getLogger(__name__)

class ImageGenerationAgent:
    def __init__(self, bot):
        """Initialize the image generation agent.
        
        Args:
            bot: The Telegram bot instance
        """
        self.bot = bot
        self.sd_handler = StableDiffusionHandler()
        
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
                image_path = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.sd_handler.generate_image,
                    prompt
                )
                
                if image_path and os.path.exists(image_path):
                    # Send the generated image using FSInputFile
                    from aiogram.types import FSInputFile
                    await message.answer_photo(
                        photo=FSInputFile(image_path),
                        caption=f"🎨 Сгенерировано по запросу: {prompt}"
                    )
                    # Clean up the file after sending
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        logger.error(f"Error removing temporary file: {str(e)}")
                else:
                    raise Exception("Failed to generate image")
                
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