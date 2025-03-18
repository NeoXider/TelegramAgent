from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.enums import ParseMode
from pathlib import Path

from ..config import WELCOME_CONFIG, BASE_DIR
from ..utils.logger import setup_logger

logger = setup_logger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    try:
        # Проверяем, включено ли приветствие
        if not WELCOME_CONFIG["enabled"]:
            return

        # Получаем путь к изображению
        image_path = Path(BASE_DIR) / WELCOME_CONFIG["image_path"]
        
        # Отправляем изображение если оно существует
        if image_path.exists():
            photo = FSInputFile(image_path)
            await message.answer_photo(
                photo,
                caption=WELCOME_CONFIG["message"] if WELCOME_CONFIG["show_commands"] else None,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            logger.info(f"Отправлено приветственное изображение пользователю {message.from_user.id}")
        else:
            # Если изображения нет, отправляем только текст
            await message.answer(
                WELCOME_CONFIG["message"] if WELCOME_CONFIG["show_commands"] else "Привет\\! 👋",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            logger.warning(f"Приветственное изображение не найдено: {image_path}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке приветствия: {e}")
        await message.answer("Привет\\! 👋", parse_mode=ParseMode.MARKDOWN_V2)

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    try:
        await message.answer(
            WELCOME_CONFIG["message"],
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.info(f"Отправлено справочное сообщение пользователю {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке справки: {e}")
        await message.answer("Извините, произошла ошибка при отправке справки\\.") 