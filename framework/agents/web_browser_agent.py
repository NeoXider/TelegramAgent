import logging
from typing import Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
from .base import BaseAgent
import os
from urllib.parse import urlparse, urljoin
import json

logger = logging.getLogger(__name__)

class WebBrowserAgent(BaseAgent):
    """Агент для работы с веб-страницами"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.screenshot_dir = os.path.join('data', 'temp', 'screenshots')
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    async def visit_url(self, url: str, with_images: bool = True) -> Dict[str, Any]:
        """Получение содержимого веб-страницы"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string if soup.title else ""
            content = soup.get_text(separator="\n")
            return {"title": title, "content": content}
        except Exception as e:
            logger.error(f"Ошибка при получении страницы: {e}")
            raise
    
    async def process_message(self, message: str, chat_id: int = None, message_id: int = None) -> dict:
        """Обработка сообщения"""
        try:
            # Проверяем, является ли сообщение URL
            if not message.startswith(('http://', 'https://')):
                return {
                    "action": "send_message",
                    "text": "Пожалуйста, отправьте корректный URL"
                }

            # Получаем содержимое страницы
            page_content = await self.visit_url(message, True)
            if not page_content:
                return {
                    "action": "send_message",
                    "text": "Не удалось получить содержимое страницы"
                }

            # Анализируем содержимое с помощью модели
            response = await self.think(
                f"Analyze webpage content: {json.dumps(page_content)}",
                chat_id,
                message_id
            )
            return response

        except Exception as e:
            logger.error(f"Ошибка при обработке URL: {e}")
            return {
                "action": "send_message",
                "text": "Произошла ошибка при обработке страницы"
            } 