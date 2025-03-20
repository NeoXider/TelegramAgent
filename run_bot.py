import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.enums import ParseMode
from framework.agents.coordinator import AgentCoordinator
from framework.agents.image_generation_agent import ImageGenerationAgent
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
coordinator = AgentCoordinator(config, bot)

# Регистрируем обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! Я Слайм, твой дружелюбный помощник! 🎨\n"
        "Отправь мне изображение или сообщение, и я помогу тебе с ним разобраться! 🌟\n\n"
        "Доступные команды:\n"
        "/help - Показать все команды\n"
        "/models - Показать доступные модели\n"
        "/setmodel <название> - Установить модель\n"
        "/current - Показать текущую модель\n"
        "/generate <описание> - Сгенерировать изображение по описанию"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "🤖 Команды бота:\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/models - Показать доступные модели\n"
        "/setmodel <название> - Установить модель\n"
        "/current - Показать текущую модель\n"
        "/generate <описание> - Сгенерировать изображение по описанию"
    )

@dp.message(Command("generate"))
async def handle_generate(message: Message):
    """Handle the /generate command."""
    try:
        # Получаем промпт из сообщения
        prompt = message.text.replace("/generate", "").strip()
        
        if not prompt:
            await message.answer(
                "Пожалуйста, укажите описание изображения после команды /generate\n"
                "Например: /generate красивый закат над горами"
            )
            return
        
        # Генерируем изображение через координатор
        await coordinator.generate_image(
            message=message,
            prompt=prompt
        )
        
    except Exception as e:
        logger.error(f"Error in handle_generate: {str(e)}")
        await message.answer("Произошла ошибка при обработке команды. Попробуйте позже.")

@dp.message(Command("models"))
async def cmd_models(message: Message):
    """Обработчик команды /models"""
    try:
        # Получаем список моделей через Ollama API
        models = await coordinator.ollama_client.list_models()
        
        if not models:
            await message.answer("😢 К сожалению, список моделей недоступен.")
            return

        response = "📚 Доступные модели:\n\n"
        for model in models:
            name = model.get('name', 'Неизвестная модель')
            size = model.get('size', 0)
            modified_at = model.get('modified_at', '')
            
            # Форматируем размер в читаемый вид
            size_str = f"{size / (1024*1024*1024):.1f} GB" if size > 0 else "Неизвестно"
            
            response += f"• {name}\n"
            response += f"  Размер: {size_str}\n"
            if modified_at:
                response += f"  Обновлено: {modified_at}\n"
            response += "\n"

        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка моделей: {str(e)}")
        await message.answer(
            "😢 Произошла ошибка при получении списка моделей. "
            "Пожалуйста, попробуйте позже."
        )

@dp.message(Command("setmodel"))
async def cmd_setmodel(message: Message, command: CommandObject):
    """Обработчик команды /setmodel"""
    try:
        if not command.args:
            await message.answer(
                "❌ Пожалуйста, укажите название модели.\n"
                "Пример: /setmodel gemma3:12b"
            )
            return
            
        model_name = command.args.strip()
        
        # Получаем список доступных моделей
        models = await coordinator.ollama_client.list_models()
        available_models = [model.get('name') for model in models]
        
        if model_name not in available_models:
            await message.answer(
                f"❌ Модель '{model_name}' не найдена.\n"
                "Используйте /models для просмотра доступных моделей."
            )
            return

        # Обновляем модель в конфиге
        coordinator.config['models']['default'] = model_name
        
        # Обновляем модель у агентов
        coordinator._update_models()

        await message.answer(f"✅ Модель успешно изменена на {model_name}!")
        
    except Exception as e:
        logger.error(f"Ошибка при смене модели: {str(e)}")
        await message.answer(
            "😢 Произошла ошибка при смене модели. "
            "Пожалуйста, попробуйте позже."
        )

@dp.message(Command("current"))
async def cmd_current(message: Message):
    """Обработчик команды /current"""
    try:
        current_model = coordinator.config.get('models', {}).get('default', 'gemma3:12b')
        
        # Получаем список моделей
        models = await coordinator.ollama_client.list_models()
        
        # Ищем информацию о текущей модели
        model_info = next((model for model in models if model.get('name') == current_model), None)
        
        if not model_info:
            await message.answer(f"❓ Текущая модель: {current_model}")
            return

        # Форматируем размер в читаемый вид
        size = model_info.get('size', 0)
        size_str = f"{size / (1024*1024*1024):.1f} GB" if size > 0 else "Неизвестно"
        
        response = f"🤖 Текущая модель:\n"
        response += f"• {model_info['name']}\n"
        response += f"• Размер: {size_str}\n"
        if model_info.get('modified_at'):
            response += f"• Обновлено: {model_info['modified_at']}"

        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Ошибка при получении информации о текущей модели: {str(e)}")
        await message.answer(
            "😢 Произошла ошибка при получении информации о модели. "
            "Пожалуйста, попробуйте позже."
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

@dp.message(F.document)
async def handle_document(message: Message):
    """Обработчик документов"""
    try:
        # Обрабатываем документ через MessageHandlers
        result = await coordinator.process_document(
            message=message,
            user_id=message.from_user.id,
            message_id=message.message_id
        )
        
        # Отправляем ответ
        if result["action"] == "send_message":
            await message.answer(result["text"])
            
    except Exception as e:
        logger.error(f"Ошибка при обработке документа: {str(e)}", exc_info=True)
        await message.answer(
            "Ой-ой! 😢 Что-то пошло не так при обработке документа. "
            "Попробуй еще раз! 📄"
        )

@dp.message()
async def handle_text(message: Message):
    """Обработчик текстовых сообщений"""
    try:
        # Проверяем, не является ли сообщение командой
        if message.text.startswith('/'):
            return
            
        text = message.text.lower()
        # Проверяем наличие ключевых слов для генерации изображения
        if any(keyword in text for keyword in ['нарисуй', 'сгенерируй', 'создай']):
            # Извлекаем промпт после ключевого слова
            prompt = message.text
            for keyword in ['нарисуй', 'сгенерируй', 'создай']:
                if keyword in text:
                    prompt = message.text[message.text.lower().find(keyword) + len(keyword):].strip()
                    break
            
            if not prompt:
                await message.answer("Пожалуйста, добавьте описание того, что нужно нарисовать. Например: нарисуй красивый закат над горами")
                return
                
            await coordinator.generate_image(message, prompt)
            return
            
        # Если это не запрос на генерацию изображения, обрабатываем как обычное сообщение
        result = await coordinator.process_message(message.text, message.from_user.id, message.message_id)
        if result.get("action") == "send_message":
            await message.answer(result["text"])
            
    except Exception as e:
        logger.error(f"Error in handle_text: {str(e)}")
        await message.answer("Произошла ошибка при обработке сообщения. Попробуйте позже.")

async def main():
    """Основная функция запуска бота"""
    try:
        logger.info("Запуск бота...")
        
        # Загружаем модель генерации изображений при запуске
        logger.info("Загрузка модели генерации изображений...")
        await coordinator.image_generator.load_model()
        logger.info("Модель генерации изображений загружена")
        
        # Запускаем бота
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}", exc_info=True)
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())