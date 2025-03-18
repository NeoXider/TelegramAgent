import os
import json
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from framework.handlers.message_handlers import MessageHandlers
from framework.utils.logger import setup_logger
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Загрузка конфигурации
def load_config():
    """Загрузка конфигурации из файла"""
    try:
        with open('config/bot_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Заменяем токен из конфига на токен из .env
            config['bot']['token'] = os.getenv('TELEGRAM_BOT_TOKEN')
            return config
    except Exception as e:
        print(f"Ошибка при загрузке конфигурации: {str(e)}")
        raise

# Инициализация бота
async def init_bot():
    """Инициализация бота и диспетчера"""
    config = load_config()
    
    # Настраиваем логгер
    logger = setup_logger(config)
    logger.info("Запуск бота...")
    
    try:
        # Создаем бота и диспетчер
        bot = Bot(token=config['bot']['token'])
        dp = Dispatcher()
        
        # Создаем обработчики сообщений
        handlers = MessageHandlers(config)
        
        # Регистрируем обработчики
        dp.message.register(handlers.handle_message, F.text)
        dp.message.register(handlers.handle_photo, F.photo)
        dp.message.register(handlers.handle_document, F.document)
        
        logger.info("Бот успешно инициализирован")
        return dp, bot
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации бота: {str(e)}")
        raise

async def main():
    try:
        # Инициализируем бота
        dp, bot = await init_bot()
        
        # Запускаем бота
        await dp.start_polling(bot)
        
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        import traceback
        print("Детали ошибки:")
        print(traceback.format_exc())
        raise

if __name__ == '__main__':
    asyncio.run(main())