import asyncio
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from interfaces.config import (
    TELEGRAM_BOT_TOKEN,
    WEBHOOK_HOST,
    WEBHOOK_PORT,
    WEBHOOK_URL_BASE,
    DEFAULT_MODELS
)
from interfaces.handlers import router
from interfaces.utils.logger import setup_logger
from interfaces.utils.model_manager import model_manager
from interfaces.utils.webhook import (
    setup_webhook_app,
    on_startup,
    on_shutdown,
    get_ssl_context
)
from interfaces.utils.middleware import AgentMiddleware
from interfaces.agent_base import AgentBase

logger = setup_logger(__name__)

async def setup_agent_models():
    """Проверяет доступность моделей по умолчанию"""
    logger.info("Проверка доступности моделей по умолчанию...")
    
    for model_type, model_name in DEFAULT_MODELS.items():
        logger.info(f"Проверка модели {model_name} для {model_type}")
        
        # Проверяем доступность модели
        if not await model_manager.ensure_model_loaded(model_name):
            logger.error(f"Модель {model_name} недоступна")
            return False
            
        # Для модели зрения проверяем поддержку изображений
        if model_type == "зрение":
            if not await model_manager.check_model_vision_support(model_name):
                logger.error(f"Модель {model_name} не поддерживает работу с изображениями")
                return False
            logger.info(f"Модель {model_name} доступна и поддерживает изображения")
        else:
            logger.info(f"Модель {model_name} доступна")
    
    return True

async def main():
    """Основная функция запуска бота в режиме webhook"""
    logger.info("Инициализация бота в режиме webhook...")
    
    # Инициализация бота и диспетчера
    default = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=TELEGRAM_BOT_TOKEN, default=default)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Создаем агента
    agent = AgentBase(DEFAULT_MODELS["основная"], DEFAULT_MODELS["зрение"])
    
    # Регистрируем middleware
    dp.update.outer_middleware(AgentMiddleware(agent))
    
    # Регистрируем роутер
    dp.include_router(router)
    
    # Проверяем доступность моделей
    if not await setup_agent_models():
        logger.error("Не удалось инициализировать модели")
        await bot.session.close()
        sys.exit(1)
    
    # Настраиваем webhook приложение
    app = setup_webhook_app(bot, dp)
    
    # Настраиваем запуск и остановку webhook
    app.on_startup.append(lambda app: on_startup(app['bot']))
    app.on_shutdown.append(lambda app: on_shutdown(app['bot']))
    
    # Запускаем webhook сервер
    logger.info(f"Запуск webhook сервера на {WEBHOOK_HOST}:{WEBHOOK_PORT}")
    web.run_app(
        app,
        host=WEBHOOK_HOST,
        port=WEBHOOK_PORT,
        ssl_context=get_ssl_context()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен") 