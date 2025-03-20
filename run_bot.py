import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from framework.agents.coordinator import AgentCoordinator
from framework.utils.logger import setup_logger
from framework.utils.config import load_config
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Инициализируем логгер
logger = setup_logger()

# Загружаем конфигурацию
config = load_config()

# Инициализируем бота и диспетчер
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()

# Инициализируем координатор агентов
coordinator = AgentCoordinator(config)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! Я Слайм, твой дружелюбный помощник! 🎨\n"
        "Отправь мне изображение или сообщение, и я помогу тебе с ним разобраться! 🌟"
    )

@dp.message(F.photo)
async def handle_photo(message: Message):
    """Обработчик фотографий"""
    try:
        # Получаем фото максимального размера
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        
        # Скачиваем фото
        photo_bytes = await bot.download_file(file.file_path)
        
        # Обрабатываем фото через координатор
        result = await coordinator.process_image(
            image_content=photo_bytes,
            user_id=message.from_user.id,
            message_id=message.message_id
        )
        
        # Отправляем ответ
        if result["action"] == "send_message":
            await message.answer(result["text"])
            
    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {str(e)}", exc_info=True)
        await message.answer(
            "Ой-ой! 😢 Что-то пошло не так при обработке фото. "
            "Попробуй еще раз или отправь другое изображение! 🎨"
        )

@dp.message(F.text)
async def handle_text(message: Message):
    """Обработчик текстовых сообщений"""
    try:
        # Обрабатываем сообщение через координатор
        result = await coordinator.process_message(
            message=message.text,
            user_id=message.from_user.id,
            message_id=message.message_id
        )
        
        # Отправляем ответ
        if result["action"] == "send_message":
            await message.answer(result["text"])
            
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}", exc_info=True)
        await message.answer(
            "Ой-ой! 😢 Что-то пошло не так при обработке сообщения. "
            "Попробуй еще раз! 🌟"
        )

async def main():
    """Основная функция запуска бота"""
    try:
        logger.info("Запуск бота...")
        
        # Запускаем бота
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}", exc_info=True)
        raise
    finally:
        cleanup()

if __name__ == "__main__":
    asyncio.run(main())