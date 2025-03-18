import aiohttp
import asyncio
import json
import logging
from typing import AsyncGenerator, Optional, Dict
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

    async def _ensure_model_loaded(self, model_name: str) -> None:
        """Проверяет, загружена ли модель, и загружает её при необходимости"""
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
                        yield f"Ошибка API: {error_text}"
                        return
                        
                    # Читаем ответ построчно
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line)
                                if "response" in chunk:
                                    yield chunk["response"]
                                elif "error" in chunk:
                                    yield f"Ошибка: {chunk['error']}"
                            except json.JSONDecodeError as e:
                                logger.error(f"Ошибка при парсинге JSON: {str(e)}")
                                logger.error(f"Полученные данные: {line}")
                                yield f"Ошибка при обработке ответа: {str(e)}"
                                
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {str(e)}")
            logger.error(f"Тип ошибки: {type(e)}")
            logger.error(f"Аргументы ошибки: {e.args}")
            yield f"Произошла ошибка при генерации ответа: {str(e)}"
            
    async def generate(self, prompt: str, model_name: str = "gemma3:12b") -> str:
        """Генерирует полный ответ"""
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
                        return f"Ошибка API: {error_text}"
                        
                    # Читаем ответ
                    response_data = await response.json()
                    if "response" in response_data:
                        return response_data["response"]
                    elif "error" in response_data:
                        return f"Ошибка: {response_data['error']}"
                    else:
                        return "Неизвестный формат ответа"
                        
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа: {str(e)}")
            logger.error(f"Тип ошибки: {type(e)}")
            logger.error(f"Аргументы ошибки: {e.args}")
            return f"Произошла ошибка при генерации ответа: {str(e)}"

# Создаем глобальный экземпляр клиента
ollama_client = OllamaClient() 