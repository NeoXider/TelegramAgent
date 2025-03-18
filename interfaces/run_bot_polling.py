import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from interfaces.config import TELEGRAM_BOT_TOKEN, DEFAULT_MODELS
from interfaces.handlers import router
from interfaces.utils.logger import setup_logger
from interfaces.utils.model_manager import model_manager
from interfaces.utils.middleware import AgentMiddleware
from interfaces.agent_base import AgentBase
from interfaces.utils.global_model_manager import GlobalModelManager

logger = setup_logger(__name__)

# Инициализация глобального менеджера моделей
global_model_manager = GlobalModelManager()

async def setup_agent_models():
    """Проверяет доступность моделей по умолчанию"""
    logger.info("Проверка доступности моделей...")
    
    # Получаем текущие модели или используем модели по умолчанию
    models = global_model_manager.get_all_models()
    main_model = models.get("основная") or DEFAULT_MODELS["основная"]
    vision_model = models.get("зрение") or DEFAULT_MODELS["зрение"]
    
    # Сохраняем модели, если они не были установлены
    if not models.get("основная"):
        global_model_manager.set_model("основная", main_model)
    if not models.get("зрение"):
        global_model_manager.set_model("зрение", vision_model)
    
    # Проверяем доступность основной модели
    logger.info(f"Проверка основной модели {main_model}")
    if not await model_manager.ensure_model_loaded(main_model):
        logger.error(f"Модель {main_model} недоступна")
        return False
    logger.info(f"Основная модель {main_model} доступна")
    
    # Проверяем модель для изображений
    logger.info(f"Проверка модели для изображений {vision_model}")
    if not await model_manager.ensure_model_loaded(vision_model):
        logger.error(f"Модель {vision_model} недоступна")
        return False
    
    if not await model_manager.check_model_vision_support(vision_model):
        logger.error(f"Модель {vision_model} не поддерживает работу с изображениями")
        return False
    logger.info(f"Модель {vision_model} доступна и поддерживает изображения")
    
    return True

async def main():
    """Основная функция запуска бота в режиме polling"""
    logger.info("Инициализация бота в режиме polling...")
    
    # Инициализация бота и диспетчера
    default = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=TELEGRAM_BOT_TOKEN, default=default)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Получаем текущие модели
    models = global_model_manager.get_all_models()
    main_model = models.get("основная") or DEFAULT_MODELS["основная"]
    vision_model = models.get("зрение") or DEFAULT_MODELS["зрение"]
    
    # Создаем агента с текущими моделями
    agent = AgentBase(main_model, vision_model)
    
    # Регистрируем middleware
    dp.update.outer_middleware(AgentMiddleware(agent))
    
    # Регистрируем роутер
    dp.include_router(router)
    
    # Проверяем доступность моделей
    if not await setup_agent_models():
        logger.error("Не удалось инициализировать модели")
        await bot.session.close()
        sys.exit(1)
    
    # Запускаем бота
    logger.info("Запуск бота в режиме polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен") 