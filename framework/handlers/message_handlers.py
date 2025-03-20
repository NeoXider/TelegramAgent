import json
import os
import logging
from typing import Dict, Any, Optional
from aiogram import types
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.enums import ChatType
from framework.agents.base import BaseAgent
from framework.agents.message_agent import MessageAgent
from framework.agents.image_agent import ImageAgent
from framework.agents.document_agent import DocumentAgent
from framework.agents.web_search_agent import WebSearchAgent
from framework.agents.web_browser_agent import WebBrowserAgent
from framework.services.file_service import FileService
from framework.utils.logger import setup_logger

# Настраиваем логгер
logger = logging.getLogger(__name__)

class MessageHandlers:
    """Обработчики сообщений для бота"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.file_service = FileService(config)
        self.bot = None  # Будет установлен позже из BotManager
        self.agents = {
            'document': DocumentAgent(config),
            'image': ImageAgent(config),
            'web_search': WebSearchAgent(config),
            'web_browser': WebBrowserAgent(config),
            'message': MessageAgent(config)
        }

    async def handle_command_start(self, message: Message, command: CommandObject) -> Dict[str, Any]:
        """Обработка команды /start"""
        response = ("Привет! Я бот-ассистент. Я могу:\n"
                   "- Анализировать изображения\n"
                   "- Обрабатывать документы\n"
                   "- Искать информацию в интернете\n"
                   "Просто отправьте мне сообщение, фото или документ!")
        
        if message.chat.type != ChatType.PRIVATE:
            await message.reply(response)
        else:
            await message.answer(response)
        return {"action": "send_message", "text": response}

    async def handle_command_help(self, message: Message, command: CommandObject) -> Dict[str, Any]:
        """Обработка команды /help"""
        response = ("Доступные команды:\n"
                   "/start - Начать работу с ботом\n"
                   "/help - Показать это сообщение\n"
                   "/search <запрос> - Поиск в интернете")
        
        if message.chat.type != ChatType.PRIVATE:
            await message.reply(response)
        else:
            await message.answer(response)
        return {"action": "send_message", "text": response}

    async def handle_command_search(self, message: Message, command: CommandObject) -> Dict[str, Any]:
        """Обработка команды /search"""
        query = command.args
        if not query:
            response = "Пожалуйста, укажите поисковый запрос после команды /search"
        else:
            try:
                search_response = await self.agents['web_search'].process_message(query, message.from_user.id, message.chat.id)
                response = search_response.get("text", "Ошибка при выполнении поиска")
            except Exception as e:
                self.logger.error(f"Ошибка при выполнении поиска: {str(e)}")
                response = "Ошибка при выполнении поиска"
        
        if message.chat.type != ChatType.PRIVATE:
            await message.reply(response)
        else:
            await message.answer(response)
        return {"action": "send_message", "text": response}

    async def handle_message(self, message: Message) -> Dict[str, Any]:
        """Обработка текстового сообщения"""
        if message.chat.type == ChatType.PRIVATE:
            return await self.handle_private_message(message)
        else:
            return await self.handle_group_message(message)
        
    async def handle_private_message(self, message: Message) -> None:
        """Обработка приватных сообщений"""
        try:
            logger.info(f"Получено приватное сообщение: {message.text}")
            
            # Обрабатываем сообщение через агента
            response = await self.agents['message'].process_message(
                message=message.text,
                chat_id=message.chat.id,
                message_id=message.message_id
            )
            
            # Отправляем ответ
            await message.answer(response)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке приватного сообщения: {str(e)}")
            await message.answer("Извините, произошла ошибка при обработке сообщения. Попробуйте позже.")
            
    async def handle_group_message(self, message: Message) -> None:
        """Обработка сообщения в групповом чате"""
        try:
            # Проверяем упоминание бота
            if not await self._is_bot_mentioned(message):
                return

            # Удаляем упоминание бота из текста
            text = message.text
            bot_username = self.config['bot']['username']
            bot_name = self.config['bot']['name']
            text = text.replace(f"@{bot_username}", "").replace(bot_name, "").strip()

            # Обрабатываем сообщение
            response = await self.agents['message'].process_message(text, message.from_user.id, message.chat.id)
            if response and response.get('text'):
                await message.reply(response['text'])

        except Exception as e:
            logger.error(f"Ошибка при обработке группового сообщения: {e}")
            await message.reply("Произошла ошибка при обработке сообщения")
            
    async def handle_photo(self, message: Message) -> None:
        """Обработка фотографий"""
        try:
            logger.info(f"Получено фото от пользователя {message.from_user.id} в чате {message.chat.id}")
            
            if not self.bot:
                logger.error("Бот не инициализирован в MessageHandlers")
                await message.answer("Извините, произошла ошибка инициализации. Попробуйте позже.")
                return
            
            # Получаем содержимое фото
            photo_data = await self.file_service.get_photo_content(message, self.bot)
            if not photo_data:
                await message.answer("Ой-ой! 😢 Не удалось получить фотографию. Попробуйте отправить её еще раз!")
                return
                
            if 'error' in photo_data:
                await message.answer(photo_data['message'])
                return
                
            # Обрабатываем фото через ImageAgent
            try:
                response = await self.agents['image'].process_image(
                    photo_data['content'],
                    message.from_user.id,
                    message.message_id
                )
                
                if not response or 'text' not in response:
                    logger.error("Получен некорректный ответ от ImageAgent")
                    await message.answer("Извините, произошла ошибка при анализе изображения 😔")
                    return
                    
                logger.info("Отправка успешного ответа пользователю")
                logger.debug(f"Текст ответа:\n{response['text']}")
                
                # Отправляем ответ, заменяя HTML-теги на обычные переносы строк
                text = response['text'].replace("<br>", "\n").replace("</br>", "\n")
                text = text.replace("<br/>", "\n").replace("<br />", "\n")
                
                await message.answer(text)
                
            except Exception as e:
                logger.error(f"Ошибка при обработке изображения: {str(e)}", exc_info=True)
                await message.answer("Произошла ошибка при обработке изображения. Попробуйте другое фото! 🎨")
                
        except Exception as e:
            logger.error(f"Критическая ошибка при обработке фото: {str(e)}", exc_info=True)
            await message.answer("Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")
            
    async def handle_document(self, message: Message) -> None:
        """Обработка документа"""
        try:
            # В групповом чате проверяем упоминание бота
            if message.chat.type != 'private':
                if not await self._is_bot_mentioned(message):
                    return

            # Получаем содержимое документа через FileService
            doc_data = await self.file_service.get_document_content(message, message.bot)
            
            if not doc_data:
                error_message = "Ой-ой! 😅 Слайм не видит документ. Пожалуйста, отправьте файл еще раз! 📄"
                if message.chat.type != 'private':
                    await message.reply(error_message)
                else:
                    await message.answer(error_message)
                return
                
            if 'error' in doc_data:
                if message.chat.type != 'private':
                    await message.reply(doc_data['message'])
                else:
                    await message.answer(doc_data['message'])
                return

            # Отправляем сообщение о начале обработки
            processing_message = "Слайм внимательно изучает документ... 🔍"
            sent_message = await message.answer(processing_message) if message.chat.type == 'private' else await message.reply(processing_message)

            # Обрабатываем документ через DocumentAgent
            response = await self.agents['document'].process_document(
                doc_data['content'],
                message.from_user.id,
                message.chat.id
            )
            
            # Удаляем сообщение о процессе обработки
            try:
                await sent_message.delete()
            except Exception as e:
                self.logger.warning(f"Не удалось удалить сообщение о процессе: {e}")
            
            if response and response.get('text'):
                if message.chat.type != 'private':
                    await message.reply(response['text'])
                else:
                    await message.answer(response['text'])
            else:
                error_message = "Ой-ой! 😢 Слайм не смог обработать документ. Может быть, попробуем другой? 📄"
                if message.chat.type != 'private':
                    await message.reply(error_message)
                else:
                    await message.answer(error_message)

        except Exception as e:
            logger.error(f"Ошибка при обработке документа: {e}")
            error_message = "Произошла ошибка при обработке документа. Попробуйте позже."
            if message.chat.type != 'private':
                await message.reply(error_message)
            else:
                await message.answer(error_message)
        
    def _is_group_allowed(self, chat_id: int) -> bool:
        """Проверка, разрешена ли группа"""
        allowed_groups = self.config['bot'].get('allowed_groups', [])
        return not allowed_groups or chat_id in allowed_groups
        
    async def _is_bot_mentioned(self, message: Message) -> bool:
        """Проверка упоминания бота в сообщении"""
        if not message.text and not message.caption:
            return False

        text = message.text or message.caption
        bot_username = self.config['bot']['username']
        bot_name = self.config['bot']['name']

        # Проверяем упоминание в тексте
        text_lower = text.lower()
        return (
            f"@{bot_username}".lower() in text_lower or
            bot_name.lower() in text_lower
        )
        
    async def _remove_bot_mention(self, message: Message) -> str:
        """Удаление упоминания бота из текста"""
        if not message.text:
            return ""
            
        bot = await message.bot.get_me()
        bot_username = bot.username.lower()
        text = message.text
        
        # Удаляем команду с упоминанием бота
        if text.lower().startswith(f"/{bot_username}"):
            text = text[len(bot_username) + 1:].strip()
            
        # Удаляем обычное упоминание
        if message.entities:
            for entity in reversed(message.entities):
                if entity.type == "mention":
                    mention = text[entity.offset:entity.offset + entity.length]
                    if mention.lower() == f"@{bot_username}":
                        text = text[:entity.offset].strip() + " " + text[entity.offset + entity.length:].strip()
                    
        return text.strip() 