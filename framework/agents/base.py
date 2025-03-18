import json
import logging
from typing import Dict, List, Optional, Any
from framework.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class BaseAgent:
    """Базовый класс для всех агентов"""
    
    def __init__(self, config: Dict[str, Any], model_name: Optional[str] = None):
        self.model_name = model_name or config.get('models', {}).get('default', 'llama2')
        self.config = config
        self.ollama_client = OllamaClient()
        self.memory: List[Dict[str, str]] = []
        self.last_analysis: Optional[Dict[str, Any]] = None
        self.last_image_analysis: Optional[Dict[str, Any]] = None
        
    async def think(self, request: str) -> Dict[str, Any]:
        """Анализ запроса и определение необходимых действий"""
        try:
            response = await self.ollama_client.generate(self._create_analysis_prompt(request))
            
            # Если это приветствие или вопрос о возможностях
            if any(word in request.lower() for word in ["привет", "здравствуй", "что ты умеешь", "помощь", "help"]):
                return {
                    "action": "send_message",
                    "text": "Привет! Я бот-ассистент. Я могу:\n"
                           "- Отвечать на вопросы\n"
                           "- Анализировать изображения\n"
                           "- Обрабатывать документы\n"
                           "- Искать информацию в интернете\n\n"
                           "Просто отправьте мне сообщение, фото или документ!"
                }
            
            # Если это запрос на поиск
            if any(word in request.lower() for word in ["найди", "поиск", "search", "ищи"]):
                return {
                    "action": "web_search",
                    "query": request
                }
            
            # Если это запрос на анализ изображения
            if any(word in request.lower() for word in ["фото", "картинк", "изображени", "photo", "image"]):
                return {
                    "action": "request_image",
                    "text": "Пожалуйста, отправьте изображение для анализа."
                }
            
            # Если это запрос на анализ документа
            if any(word in request.lower() for word in ["документ", "файл", "doc", "file"]):
                return {
                    "action": "request_file",
                    "text": "Пожалуйста, отправьте документ для анализа."
                }
            
            # По умолчанию пытаемся дать ответ
            return {
                "action": "answer",
                "text": response
            }
            
        except Exception as e:
            logger.error(f"Ошибка при анализе запроса: {str(e)}")
            return {
                "action": "send_message",
                "text": "Произошла ошибка при анализе запроса. Попробуйте переформулировать."
            }
            
    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Анализ изображения"""
        try:
            response = await self.ollama_client.generate(self._create_image_analysis_prompt(image_path))
            return {
                "action": "send_message",
                "text": response
            }
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения: {str(e)}")
            return {
                "action": "send_message",
                "text": "Произошла ошибка при анализе изображения"
            }
            
    async def get_response(self, request: str) -> Dict[str, Any]:
        """Получение ответа на запрос"""
        try:
            response = await self.ollama_client.generate(self._create_response_prompt(request))
            return {
                "action": "send_message",
                "text": response
            }
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {str(e)}")
            return {
                "action": "send_message",
                "text": f"Произошла ошибка при генерации ответа: {str(e)}"
            }
            
    def is_private_chat(self, chat_id: int) -> bool:
        """Проверяет, является ли чат приватным"""
        return chat_id > 0
            
    def _create_analysis_prompt(self, request: str) -> str:
        """Создает промпт для анализа запроса"""
        return (
            "<start_of_turn>user\n"
            "Ты - ассистент в Telegram боте. Проанализируй следующий запрос и определи необходимые действия. "
            "Ответ должен быть кратким и по существу. "
            "Если это приветствие или вопрос о возможностях, ответь про свои функции. "
            "Если это запрос на поиск, предложи использовать поиск. "
            "Если это запрос на анализ изображения, попроси отправить изображение. "
            "Если это запрос на анализ документа, попроси отправить документ. "
            f"\nЗапрос пользователя: {request}\n"
            "<end_of_turn>\n"
            "<start_of_turn>assistant\n"
        )
        
    def _create_image_analysis_prompt(self, image_path: str) -> str:
        """Создает промпт для анализа изображения"""
        return (
            "<start_of_turn>user\n"
            "Ты - ассистент в Telegram боте. Проанализируй изображение и опиши его содержимое. "
            "Ответ должен быть кратким, понятным и на русском языке. "
            f"\nПуть к изображению: {image_path}\n"
            "<end_of_turn>\n"
            "<start_of_turn>assistant\n"
        )
        
    def _create_response_prompt(self, request: str) -> str:
        """Создает промпт для генерации ответа"""
        return (
            "<start_of_turn>user\n"
            "Ты - ассистент в Telegram боте. Сгенерируй краткий и понятный ответ на русском языке. "
            "Ответ должен быть полезным и по существу. "
            f"\nЗапрос пользователя: {request}\n"
            "<end_of_turn>\n"
            "<start_of_turn>assistant\n"
        ) 