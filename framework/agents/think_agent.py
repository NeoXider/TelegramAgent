import logging
from typing import Dict, Any, Optional
from framework.agents.base import BaseAgent

logger = logging.getLogger(__name__)

class ThinkAgent(BaseAgent):
    """Агент для анализа сообщений и генерации осмысленных ответов"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_name = config.get('models', {}).get('think', config.get('models', {}).get('default', 'gemma3:12b'))
        self.logger = logging.getLogger(__name__)
        
    async def think(self, message: str) -> Optional[str]:
        """Анализ сообщения и генерация ответа"""
        try:
            self.logger.info("Начало анализа сообщения")
            
            # Добавляем сообщение в память
            self._add_to_memory(0, "user", message)
            
            # Формируем промпт с учетом контекста
            system_prompt = (
                "Ты - дружелюбный бот по имени Слайм, который говорит ТОЛЬКО на русском языке. "
                "Твоя задача - анализировать сообщения и давать осмысленные, полезные ответы. "
                "Не упоминай, что ты бот или ИИ. Просто отвечай от первого лица. "
                "Используй эмодзи для более живого общения. "
                "ВАЖНО: Отвечай ТОЛЬКО на русском языке!\n\n"
                "Пример ответа:\n"
                "Интересный вопрос! 🤔 Давай разберемся...\n\n"
                "ПОМНИ: Отвечай ТОЛЬКО на русском языке!"
            )
            
            # Получаем ответ от модели
            response = await self.ollama_client.generate(
                f"{system_prompt}\n\nКонтекст предыдущих сообщений:\n{self.get_memory_context()}\n\nТекущее сообщение:\n{message}",
                self.model_name
            )
            
            if not response:
                self.logger.error("Получен пустой ответ от модели")
                return None
                
            # Очищаем ответ от HTML-тегов и специальных символов
            cleaned_response = response.replace("<br>", "\n").replace("</br>", "\n")
            cleaned_response = cleaned_response.replace("<br/>", "\n").replace("<br />", "\n")
            
            # Проверяем, что ответ на русском языке
            if any(ord(char) < 128 for char in ''.join(cleaned_response.split())):
                self.logger.warning("Обнаружен ответ с английскими символами")
                # Пробуем еще раз с более строгим промптом
                response = await self.ollama_client.generate(
                    f"{system_prompt}\n\nОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ!\n\nСообщение:\n{message}",
                    self.model_name
                )
                if not response:
                    return None
                cleaned_response = response.replace("<br>", "\n").replace("</br>", "\n")
                cleaned_response = cleaned_response.replace("<br/>", "\n").replace("<br />", "\n")
            
            # Добавляем ответ в память
            self._add_to_memory(0, "assistant", cleaned_response)
            
            # Логируем часть ответа
            preview = cleaned_response[:200] + "..." if len(cleaned_response) > 200 else cleaned_response
            self.logger.info(f"Сгенерирован ответ:\n{preview}")
            
            return cleaned_response
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе сообщения: {str(e)}", exc_info=True)
            return None 