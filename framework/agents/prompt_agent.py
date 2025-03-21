import logging
from typing import Optional
import re
from framework.agents.base import BaseAgent
from framework.utils.logger import setup_logger

logger = logging.getLogger(__name__)

class PromptAgent(BaseAgent):
    """Агент для обработки промптов и их перевода"""
    
    def __init__(self, config: dict, ollama_client):
        super().__init__(config, ollama_client)
        self.logger = setup_logger()
        
    def is_russian(self, text: str) -> bool:
        """Проверяет, содержит ли текст русские буквы"""
        return any(ord(c) in range(1040, 1104) for c in text)
    
    def clean_text(self, text: str) -> str:
        """Очищает текст от русских букв и эмодзи"""
        # Удаляем эмодзи
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # эмодзи
            u"\U0001F300-\U0001F5FF"  # символы и пиктограммы
            u"\U0001F680-\U0001F6FF"  # транспорт и символы
            u"\U0001F1E0-\U0001F1FF"  # флаги
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        
        # Удаляем русские буквы
        text = ''.join(c for c in text if ord(c) not in range(1040, 1104))
        
        # Удаляем лишние пробелы
        text = ' '.join(text.split())
        
        return text.strip()
    
    def extract_prompt(self, text: str) -> Optional[str]:
        """Извлекает промпт из текста, убирая ключевые слова"""
        keywords = ['нарисуй', 'сгенерируй', 'создай', 'generate', 'draw', 'create']
        text = text.lower()
        
        for keyword in keywords:
            if keyword in text:
                return text[text.find(keyword) + len(keyword):].strip()
        return None
    
    async def translate_prompt(self, text: str) -> Optional[str]:
        """Переводит промпт на английский язык"""
        try:
            prompt = (
                "Translate this image description to English. "
                "Keep it concise and descriptive. "
                "Focus on visual elements. "
                "Text to translate: " + text
            )
            translated = await self.ollama_client.generate(prompt)
            return translated.strip()
        except Exception as e:
            self.logger.error(f"Error translating prompt: {str(e)}")
            return None
    
    async def process_prompt(self, text: str) -> Optional[str]:
        """Обрабатывает промпт и возвращает готовый текст для генерации изображения"""
        try:
            # Извлекаем промпт из текста
            prompt = self.extract_prompt(text)
            if not prompt:
                prompt = text
                
            # Если промпт на русском, переводим его
            if self.is_russian(prompt):
                translated = await self.translate_prompt(prompt)
                if translated:
                    return self.clean_text(translated)
                return None
                
            # Очищаем английский промпт
            return self.clean_text(prompt)
            
        except Exception as e:
            self.logger.error(f"Error processing prompt: {str(e)}")
            return None 