import logging
from typing import Dict, Any, List
import aiohttp
from bs4 import BeautifulSoup
from .base import BaseAgent
import json

logger = logging.getLogger(__name__)

class WebSearchAgent(BaseAgent):
    """Агент для веб-поиска"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.search_engine = config.get('search_engine', 'https://www.google.com/search')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Выполнение поискового запроса"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {'q': query}
                async with session.get(self.search_engine, headers=self.headers, params=params) as response:
                    html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            # Пробуем найти ссылки выдачи
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/url?q='):
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    title = a.get_text().strip()
                    if title and actual_url:
                        results.append({"title": title, "url": actual_url})
                if len(results) >= limit:
                    break
            return results
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            raise
    
    async def process_message(self, message: str, chat_id: int = None, message_id: int = None) -> dict:
        """Обработка поискового запроса"""
        try:
            # Выполняем поиск
            search_results = await self.search(message, 5)
            if not search_results:
                return {
                    "action": "send_message",
                    "text": "По вашему запросу ничего не найдено"
                }

            # Анализируем результаты с помощью модели
            response = await self.think(
                f"Analyze search results: {json.dumps(search_results)}",
                chat_id,
                message_id
            )
            return response

        except Exception as e:
            logger.error(f"Ошибка при выполнении поиска: {e}")
            return {
                "action": "send_message",
                "text": "Произошла ошибка при выполнении поиска"
            } 