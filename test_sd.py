import asyncio
import os
from framework.models.image_generation.stable_diffusion import StableDiffusionHandler

async def test_image_generation():
    # Инициализируем генератор
    generator = StableDiffusionHandler(
        model_id="runwayml/stable-diffusion-v1-5"
    )
    
    # Тестовые промпты разной длины
    test_prompts = [
        ("a beautiful mountain landscape", "Тест 1: Генерация изображения с промптом длиной 30 символов"),
        ("a beautiful mountain landscape with snow peaks and clear blue sky", "Тест 2: Генерация изображения с промптом длиной 65 символов"),
        ("a detailed beautiful mountain landscape with snow-covered peaks, clear blue sky, green forests in the valley, a crystal-clear lake reflecting the mountains, and small wooden cabins scattered around", "Тест 3: Генерация изображения с промптом длиной 197 символов")
    ]
    
    # Создаем директорию для тестовых изображений, если её нет
    os.makedirs("test_images", exist_ok=True)
    
    # Запускаем тесты
    for i, (prompt, test_name) in enumerate(test_prompts, 1):
        print(f"\n{test_name}")
        print(f"Промпт: {prompt}")
        
        try:
            # Генерируем изображение
            output_path = await generator.generate_image(prompt)
            
            if output_path:
                print(f"✓ Изображение успешно сгенерировано и сохранено как {output_path}")
            else:
                print("✗ Ошибка при генерации изображения")
                
        except Exception as e:
            print(f"✗ Ошибка: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_image_generation()) 