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
        bot_config = config.get('bot', {})
        self.bot_name = bot_config.get('name', 'Бот')
        self.personality = bot_config.get('personality', {
            'greeting_phrases': ['Привет!', 'Здравствуйте!', 'Добрый день!'],
            'error_phrases': ['Произошла ошибка', 'Что-то пошло не так'],
            'capabilities': ['Обработка сообщений', 'Анализ изображений', 'Работа с документами'],
            'self_description': 'Я бот-ассистент',
            'about_creator': ['Меня создала команда разработчиков']
        })
        self.creator = bot_config.get('creator', {'name': 'Команда разработчиков'})
        self.logger = logging.getLogger(__name__)
        
    def _add_to_memory(self, chat_id: int, role: str, content: str):
        """Добавляет сообщение в память для указанного чата"""
        if not hasattr(self, 'memory') or self.memory is None:
            self.memory = {}
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
        """Обработка сообщения и генерация ответа"""
        try:
            # Создаем системный промпт
            system_prompt = self._create_analysis_prompt(message)
            
            # Генерируем ответ
            response = await self.ollama_client.generate(
                prompt=system_prompt
            )
            
            if not response:
                return {
                    "action": "send_message",
                    "text": f"Произошла ошибка: {self.bot_name} не смог сгенерировать ответ 😢"
                }
                
            # Если ответ уже является словарем, возвращаем его
            if isinstance(response, dict):
                return response
                
            # Пробуем распарсить JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Если не получилось распарсить JSON, возвращаем текст как есть
                return {
                    "action": "send_message",
                    "text": response
                }
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            return {
                "action": "send_message",
                "text": f"Произошла ошибка при обработке сообщения 🚫"
            }
            
    async def analyze_image(self, image_path: str, chat_id: int, message_id: int) -> dict:
        """Анализ изображения"""
        try:
            # Создаем системный промпт
            system_prompt = self._create_image_analysis_prompt(image_path)
            
            # Генерируем ответ
            response = await self.ollama_client.generate(
                prompt=system_prompt
            )
            
            if not response:
                return {
                    "action": "send_message",
                    "text": f"Произошла ошибка: {self.bot_name} не смог проанализировать изображение 😢"
                }
                
            # Если ответ уже является словарем, возвращаем его
            if isinstance(response, dict):
                return response
                
            # Пробуем распарсить JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Если не получилось распарсить JSON, возвращаем текст как есть
                return {
                    "action": "send_message",
                    "text": response
                }
            
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения: {e}")
            return {
                "action": "send_message",
                "text": f"Произошла ошибка при анализе изображения 🚫"
            }
            
    async def get_response(self, message: str, chat_id: int, user_id: int) -> dict:
        """Получение ответа от модели"""
        try:
            # Создаем системный промпт
            system_prompt = self._create_response_prompt(message)
            
            # Генерируем ответ
            response = await self.ollama_client.generate(
                prompt=system_prompt
            )
            
            if not response:
                return {
                    "action": "send_message",
                    "text": f"{self.bot_name} не смог сгенерировать ответ 😢"
                }
            
            # Если ответ уже является словарем, проверяем наличие текста
            if isinstance(response, dict):
                if "text" in response:
                    return response
                else:
                    return {
                        "action": "send_message",
                        "text": str(response)
                    }
            
            # Если получили строку, возвращаем её как текст
            return {
                "action": "send_message",
                "text": str(response)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {e}")
            return {
                "action": "send_message",
                "text": f"{self.bot_name} столкнулся с ошибкой при обработке сообщения 😔"
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
        if self.memory.get(0):  # Используем дефолтный chat_id для примера
            history = "\n".join([
                f"{'Пользователь' if msg['role'] == 'user' else 'Слайм'}: {msg['content']}"
                for msg in self.memory[0][-5:]  # Последние 5 сообщений
            ])
            system_prompt += f"{history}\n"
            
        system_prompt += (
            f"\nТЕКУЩЕЕ СООБЩЕНИЕ:\n{message}\n"
            "\nОТВЕЧАЙ СТРОГО НА РУССКОМ ЯЗЫКЕ!\n"
            "ВСЕГДА говори от третьего лица, используя имя 'Слайм'!\n"
            "Используй эмодзи в каждом предложении! 🌟"
        )
        
        return system_prompt

    async def get_file_content(self, file_id: str) -> Optional[str]:
        """Получение содержимого файла по его ID"""
        try:
            if not file_id:
                self.logger.error("Получен пустой file_id")
                return None
                
            # В реальном боте здесь будет код для получения файла через Telegram API
            # В тестах этот метод будет замокан
            self.logger.info(f"Получение содержимого файла с ID: {file_id}")
            return f"Content of file {file_id}"
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении содержимого файла: {e}")
            return None 

    def get_memory_context(self, chat_id: int = 0) -> str:
        """Возвращает контекст сообщений из памяти для заданного чата"""
        if chat_id not in self.memory:
            return ""
        return "\n".join(f"{msg['role']}: {msg['content']}" for msg in self.memory[chat_id]) 