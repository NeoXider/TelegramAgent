import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from framework.agents.coordinator import AgentCoordinator
from framework.utils.logger import setup_logger
from framework.utils.config import load_config
import os
from dotenv import load_dotenv
from framework.utils.prompt_generator import PromptGenerator

# Загружаем переменные окружения
load_dotenv()

# Инициализируем логгер
logger = setup_logger()

# Загружаем конфигурацию
config = load_config()

# Инициализируем бота и диспетчер
bot = Bot(
    token=os.getenv("TELEGRAM_BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Инициализируем координатор агентов
coordinator = AgentCoordinator(config, bot)

# Регистрируем обработчики команд
@dp.message(Command("start"))
async def handle_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! 👋 Я бот-ассистент, который может:\n"
        "1. Отвечать на ваши сообщения\n"
        "2. Анализировать изображения\n"
        "3. Генерировать изображения по описанию\n\n"
        "Просто напишите мне что-нибудь или отправьте изображение!"
    )

@dp.message(Command("help"))
async def handle_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "🤖 Доступные команды:\n\n"
        "📝 Основные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/generate &lt;описание&gt; - Сгенерировать изображение по описанию\n\n"
        "🔄 Управление моделями:\n"
        "/models - Показать список доступных моделей\n"
        "/setmodel &lt;название&gt; - Установить модель по умолчанию\n"
        "/current - Показать текущую активную модель\n\n"
        "💡 Примеры запросов:\n"
        "1. Напиши стихотворение о весне\n"
        "2. Объясни, как работает фотосинтез\n"
        "3. Нарисуй красивый закат над горами\n\n"
        "📸 Работа с изображениями:\n"
        "• Отправьте изображение для его анализа\n"
        "• Используйте команду /generate или ключевые слова 'нарисуй', 'сгенерируй', 'создай' для генерации изображений"
    )

@dp.message(Command("generate"))
async def handle_generate(message: Message):
    """Обработчик команды /generate"""
    try:
        # Извлекаем промпт из сообщения
        prompt = message.text.replace("/generate", "").strip()
        
        if not prompt:
            await message.answer(
                "Пожалуйста, добавьте описание того, что нужно нарисовать.\n"
                "Например: /generate красивый закат над горами"
            )
            return
            
        await coordinator.generate_image(message, prompt)
        
    except Exception as e:
        logger.error(f"Error in handle_generate: {str(e)}")
        await message.answer("Произошла ошибка при генерации изображения. Попробуйте еще раз.")

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
        # Получаем информацию о фото
        photo = message.photo[-1]  # Берем самое большое фото
        file_id = photo.file_id
        
        # Получаем файл
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Скачиваем файл
        file_bytes = await bot.download_file(file_path)
        
        # Обрабатываем изображение
        result = await coordinator.process_image(file_bytes, message.from_user.id, message.message_id, message.caption or "")
        if result.get("action") == "send_message":
            await message.answer(result["text"])
            
    except Exception as e:
        logger.error(f"Error in handle_photo: {str(e)}")
        await message.answer("Произошла ошибка при обработке изображения. Попробуйте еще раз.")

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
            
        # Проверяем, является ли сообщение ответом на сообщение бота
        if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
            # Обрабатываем как обычное сообщение
            result = await coordinator.process_message(message.text, message.from_user.id, message.message_id)
            if result.get("action") == "send_message":
                await message.answer(result["text"])
            return
            
        # Проверяем наличие ключевых слов для генерации изображения
        prompt = coordinator.prompt_agent.extract_prompt(message.text)
        if prompt:
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
        logger.info("Загрузка модели генерации изображений...")
        await coordinator.image_generator.load_model()
        logger.info("Бот успешно запущен")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())