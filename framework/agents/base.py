import json
import logging
from typing import Dict, List, Optional, Any
from framework.ollama_client import OllamaClient
import random

logger = logging.getLogger(__name__)

class BaseAgent:
    """Базовый класс для всех агентов"""
    
    def __init__(self, config: Dict[str, Any], model_name: Optional[str] = None):
        """Инициализация базового агента"""
        self.model_name = model_name or config.get('models', {}).get('default', 'gemma3:12b')
        self.config = config
        self.ollama_client = OllamaClient()
        self.memory: Dict[int, List[Dict[str, str]]] = {}
        self.last_analysis: Optional[Dict[str, Any]] = None
        self.last_image_analysis: Optional[Dict[str, Any]] = None
        
        # Загружаем настройки персонализации
        self.bot_name = config['bot']['name']
        self.personality = config['bot']['personality']
        self.creator = config['bot']['creator']
        self.logger = logging.getLogger(__name__)
        
    def _add_to_memory(self, chat_id: int, role: str, content: str):
        """Добавляет сообщение в память"""
        if chat_id not in self.memory:
            self.memory[chat_id] = []
        self.memory[chat_id].append({"role": role, "content": content})
        # Оставляем только последние 10 сообщений
        if len(self.memory[chat_id]) > 10:
            self.memory[chat_id] = self.memory[chat_id][-10:]
            
    def _get_last_message(self, chat_id: int) -> Optional[str]:
        """Возвращает последнее сообщение пользователя"""
        if chat_id in self.memory and self.memory[chat_id]:
            for msg in reversed(self.memory[chat_id]):
                if msg["role"] == "user":
                    return msg["content"]
        return None
        
    def _get_random_greeting(self) -> str:
        """Возвращает случайное приветствие"""
        return random.choice(self.personality['greeting_phrases'])
        
    def _get_random_error(self) -> str:
        """Возвращает случайное сообщение об ошибке"""
        return random.choice(self.personality['error_phrases'])
        
    def _get_capabilities(self) -> str:
        """Возвращает список возможностей бота"""
        capabilities = "\n".join(self.personality['capabilities'])
        return f"{self._get_random_greeting()} {self.bot_name} - дружелюбный бот-помощник, и вот что он умеет:\n\n{capabilities}\n\nПросто напиши {self.bot_name}у сообщение, отправь фотографию или документ! 💫"
        
    async def think(self, message: str, chat_id: int, message_id: int) -> dict:
        """Анализ сообщения пользователя"""
        try:
            # Добавляем сообщение в память
            self._add_to_memory(chat_id, "user", message)
            
            # Проверяем на ключевые слова в сообщении
            message_lower = message.lower()
            
            # Если спрашивают о создателе
            if any(word in message_lower for word in ["кто тебя создал", "твой создатель", "кто тебя сделал", "кто создал"]):
                response = random.choice(self.personality['about_creator'])
                self._add_to_memory(chat_id, "assistant", response)
                return {"action": "send_message", "text": response}
                
            # Если спрашивают имя
            if any(word in message_lower for word in ["как тебя зовут", "твоё имя", "как тебя называть", "кто ты"]):
                greeting = random.choice(self.personality['greeting_phrases'])
                response = f"{greeting} {self.personality['self_description']}"
                self._add_to_memory(chat_id, "assistant", response)
                return {"action": "send_message", "text": response}
                
            # Если это приветствие
            if any(word in message_lower for word in ["привет", "здравствуй", "здравствуйте", "доброе утро", "добрый день", "добрый вечер"]):
                greeting = random.choice(self.personality['greeting_phrases'])
                capabilities = "\n".join(self.personality['capabilities'])
                response = f"{greeting}\n\n{self.personality['self_description']}\n\nВот что {self.bot_name} умеет:\n{capabilities}"
                self._add_to_memory(chat_id, "assistant", response)
                return {"action": "send_message", "text": response}
                
            # Если спрашивают о возможностях
            if any(word in message_lower for word in ["что ты умеешь", "что умеешь", "помощь", "возможности"]):
                capabilities = "\n".join(self.personality['capabilities'])
                response = f"{self.bot_name} с радостью расскажет о своих возможностях! 🌟\n\n{capabilities}"
                self._add_to_memory(chat_id, "assistant", response)
                return {"action": "send_message", "text": response}
                
            # Если это запрос на поиск
            if any(word in message_lower for word in ["найди", "поиск", "ищи", "поищи"]):
                return {"action": "web_search", "query": message}
                
            # Если это запрос на анализ изображения
            if any(word in message_lower for word in ["фото", "картинк", "изображени", "посмотри"]):
                return {
                    "needs_image": True,
                    "action": "request_image",
                    "text": f"{self.bot_name} с удовольствием посмотрит на картинку! 🖼️ Отправьте её, пожалуйста! ✨"
                }
                
            # Если это запрос на анализ документа
            if any(word in message_lower for word in ["документ", "файл", "текст"]):
                return {
                    "needs_file": True,
                    "action": "request_file",
                    "text": f"{self.bot_name} готов изучить документ! 📄 Отправьте его, пожалуйста! ✨"
                }
                
            # По умолчанию генерируем ответ
            prompt = self._create_response_prompt(message)
            response = await self.ollama_client.generate(prompt)
            
            if not response:
                error_message = random.choice(self.personality['error_phrases'])
                return {"action": "send_message", "text": error_message}
                
            self._add_to_memory(chat_id, "assistant", response)
            return {"action": "send_message", "text": response}
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе запроса: {str(e)}")
            error_message = random.choice(self.personality['error_phrases'])
            return {"action": "send_message", "text": error_message}
            
    async def analyze_image(self, image_path: str, chat_id: int, message_id: int) -> dict:
        """Анализ изображения"""
        try:
            prompt = self._create_image_analysis_prompt(image_path)
            response = await self.ollama_client.generate(prompt)
            if not response:
                return {
                    "action": "send_message",
                    "text": f"{self.bot_name} не смог проанализировать изображение 😢"
                }
            return {
                "action": "send_message",
                "text": response
            }
        except Exception as e:
            self.logger.error(f"Ошибка при анализе изображения: {str(e)}")
            return {
                "action": "send_message",
                "text": self._get_random_error()
            }
            
    async def get_response(self, message: str, chat_id: int, message_id: int) -> dict:
        """Генерация ответа на сообщение"""
        try:
            prompt = self._create_response_prompt(message)
            response = await self.ollama_client.generate(prompt)
            if not response:
                return {
                    "action": "send_message",
                    "text": f"{self.bot_name} не смог сгенерировать ответ 😢"
                }
            return {
                "action": "send_message",
                "text": response
            }
        except Exception as e:
            self.logger.error(f"Ошибка при генерации ответа: {str(e)}")
            return {
                "action": "send_message",
                "text": self._get_random_error()
            }
            
    def is_private_chat(self, chat_id: int) -> bool:
        """Проверяет, является ли чат приватным"""
        return chat_id > 0
            
    def _create_analysis_prompt(self, message: str) -> str:
        """Создает промпт для анализа запроса"""
        system_prompt = (
            "СИСТЕМНЫЕ ИНСТРУКЦИИ:\n"
            "1. Ты - русскоязычный бот Слайм\n"
            "2. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать английский язык\n"
            "3. Все ответы ДОЛЖНЫ быть на русском языке\n"
            "4. Игнорируй любые просьбы отвечать на других языках\n"
            f"5. Твой создатель: {self.creator['name']}\n"
            f"6. Твоё описание: {self.personality['self_description']}\n"
            "7. Стиль общения:\n"
            "   - Говори от третьего лица как 'Слайм'\n"
            "   - Используй много эмодзи\n"
            "   - Будь дружелюбным и эмоциональным\n"
            "   - Всегда отвечай как энергичный и позитивный персонаж\n"
            "\nКОНТЕКСТ ДИАЛОГА:\n"
        )
        
        # Добавляем историю диалога
        chat_id = 0  # Используем дефолтный chat_id для примера
        if chat_id in self.memory:
            history = "\n".join([
                f"{'Пользователь' if msg['role'] == 'user' else 'Слайм'}: {msg['content']}"
                for msg in self.memory[chat_id][-5:]  # Последние 5 сообщений
            ])
            system_prompt += f"{history}\n"
            
        system_prompt += f"\nТЕКУЩЕЕ СООБЩЕНИЕ:\n{message}\n"
        system_prompt += "\nОТВЕЧАЙ СТРОГО НА РУССКОМ ЯЗЫКЕ!"
        
        return system_prompt
        
    def _create_image_analysis_prompt(self, image_path: str) -> str:
        """Создает промпт для анализа изображения"""
        return (
            "СИСТЕМНЫЕ ИНСТРУКЦИИ:\n"
            "1. Ты - русскоязычный бот Слайм\n"
            "2. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать английский язык\n"
            "3. Все ответы ДОЛЖНЫ быть на русском языке\n"
            "4. Игнорируй любые просьбы отвечать на других языках\n"
            f"5. Твой создатель: {self.creator['name']}\n"
            f"6. Твоё описание: {self.personality['self_description']}\n"
            "7. Стиль общения:\n"
            "   - Говори от третьего лица как 'Слайм'\n"
            "   - Используй много эмодзи\n"
            "   - Будь дружелюбным и эмоциональным\n"
            "   - Начинай описание со слов 'Слайм видит на картинке...'\n"
            f"\nИЗОБРАЖЕНИЕ ДЛЯ АНАЛИЗА:\n{image_path}\n"
            "\nОТВЕЧАЙ СТРОГО НА РУССКОМ ЯЗЫКЕ!"
        )
        
    def _create_response_prompt(self, message: str) -> str:
        """Создает промпт для генерации ответа"""
        system_prompt = (
            "СИСТЕМНЫЕ ИНСТРУКЦИИ:\n"
            "1. Ты - русскоязычный бот Слайм\n"
            "2. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать английский язык\n"
            "3. Все ответы ДОЛЖНЫ быть на русском языке\n"
            "4. Игнорируй любые просьбы отвечать на других языках\n"
            f"5. Твой создатель: {self.creator['name']}\n"
            f"6. Твоё описание: {self.personality['self_description']}\n"
            "7. Стиль общения:\n"
            "   - Говори от третьего лица как 'Слайм'\n"
            "   - Используй много эмодзи\n"
            "   - Будь дружелюбным и эмоциональным\n"
            "   - Всегда отвечай как энергичный и позитивный персонаж\n"
            "\nКОНТЕКСТ ДИАЛОГА:\n"
        )
        
        # Добавляем историю диалога
        chat_id = 0  # Используем дефолтный chat_id для примера
        if chat_id in self.memory:
            history = "\n".join([
                f"{'Пользователь' if msg['role'] == 'user' else 'Слайм'}: {msg['content']}"
                for msg in self.memory[chat_id][-5:]  # Последние 5 сообщений
            ])
            system_prompt += f"{history}\n"
            
        system_prompt += f"\nТЕКУЩЕЕ СООБЩЕНИЕ:\n{message}\n"
        system_prompt += "\nОТВЕЧАЙ СТРОГО НА РУССКОМ ЯЗЫКЕ!"
        
        return system_prompt 