from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from ..utils.logger import setup_logger
from ..utils.global_model_manager import GlobalModelManager
from ..config import SYSTEM_CONFIG
import re
import time

from framework.agent_base import AIAgent


logger = setup_logger(__name__)

router = Router()

# Инициализация менеджера моделей
global_model_manager = GlobalModelManager()

def escape_markdown(text: str) -> str:
    """Экранирует специальные символы для Markdown V2"""
    # Символы, которые нужно экранировать
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    # Экранируем каждый специальный символ
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text

@router.message()
async def handle_message(message: Message, agent, bot):
    """Обработчик всех сообщений"""
    
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"Бот: {bot_info.username} (ID: {bot_info.id})")
    
    # Проверяем, является ли чат группой
    is_group = message.chat.type in ['group', 'supergroup']
    logger.info(f"Тип чата: {'группа' if is_group else 'личный'} ({message.chat.type})")
    
    # Проверяем, обращаются ли к боту
    is_bot_mentioned = False
    if is_group:
        logger.info("Проверка упоминания бота в групповом чате...")
        
        # Проверяем reply на сообщение бота
        if message.reply_to_message:
            logger.info(f"Найден reply на сообщение. От пользователя: {message.reply_to_message.from_user.id if message.reply_to_message.from_user else 'Unknown'}")
            if message.reply_to_message.from_user:
                is_bot_mentioned = message.reply_to_message.from_user.id == bot_info.id
                logger.info(f"Reply на сообщение бота: {is_bot_mentioned}")
        
        # Проверяем упоминание в тексте
        if message.text and not is_bot_mentioned:
            logger.info(f"Проверка упоминания в тексте: {message.text}")
            mention = f"@{bot_info.username}"
            is_bot_mentioned = mention in message.text
            logger.info(f"Упоминание '{mention}' найдено в тексте: {is_bot_mentioned}")
        
        # Проверяем упоминание в подписи к фото
        if message.caption and not is_bot_mentioned:
            logger.info(f"Проверка упоминания в подписи: {message.caption}")
            mention = f"@{bot_info.username}"
            is_bot_mentioned = mention in message.caption
            logger.info(f"Упоминание '{mention}' найдено в подписи: {is_bot_mentioned}")
    else:
        # В личных сообщениях всегда отвечаем
        is_bot_mentioned = True
        logger.info("Личный чат - всегда отвечаем")

    # Если это группа и бота не упомянули - игнорируем сообщение
    if is_group and not is_bot_mentioned:
        logger.info("Бот не упомянут в групповом чате - игнорируем сообщение")
        return

    # Получаем ID и имя пользователя
    if message.from_user:
        user_name = message.from_user.full_name or message.from_user.username or "Без имени"
        user_id = message.from_user.id
        user_id_name = f"{user_id} ({user_name})"
    else:
        user_id_name = "Unknown"
        user_id = "Unknown"

    # Логируем полученное сообщение
    chat_type = "группе" if is_group else "личке"
    if message.text:
        logger.info(f"Получено текстовое сообщение в {chat_type} от пользователя {user_id_name}: {message.text[:100]}...")
        
        # Проверяем, спрашивает ли пользователь о модели
        if re.search(r'(что\s+ты\s+за\s+модель|какая\s+ты\s+модель)', message.text.lower()):
            models = global_model_manager.get_all_models()
            main_model = models.get("основная", "не установлена")
            vision_model = models.get("зрение", "не установлена")
            
            # Экранируем специальные символы для Markdown
            safe_main = escape_markdown(main_model)
            safe_vision = escape_markdown(vision_model)
            
            response = (
                f"Я использую следующие модели:\n"
                f"\\- Основная модель: `{safe_main}`\n"
                f"\\- Модель для изображений: `{safe_vision}`"
            )
            
            await message.reply(
                response,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
            
    elif message.photo:
        logger.info(f"Получено изображение в {chat_type} от пользователя {user_id_name}")
        if message.caption:
            logger.info(f"Подпись к изображению: {message.caption[:100]}...")
    else:
        logger.info(f"Получено сообщение без текста и изображений в {chat_type} от пользователя {user_id_name}")
        await message.reply(
            escape_markdown("Извините, я могу обрабатывать только текст и изображения."),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    try:
        # Отправляем сообщение о начале обработки
        processing_msg = await message.reply(
            "*Обрабатываю ваш запрос*\\.\\.\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )

        # Получаем путь к изображению, если оно есть
        image_path = None
        if message.photo:
            # Берем последнее (самое качественное) изображение
            photo = message.photo[-1]
            # Скачиваем файл
            file = await message.bot.get_file(photo.file_id)
            downloaded_file = await message.bot.download_file(file.file_path)
            # Сохраняем во временный файл
            image_path = f"temp_{user_id}_{photo.file_id}.jpg"
            with open(image_path, "wb") as f:
                f.write(downloaded_file.read())

        # Очищаем текст от упоминания бота
        text = message.text or message.caption or "Опишите это изображение"
        if is_group:
            original_text = text
            text = text.replace(f"@{bot_info.username}", "").strip()
            logger.info(f"Очистка упоминания бота: '{original_text}' -> '{text}'")

        # Получаем ответ от модели
        logger.info(f"Отправляем запрос модели. ID пользователя: {user_id}, Текст: {text}, Изображение: {'да' if image_path else 'нет'}")
        
        try:
            # Получаем ответ от модели
            response = await agent.get_response(
                chat_id=user_id,
                message=text,
                image_path=image_path
            )
            
            # Экранируем специальные символы в ответе
            safe_response = escape_markdown(response)
            
            # Обновляем сообщение с ответом
            await processing_msg.edit_text(
                safe_response,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            logger.info("Ответ отправлен пользователю")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            await message.reply(
                "*Ошибка*: Произошла ошибка при обработке вашего запроса\\. Попробуйте позже\\.",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            if processing_msg:
                await processing_msg.delete()

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await message.reply(
            "*Ошибка*: Произошла ошибка при обработке вашего запроса\\. Попробуйте позже\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    finally:
        # Удаляем временный файл изображения, если он был создан
        if image_path:
            try:
                import os
                os.remove(image_path)
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла {image_path}: {e}") 