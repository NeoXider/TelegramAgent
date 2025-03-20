import torch
from diffusers import StableDiffusionPipeline, DDIMScheduler
from PIL import Image
import io
import logging
import os

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
        logger.info(f"Using device: {self.device}")
        logger.info(f"Model path: {model_id}")
        
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
        
    def load_model(self):
        """Load the Stable Diffusion model."""
        if self.pipe is None:
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
                        safety_checker=None,  # We'll load the safety checker separately
                        scheduler=scheduler,
                        local_files_only=True
                    )
                else:
                    logger.info("Loading from Hugging Face")
                    self.pipe = StableDiffusionPipeline.from_pretrained(
                        self.model_id,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        safety_checker=None,  # We'll load the safety checker separately
                        local_files_only=True
                    )
                
                # Load the safety checker separately
                from diffusers.pipelines.stable_diffusion.safety_checker import StableDiffusionSafetyChecker
                safety_checker = StableDiffusionSafetyChecker.from_pretrained(
                    "CompVis/stable-diffusion-safety-checker",
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
                safety_checker.to(self.device)
                self.pipe.safety_checker = safety_checker
                
                self.pipe.to(self.device)
                logger.info("Model and safety checker loaded successfully")
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                raise
    
    def generate_image(self, prompt: str, negative_prompt: str = None, width: int = None, height: int = None) -> bytes:
        """Generate an image from a text prompt.
        
        Args:
            prompt (str): The text prompt to generate the image from
            negative_prompt (str, optional): The negative prompt to avoid certain elements
            width (int, optional): Custom width for the image (must be divisible by 8)
            height (int, optional): Custom height for the image (must be divisible by 8)
            
        Returns:
            bytes: The generated image as bytes
        """
        try:
            if self.pipe is None:
                self.load_model()
            
            # Валидируем размеры изображения
            if width is not None or height is not None:
                width = width if width is not None else self.width
                height = height if height is not None else self.height
                width, height = self.validate_dimensions(width, height)
            else:
                width, height = self.width, self.height
            
            logger.info(f"Generating image for prompt: {prompt} with dimensions {width}x{height}")
            
            # Генерация изображения с настройками
            image = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=30,  # Количество шагов генерации (больше = качественнее, но медленнее)
                guidance_scale=7.5,      # Сила следования промпту (больше = точнее промпту, но менее креативно)
                width=width,             # Ширина изображения
                height=height,           # Высота изображения
                num_images_per_prompt=1  # Количество изображений за одну генерацию
            ).images[0]
            
            # Конвертируем PIL Image в bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            logger.info("Image generated successfully")
            return img_byte_arr
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            raise 