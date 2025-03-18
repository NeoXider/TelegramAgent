import pytest
from unittest.mock import patch, MagicMock
from framework.agents.image_agent import ImageAgent
import json

@pytest.fixture
def config():
    return {
        "models": {
            "default": "test_model"
        }
    }

@pytest.fixture
def agent(config):
    return ImageAgent(config)

@pytest.mark.asyncio
async def test_process_image_success(agent):
    """Тест успешной обработки изображения"""
    test_response = {
        "action": "send_message",
        "text": "Тестовое описание изображения"
    }

    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = json.dumps(test_response)

        result = await agent.process_image("test_image.jpg", 123456, 789012)
        assert result == test_response
        mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_process_image_error(agent):
    """Тест ошибки при обработке изображения"""
    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.side_effect = Exception("Тестовая ошибка")

        result = await agent.process_image("test_image.jpg", 123456, 789012)
        assert result["action"] == "send_message"
        assert "Произошла ошибка при обработке изображения" in result["text"]

@pytest.mark.asyncio
async def test_process_image_needs_info(agent):
    """Тест запроса дополнительной информации"""
    test_response = {
        "needs_additional_info": True,
        "additional_info": "Нужна дополнительная информация"
    }

    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = json.dumps(test_response)

        result = await agent.process_image("test_image.jpg", 123456, 789012)
        assert result["action"] == "request_info"
        assert result["text"] == "Нужна дополнительная информация"

@pytest.mark.asyncio
async def test_process_image_empty_response(agent):
    """Тест обработки пустого ответа"""
    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = ""

        result = await agent.process_image("test_image.jpg", 123456, 789012)
        assert result["action"] == "send_message"
        assert "Произошла ошибка при обработке изображения" in result["text"]

@pytest.mark.asyncio
async def test_process_image_none_response(agent):
    """Тест обработки ответа None"""
    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = None

        result = await agent.process_image("test_image.jpg", 123456, 789012)
        assert result["action"] == "send_message"
        assert "Произошла ошибка при обработке изображения" in result["text"]

@pytest.mark.asyncio
async def test_is_private_chat(agent):
    """Тест проверки приватного чата"""
    assert agent.is_private_chat(123456) == True
    assert agent.is_private_chat(-123456) == False 