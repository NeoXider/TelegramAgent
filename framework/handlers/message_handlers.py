import json
import os
import logging
from typing import Dict, Any
from aiogram import types
from aiogram.filters import Command
from aiogram.types import Message
from framework.agents.base import BaseAgent
from framework.agents.message_agent import MessageAgent
from framework.agents.image_agent import ImageAgent
from framework.agents.document_agent import DocumentAgent
from framework.agents.web_search_agent import WebSearchAgent
from framework.agents.web_browser_agent import WebBrowserAgent
from framework.utils.logger import setup_logger

# Настраиваем логгер
logger = logging.getLogger(__name__)

class MessageHandlers:
    """Обработчики сообщений для бота"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.agents = {
            'document': DocumentAgent(config),
            'image': ImageAgent(config),
            'web_search': WebSearchAgent(config),
            'web_browser': WebBrowserAgent(config),
            'message': MessageAgent(config)
        }
        
    async def handle_message(self, message: Message) -> Dict[str, Any]:
        """Обработка текстового сообщения"""
        try:
            text = message.text
            if not text:
                return {"action": "ignore"}
                
            # Проверяем, является ли чат групповым и есть ли упоминание бота
            if not message.chat.type == "private" and not any(entity.type == "mention" for entity in message.entities):
                return {"action": "ignore"}
                
            self.logger.info(f"Получено текстовое сообщение: {text[:100]}...")
            
            # Проверяем, является ли сообщение командой
            if text.startswith('/'):
                return await self._handle_command(message)
            else:
                # Обрабатываем обычное сообщение через MessageAgent
                response = await self.agents['message'].process_message(text, message.from_user.id, message.chat.id)
                await message.answer(response["text"])
                return response
                
        except Exception as e:
            self.logger.error(f"Ошибка при обработке сообщения: {str(e)}")
            await message.answer("Произошла ошибка при обработке сообщения. Попробуйте позже.")
            return {"action": "send_message", "text": "Произошла ошибка при обработке сообщения"}
            
    async def handle_photo(self, message: Message) -> Dict[str, Any]:
        """Обработка фото"""
        try:
            photo = message.photo[-1]
            file_id = photo.file_id
            if not file_id:
                return {"action": "ignore"}
                
            self.logger.info(f"Получено фото: {file_id}")
            
            # Обрабатываем фото через ImageAgent
            response = await self.agents['image'].process_image(file_id, message.from_user.id, message.chat.id)
            await message.answer(response["text"])
            return response
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке фото: {str(e)}")
            await message.answer("Произошла ошибка при обработке фото. Попробуйте позже.")
            return {"action": "send_message", "text": "Произошла ошибка при обработке фото"}
            
    async def handle_document(self, message: Message) -> Dict[str, Any]:
        """Обработка документа"""
        try:
            document = message.document
            file_id = document.file_id
            if not file_id:
                return {"action": "ignore"}
                
            self.logger.info(f"Получен документ: {document.file_name} ({file_id})")
            
            # Обрабатываем документ через DocumentAgent
            response = await self.agents['document'].process_document(file_id, message.from_user.id, message.chat.id)
            await message.answer(response["text"])
            return response
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке документа: {str(e)}")
            await message.answer("Произошла ошибка при обработке документа. Попробуйте позже.")
            return {"action": "send_message", "text": "Произошла ошибка при обработке документа"}

    async def _handle_command(self, message: Message) -> Dict[str, Any]:
        """Обработка команд"""
        command = message.text.split()[0].lower()
        
        if command == '/start':
            await message.answer("Привет! Я бот-ассистент. Я могу:\n"
                               "- Анализировать изображения\n"
                               "- Обрабатывать документы\n"
                               "- Искать информацию в интернете\n"
                               "Просто отправьте мне сообщение, фото или документ!")
            return {"action": "send_message", "text": "Приветственное сообщение"}
        elif command == '/help':
            await message.answer("Доступные команды:\n"
                               "/start - Начать работу с ботом\n"
                               "/help - Показать это сообщение\n"
                               "/search <запрос> - Поиск в интернете")
            return {"action": "send_message", "text": "Справка"}
        elif command == '/search':
            query = ' '.join(message.text.split()[1:])
            if not query:
                await message.answer("Пожалуйста, укажите поисковый запрос после команды /search")
                return {"action": "send_message", "text": "Пустой поисковый запрос"}
            else:
                response = await self.agents['web_search'].process_message({"text": query})
                if response.get("status") == "error":
                    await message.answer(response["message"])
                    return {"action": "send_message", "text": response["message"]}
                await message.answer(response["message"])
                return {"action": "send_message", "text": response["message"]}
        else:
            await message.answer("Неизвестная команда. Используйте /help для просмотра доступных команд.")
            return {"action": "send_message", "text": "Неизвестная команда"} 