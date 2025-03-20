import logging
import sys
from typing import Optional, Dict, Any
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from framework.handlers.message_handlers import MessageHandlers

class BotManager:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any]):
        if not BotManager._initialized:
            self.config = config
            self.logger = logging.getLogger(__name__)
            self.bot: Optional[Bot] = None
            self.dp: Optional[Dispatcher] = None
            self._handlers: Optional[MessageHandlers] = None
            BotManager._initialized = True
    
    async def initialize(self) -> None:
        """Инициализация бота и диспетчера"""
        if self.bot is not None:
            self.logger.warning("Bot is already initialized")
            return
            
        try:
            self.logger.info("Initializing bot...")
            
            # Проверяем наличие токена
            if not self.config['bot']['token']:
                self.logger.error("Bot token is not set in configuration")
                raise ValueError("Bot token is not set in configuration")
            
            # Создаем бота с правильными настройками
            self.bot = Bot(
                token=self.config['bot']['token'],
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            
            # Создаем диспетчер
            self.dp = Dispatcher()
            
            # Инициализируем обработчики
            try:
                self._handlers = MessageHandlers(self.config)
                # Устанавливаем бота в обработчики
                self._handlers.bot = self.bot
            except Exception as e:
                self.logger.error(f"Failed to initialize message handlers: {e}")
                raise
            
            # Регистрируем обработчики
            try:
                self._register_handlers()
            except Exception as e:
                self.logger.error(f"Failed to register message handlers: {e}")
                raise
            
            self.logger.info("Bot successfully initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}")
            # Очищаем ресурсы при ошибке
            if self.bot:
                await self.bot.session.close()
            raise
    
    def _register_handlers(self) -> None:
        """Регистрация всех обработчиков сообщений"""
        if not self._handlers or not self.dp:
            raise RuntimeError("Handlers or dispatcher not initialized")
            
        try:
            self.logger.info("Начало регистрации обработчиков...")
            
            # Регистрируем обработчики команд
            self.logger.debug("Регистрация обработчиков команд")
            self.dp.message.register(
                self._handlers.handle_command_start,
                Command(commands=["start"])
            )
            self.dp.message.register(
                self._handlers.handle_command_help,
                Command(commands=["help"])
            )
            self.dp.message.register(
                self._handlers.handle_command_search,
                Command(commands=["search"])
            )
            
            # Регистрируем обработчики для приватных чатов
            self.logger.debug("Регистрация обработчиков для приватных чатов")
            self.dp.message.register(
                self._handlers.handle_private_message,
                F.chat.type == "private",
                ~Command(commands=["start", "help", "search"]),
                F.text
            )
            
            # Регистрируем обработчик фотографий для приватных чатов
            self.logger.debug("Регистрация обработчика фотографий для приватных чатов")
            self.dp.message.register(
                self._handlers.handle_photo,
                F.chat.type == "private",
                F.photo
            )
            
            # Регистрируем обработчик документов для приватных чатов
            self.logger.debug("Регистрация обработчика документов для приватных чатов")
            self.dp.message.register(
                self._handlers.handle_document,
                F.chat.type == "private",
                F.document
            )
            
            # Регистрируем обработчики для групповых чатов
            self.logger.debug("Регистрация обработчиков для групповых чатов")
            self.dp.message.register(
                self._handlers.handle_group_message,
                (F.chat.type == "group") | (F.chat.type == "supergroup"),
                ~Command(commands=["start", "help", "search"]),
                F.text
            )
            
            # Регистрируем обработчик фотографий для групповых чатов
            self.logger.debug("Регистрация обработчика фотографий для групповых чатов")
            self.dp.message.register(
                self._handlers.handle_photo,
                (F.chat.type == "group") | (F.chat.type == "supergroup"),
                F.photo
            )
            
            # Регистрируем обработчик документов для групповых чатов
            self.logger.debug("Регистрация обработчика документов для групповых чатов")
            self.dp.message.register(
                self._handlers.handle_document,
                (F.chat.type == "group") | (F.chat.type == "supergroup"),
                F.document
            )
            
            self.logger.info("Все обработчики успешно зарегистрированы")
            
        except Exception as e:
            self.logger.error(f"Ошибка при регистрации обработчиков: {e}", exc_info=True)
            raise
    
    async def start(self) -> None:
        """Запуск бота"""
        if not self.bot or not self.dp:
            raise RuntimeError("Bot not initialized. Call initialize() first")
            
        try:
            self.logger.info("Starting bot...")
            await self.dp.start_polling(
                self.bot,
                allowed_updates=self.dp.resolve_used_update_types()
            )
        except Exception as e:
            self.logger.error(f"Error while running bot: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Остановка бота"""
        if self.dp:
            try:
                self.logger.info("Stopping bot...")
                await self.dp.stop_polling()
                
                if self.bot:
                    await self.bot.session.close()
                    
                self.logger.info("Bot stopped successfully")
            except Exception as e:
                self.logger.error(f"Error while stopping bot: {e}")
                raise 