from aiogram import Router
from .start_handlers import router as start_router
from .model_handlers import router as model_router
from .message_handlers import router as message_router
from .memory_handlers import router as memory_router
from .help_handlers import router as help_router
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Создаем основной роутер
router = Router()

# Подключаем все роутеры
logger.info("Подключение роутеров...")
router.include_router(start_router)
router.include_router(model_router)
router.include_router(message_router)
router.include_router(memory_router)
router.include_router(help_router)
logger.info("Роутеры успешно подключены")

__all__ = ['router'] 