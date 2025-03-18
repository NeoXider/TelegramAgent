import pytest
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

@pytest.fixture(autouse=True)
def setup_test_env():
    """Настройка тестового окружения"""
    # Устанавливаем тестовые переменные окружения
    os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
    
    # Создаем временную директорию для тестовых данных
    test_data_dir = Path(project_root) / "data" / "test"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Очищаем временную директорию после тестов
    for file in test_data_dir.glob("*"):
        file.unlink()
    test_data_dir.rmdir()

@pytest.fixture
def test_image_path(setup_test_env):
    """Создает тестовое изображение"""
    from PIL import Image
    import numpy as np
    
    # Создаем случайное изображение
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(img_array)
    
    # Сохраняем изображение
    image_path = Path(project_root) / "data" / "test" / "test_image.jpg"
    img.save(image_path)
    
    return str(image_path)

@pytest.fixture
def test_document_path(setup_test_env):
    """Создает тестовый документ"""
    document_path = Path(project_root) / "data" / "test" / "test_document.txt"
    document_path.write_text("Тестовое содержимое документа")
    return str(document_path)

@pytest.fixture
def mock_ollama_response():
    """Создает мок ответа от Ollama"""
    return {
        "response": "Тестовый ответ",
        "done": True
    }

@pytest.fixture
def mock_ollama_error():
    """Создает мок ошибки от Ollama"""
    return {
        "error": "Тестовая ошибка",
        "done": True
    } 