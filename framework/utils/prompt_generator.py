import logging
from typing import Optional
import re

logger = logging.getLogger(__name__)

class PromptGenerator:
    """Класс для обработки текста и генерации промптов для изображений"""
    
    @staticmethod
    def is_russian(text: str) -> bool:
        """Проверяет, содержит ли текст русские буквы"""
        return any(ord(c) in range(1040, 1104) for c in text)
    
    @staticmethod
    def clean_russian(text: str) -> str:
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
    
    @staticmethod
    def extract_prompt(text: str) -> Optional[str]:
        """Извлекает промпт из текста, убирая ключевые слова"""
        keywords = ['нарисуй', 'сгенерируй', 'создай', 'generate', 'draw', 'create']
        text = text.lower()
        
        for keyword in keywords:
            if keyword in text:
                return text[text.find(keyword) + len(keyword):].strip()
        return None
    
    @staticmethod
    def generate_translation_prompt(text: str) -> str:
        """Генерирует промпт для перевода текста на английский"""
        return (
            "Translate this image description to English. "
            "Keep it concise and descriptive. "
            "Focus on visual elements. "
            "Text to translate: " + text
        )
    
    @staticmethod
    def enhance_prompt(text: str) -> str:
        """Улучшает промпт для генерации изображения"""
        return (
            "Create a detailed image description in English. "
            "Focus on visual elements, style, and mood. "
            "Keep it concise and descriptive. "
            "Do not include any Russian characters or emojis. "
            "Description: " + text
        )
    
    @staticmethod
    def process_prompt(text: str) -> str:
        """Обрабатывает текст и возвращает промпт для генерации изображения"""
        # Извлекаем промпт из текста
        prompt = PromptGenerator.extract_prompt(text)
        if not prompt:
            prompt = text
            
        # Если промпт на русском, генерируем запрос на перевод
        if PromptGenerator.is_russian(prompt):
            return PromptGenerator.generate_translation_prompt(prompt)
            
        # Очищаем промпт от русских букв и эмодзи
        prompt = PromptGenerator.clean_russian(prompt)
        
        # Если промпт на английском, улучшаем его
        return PromptGenerator.enhance_prompt(prompt) 