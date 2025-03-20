import logging
from typing import Optional, Dict, Any
from aiogram import Bot
from aiogram.types import Message

logger = logging.getLogger(__name__)

class FileService:
    """Сервис для работы с файлами"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_file_size = config.get('file_limits', {}).get('max_size', 20 * 1024 * 1024)  # 20MB по умолчанию
        
    async def get_photo_content(self, message: Message, bot: Bot) -> Optional[Dict[str, Any]]:
        """Получение содержимого фото из сообщения"""
        try:
            if not message.photo:
                logger.warning("Сообщение не содержит фото")
                return None
                
            # Берем самую качественную версию фото
            photo = message.photo[-1]
            logger.info(f"Получено фото: file_id={photo.file_id}, размер={photo.file_size}, разрешение={photo.width}x{photo.height}")
            
            # Проверяем размер файла
            if photo.file_size and photo.file_size > self.max_file_size:
                logger.warning(f"Файл слишком большой: {photo.file_size} байт")
                return {
                    'error': 'size_limit',
                    'message': "Ой-ой! 😅 Фотография слишком большая. Пожалуйста, отправьте картинку поменьше! 🖼️"
                }
            
            # Получаем файл
            file = await bot.get_file(photo.file_id)
            if not file:
                logger.error("Не удалось получить информацию о файле")
                return {
                    'error': 'file_not_found',
                    'message': "Ой-ой! 😢 Не удалось получить файл. Попробуйте отправить фото еще раз!"
                }
                
            # Скачиваем содержимое файла
            file_content = await bot.download_file(file.file_path)
            if not file_content:
                logger.error("Не удалось скачать файл")
                return {
                    'error': 'download_failed',
                    'message': "Ой-ой! 😢 Не удалось скачать файл. Попробуйте отправить фото еще раз!"
                }
                
            return {
                'file_id': photo.file_id,
                'file_size': photo.file_size,
                'width': photo.width,
                'height': photo.height,
                'content': file_content,
                'mime_type': 'image/jpeg'  # Telegram конвертирует все фото в JPEG
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении фото: {str(e)}", exc_info=True)
            return {
                'error': 'unknown',
                'message': "Ой-ой! 😱 Что-то пошло не так при получении фото. Попробуйте еще раз!"
            }
            
    async def get_document_content(self, message: Message, bot: Bot) -> Optional[Dict[str, Any]]:
        """Получение содержимого документа из сообщения"""
        try:
            if not message.document:
                logger.warning("Сообщение не содержит документ")
                return None
                
            document = message.document
            logger.info(f"Получен документ: file_id={document.file_id}, размер={document.file_size}, имя={document.file_name}")
            
            # Проверяем размер файла
            if document.file_size and document.file_size > self.max_file_size:
                logger.warning(f"Файл слишком большой: {document.file_size} байт")
                return {
                    'error': 'size_limit',
                    'message': "Ой-ой! 😅 Документ слишком большой. Пожалуйста, отправьте файл поменьше!"
                }
            
            # Получаем файл
            file = await bot.get_file(document.file_id)
            if not file:
                logger.error("Не удалось получить информацию о файле")
                return {
                    'error': 'file_not_found',
                    'message': "Ой-ой! 😢 Не удалось получить файл. Попробуйте отправить документ еще раз!"
                }
                
            # Скачиваем содержимое файла
            file_content = await bot.download_file(file.file_path)
            if not file_content:
                logger.error("Не удалось скачать файл")
                return {
                    'error': 'download_failed',
                    'message': "Ой-ой! 😢 Не удалось скачать файл. Попробуйте отправить документ еще раз!"
                }
                
            return {
                'file_id': document.file_id,
                'file_size': document.file_size,
                'file_name': document.file_name,
                'mime_type': document.mime_type,
                'content': file_content
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении документа: {str(e)}", exc_info=True)
            return {
                'error': 'unknown',
                'message': "Ой-ой! 😱 Что-то пошло не так при получении документа. Попробуйте еще раз!"
            } 