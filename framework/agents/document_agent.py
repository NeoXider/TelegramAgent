import os
import json
import logging
from typing import Dict, Any
from framework.agents.base import BaseAgent

class DocumentAgent(BaseAgent):
    """Агент для обработки документов"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    def _is_document_valid(self, file_id: str) -> bool:
        """Проверка валидности документа"""
        # TODO: Реализовать проверку
        return True
        
    async def process_document(self, file_id: str, chat_id: int, message_id: int) -> dict:
        """Обработка документа"""
        try:
            # Получаем содержимое документа
            content = await self.get_file_content(file_id)
            if not content:
                return {
                    "action": "send_message",
                    "text": "Произошла ошибка: не удалось получить содержимое документа"
                }

            # Анализируем документ с помощью модели
            response = await self.think(
                f"Analyze document content: {content}",
                chat_id,
                message_id
            )
            if not response or not isinstance(response, dict):
                return {
                    "action": "send_message",
                    "text": "Произошла ошибка при анализе документа"
                }
            return response

        except Exception as e:
            self.logger.error(f"Ошибка при обработке документа: {e}")
            return {
                "action": "send_message",
                "text": "Произошла ошибка при обработке документа"
            }
            
    async def analyze_document(self, file_id: str, chat_id: int, message_id: int) -> dict:
        """Анализ документа"""
        try:
            prompt = self._create_document_analysis_prompt(file_id)
            response = await self.ollama_client.generate(prompt)
            if not response:
                return {
                    "action": "send_message",
                    "text": "Не удалось проанализировать документ"
                }
            return {
                "action": "send_message",
                "text": response
            }
        except Exception as e:
            self.logger.error(f"Ошибка при анализе документа: {str(e)}")
            return {
                "action": "send_message",
                "text": "Произошла ошибка при анализе документа"
            }
            
    def _create_document_analysis_prompt(self, file_id: str) -> str:
        """Создает промпт для анализа документа"""
        return (
            "<start_of_turn>user\n"
            "Ты - ассистент в Telegram боте. Проанализируй документ и опиши его содержимое. "
            "Ответ должен быть кратким и по существу. "
            f"\nДокумент: {file_id}\n"
            "<end_of_turn>\n"
            "<start_of_turn>assistant\n"
        ) 