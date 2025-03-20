import aiohttp
import asyncio
import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any
import subprocess
import time

logger = logging.getLogger(__name__)

class OllamaClient:
    """Клиент для работы с Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self._model_cache = {}
        self._model_lock = {}
        logger.info(f"Инициализация OllamaClient с базовым URL: {base_url}")

    async def check_server(self) -> bool:
        """Проверяет доступность Ollama сервера"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        logger.info("Ollama сервер доступен")
                        return True
                    else:
                        logger.error(f"Ollama сервер недоступен. Статус: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Ошибка при проверке Ollama сервера: {str(e)}")
            return False

    async def _ensure_model_loaded(self, model_name: str) -> None:
        """Проверяет, загружена ли модель, и загружает её при необходимости"""
        # Сначала проверяем доступность сервера
        if not await self.check_server():
            raise RuntimeError("Ollama сервер недоступен. Убедитесь, что он запущен.")
            
        current_time = time.time()
        logger.debug(f"Проверка загрузки модели {model_name}")

        # Проверяем, нужно ли загружать модель
        if model_name not in self._model_cache or current_time - self._model_cache[model_name] > 3600:  # 1 час
            logger.info(f"Модель {model_name} требует загрузки или обновления")
            if model_name not in self._model_lock:
                self._model_lock[model_name] = asyncio.Lock()

            async with self._model_lock[model_name]:
                try:
                    # Проверяем, не загрузил ли кто-то модель пока мы ждали
                    if model_name in self._model_cache and current_time - self._model_cache[model_name] <= 3600:
                        logger.debug(f"Модель {model_name} уже загружена другим процессом")
                        return

                    logger.info(f"Начало загрузки модели {model_name}...")
                    # Загружаем модель через ollama pull
                    process = await asyncio.create_subprocess_exec(
                        "ollama", "pull", model_name,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        error_msg = stderr.decode() if stderr else "Неизвестная ошибка"
                        logger.error(f"Ошибка при загрузке модели {model_name}. Код: {process.returncode}")
                        logger.error(error_msg)
                        raise RuntimeError(f"Ошибка при загрузке модели: {error_msg}")
                        
                    self._model_cache[model_name] = current_time
                    logger.info(f"Модель {model_name} успешно загружена")
                    
                except Exception as e:
                    logger.error(f"Ошибка при загрузке модели {model_name}: {str(e)}")
                    raise
                    
    async def generate_stream(self, prompt: str, model_name: str = "gemma3:12b") -> AsyncGenerator[str, None]:
        """Генерирует ответ в потоковом режиме"""
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt должен быть непустой строкой")

        try:
            # Убеждаемся, что модель загружена
            await self._ensure_model_loaded(model_name)
            
            # Формируем запрос
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": True
            }
            
            # Отправляем запрос
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ошибка API: {response.status}")
                        logger.error(f"Ответ: {error_text}")
                        raise RuntimeError(f"Ошибка API: {error_text}")
                        
                    # Читаем ответ построчно
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line)
                                if "response" in chunk:
                                    if not isinstance(chunk["response"], str):
                                        raise ValueError("Неверный формат ответа: response не является строкой")
                                    yield chunk["response"]
                                elif "error" in chunk:
                                    raise RuntimeError(f"Ошибка API: {chunk['error']}")
                                else:
                                    raise ValueError("Неверный формат ответа: отсутствуют поля response и error")
                            except json.JSONDecodeError as e:
                                logger.error(f"Ошибка при парсинге JSON: {str(e)}")
                                logger.error(f"Полученные данные: {line}")
                                raise RuntimeError(f"Ошибка при обработке ответа: {str(e)}")
                                
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {str(e)}")
            logger.error(f"Тип ошибки: {type(e)}")
            logger.error(f"Аргументы ошибки: {e.args}")
            raise
            
    async def generate_with_image(self, prompt: str, image: str, model_name: str = "gemma3:12b") -> str:
        """Генерирует полный ответ с использованием изображения"""
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt должен быть непустой строкой")
        if not image or not isinstance(image, str):
            raise ValueError("Image должен быть непустой строкой (base64)")
        try:
            await self._ensure_model_loaded(model_name)
            payload = {
                "model": model_name,
                "prompt": prompt,
                "image": image,
                "images": [image],
                "stream": False
            }
            logger.info(f"Отправляем запрос с изображением: длина изображения = {len(image)}; первые 30 символов: {image[:30]}")
            logger.debug(f"Payload: {{'model': {model_name}, 'prompt': {prompt}, 'images': [<image данных, длина={len(image)}>], 'stream': False}}")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ошибка API: {response.status}")
                        logger.error(f"Ответ: {error_text}")
                        raise RuntimeError(f"Ошибка API: {error_text}")
                    response_data = await response.json()
                    logger.debug(f"Response data: {response_data}")
                    if "response" in response_data:
                        if not isinstance(response_data["response"], str):
                            raise ValueError("Неверный формат ответа: response не является строкой")
                        return response_data["response"]
                    elif "error" in response_data:
                        raise RuntimeError(f"Ошибка API: {response_data['error']}")
                    else:
                        raise ValueError("Неверный формат ответа: отсутствуют поля response и error")
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа с изображением: {str(e)}")
            logger.error(f"Тип ошибки: {type(e)}")
            logger.error(f"Аргументы ошибки: {e.args}")
            raise

    async def generate(self, prompt: str, model_name: str = "gemma3:12b") -> str:
        """Генерирует полный ответ"""
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt должен быть непустой строкой")

        try:
            # Убеждаемся, что модель загружена
            await self._ensure_model_loaded(model_name)
            
            # Формируем запрос
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
            
            # Отправляем запрос
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ошибка API: {response.status}")
                        logger.error(f"Ответ: {error_text}")
                        raise RuntimeError(f"Ошибка API: {error_text}")
                        
                    # Читаем ответ
                    response_data = await response.json()
                    if "response" in response_data:
                        if not isinstance(response_data["response"], str):
                            raise ValueError("Неверный формат ответа: response не является строкой")
                        return response_data["response"]
                    elif "error" in response_data:
                        raise RuntimeError(f"Ошибка API: {response_data['error']}")
                    else:
                        raise ValueError("Неверный формат ответа: отсутствуют поля response и error")
                        
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {str(e)}")
            logger.error(f"Тип ошибки: {type(e)}")
            logger.error(f"Аргументы ошибки: {e.args}")
            raise

    async def list_models(self) -> Dict[str, Any]:
        """Получает список доступных моделей через Ollama API"""
        try:
            # Проверяем доступность сервера
            if not await self.check_server():
                raise RuntimeError("Ollama сервер недоступен. Убедитесь, что он запущен.")
                
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ошибка API при получении списка моделей: {response.status}")
                        logger.error(f"Ответ: {error_text}")
                        raise RuntimeError(f"Ошибка API: {error_text}")
                    
                    response_data = await response.json()
                    if "models" not in response_data:
                        raise ValueError("Неверный формат ответа: отсутствует поле models")
                    
                    return response_data["models"]
                    
        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей: {str(e)}")
            logger.error(f"Тип ошибки: {type(e)}")
            logger.error(f"Аргументы ошибки: {e.args}")
            raise

# Создаем глобальный экземпляр клиента
ollama_client = OllamaClient() 