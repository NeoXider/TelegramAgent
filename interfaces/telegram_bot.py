import asyncio
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from typing import Dict, Optional

# Добавляем родительскую директорию в путь Python
sys.path.append(str(Path(__file__).parent.parent))

from framework.agent_base import AIAgent
from interfaces.config import TELEGRAM_BOT_TOKEN, DEFAULT_MODEL, DEFAULT_VISION_MODEL
from interfaces.utils import setup_logger, model_manager
from interfaces.handlers import router
from interfaces.utils.global_model_manager import GlobalModelManager

# Настраиваем логирование
logger = setup_logger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.dp.include_router(router)
        self.global_model_manager = GlobalModelManager()
        self.agents: Dict[int, AIAgent] = {}

    async def setup_agent_models(self) -> bool:
        """Проверка и настройка моделей"""
        models = self.global_model_manager.get_all_models()
        
        # Проверяем, установлены ли модели
        if not models["основная"] or not models["зрение"]:
            logger.error("Модели не настроены. Используйте команду /set_model для настройки моделей")
            return False

        # Проверяем доступность моделей
        try:
            test_agent = AIAgent(
                model_name=models["основная"],
                vision_model_name=models["зрение"]
            )
            # Пробуем выполнить тестовый запрос
            await test_agent.think("test")
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке моделей: {e}")
            return False

    def get_agent(self, user_id: int) -> AIAgent:
        """Получение или создание агента для пользователя"""
        if user_id not in self.agents:
            models = self.global_model_manager.get_all_models()
            self.agents[user_id] = AIAgent(
                model_name=models["основная"],
                vision_model_name=models["зрение"]
            )
        return self.agents[user_id]

    async def start(self):
        """Запуск бота"""
        logger.info("Инициализация бота...")
        
        # Проверяем модели перед запуском
        if not await self.setup_agent_models():
            logger.error("Ошибка при инициализации моделей")
            sys.exit(1)

        # Добавляем middleware для внедрения агента
        @self.dp.update.middleware()
        async def agent_middleware(handler, event, data):
            if isinstance(event, Message):
                data["agent"] = self.get_agent(event.from_user.id)
            return await handler(event, data)

        # Запускаем бота
        logger.info("Бот запущен")
        await self.dp.start_polling(self.bot)

async def main():
    """Основная функция запуска бота"""
    logger.info("Запуск бота")
    try:
        bot = TelegramBot(TELEGRAM_BOT_TOKEN)
        await bot.start()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == '__main__':
    try:
        logger.info("Старт приложения")
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        logger.info("Завершение работы приложения")