import torch
from diffusers import StableDiffusionPipeline, DDIMScheduler
from PIL import Image
import io
import logging
import os
import time
from typing import Optional

# Отключаем предупреждения о символических ссылках
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# Отключаем использование символических ссылок
os.environ["HF_HUB_ENABLE_SYMLINKS"] = "0"

logger = logging.getLogger(__name__)

# Обновленная конфигурация для Stable Diffusion
DEFAULT_SCHEDULER_CONFIG = {
    "beta_start": 0.00085,
    "beta_end": 0.012,
    "beta_schedule": "scaled_linear",
    "clip_sample": False,
    "set_alpha_to_one": False,
    "steps_offset": 1,
    "prediction_type": "epsilon"
}

class StableDiffusionHandler:
    def __init__(self, model_id: str = "runwayml/stable-diffusion-v1-5"):
        """Initialize the Stable Diffusion handler.
        
        Args:
            model_id (str): Путь к локальной модели или ID модели с Hugging Face.
                          Например: "C:/models/stable-diffusion-v1-5" или "runwayml/stable-diffusion-v1-5"
        """
        self.model_id = model_id
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Настройки размера изображения (должны быть кратны 8)
        self.width = 512
        self.height = 512
        self.is_loaded = False
        self.logger = logging.getLogger(__name__)
        logger.info(f"Using device: {self.device}")
        logger.info(f"Model path: {model_id}")
        
    def is_model_loaded(self) -> bool:
        """Проверяет, загружена ли модель"""
        return self.is_loaded and self.pipe is not None
        
    async def load_model(self):
        """Load the Stable Diffusion model."""
        if not self.is_model_loaded():
            logger.info(f"Loading model: {self.model_id}")
            try:
                # Проверяем, является ли путь локальным
                if os.path.exists(self.model_id):
                    logger.info("Loading from local path")
                    # Преобразуем путь в формат, совместимый с diffusers
                    model_path = os.path.abspath(self.model_id).replace("\\", "/")
                    logger.info(f"Normalized model path: {model_path}")
                    
                    # Создаем планировщик с обновленной конфигурацией
                    scheduler = DDIMScheduler(**DEFAULT_SCHEDULER_CONFIG)
                    
                    # Загружаем модель с нашим планировщиком
                    self.pipe = StableDiffusionPipeline.from_single_file(
                        model_path,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        safety_checker=None,  # Отключаем проверку безопасности
                        scheduler=scheduler,
                        local_files_only=True
                    )
                else:
                    logger.info("Loading from Hugging Face")
                    # Создаем планировщик с обновленной конфигурацией
                    scheduler = DDIMScheduler(**DEFAULT_SCHEDULER_CONFIG)
                    
                    # Загружаем модель с нашим планировщиком
                    self.pipe = StableDiffusionPipeline.from_pretrained(
                        self.model_id,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        safety_checker=None,  # Отключаем проверку безопасности
                        scheduler=scheduler,
                        local_files_only=False
                    )
                
                self.pipe.to(self.device)
                self.is_loaded = True
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                raise
                
    def validate_dimensions(self, width: int, height: int) -> tuple[int, int]:
        """Validate and adjust image dimensions to be divisible by 8.
        
        Args:
            width (int): Desired width
            height (int): Desired height
            
        Returns:
            tuple[int, int]: Validated width and height
        """
        # Округляем до ближайшего числа, кратного 8
        width = (width // 8) * 8
        height = (height // 8) * 8
        
        # Убеждаемся, что размеры не меньше минимально допустимых
        width = max(width, 64)
        height = max(height, 64)
        
        return width, height
        
    async def generate_image(self, prompt: str, negative_prompt: str = None, width: int = None, height: int = None) -> Optional[str]:
        """Generate an image from a text prompt."""
        if not self.is_model_loaded():
            await self.load_model()
            
        try:
            logger.info(f"Generating image with prompt: {prompt}")
            
            # Устанавливаем размеры изображения
            if width is not None:
                self.width = width
            if height is not None:
                self.height = height
                
            # Проверяем и корректируем размеры
            self.width, self.height = self.validate_dimensions(self.width, self.height)
            
            # Генерируем изображение
            with torch.inference_mode():
                image = self.pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=30,
                    guidance_scale=7.5,
                    width=self.width,
                    height=self.height
                ).images[0]
            
            # Создаем директорию для выходных файлов, если её нет
            os.makedirs("output", exist_ok=True)
            
            # Сохраняем изображение
            output_path = os.path.join("output", f"generated_{int(time.time())}.png")
            image.save(output_path)
            logger.info(f"Image generated successfully")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return None 