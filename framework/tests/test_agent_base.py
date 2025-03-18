import pytest
import json
from unittest.mock import patch, MagicMock
from framework.agents.base import BaseAgent

@pytest.fixture
def config():
    return {
        "models": {
            "default": "test_model"
        }
    }

@pytest.fixture
def agent(config):
    return BaseAgent(config)

@pytest.mark.asyncio
async def test_think_success(agent):
    """Тест успешного размышления"""
    test_response = {
        "action": "send_message",
        "text": "Тестовый ответ"
    }

    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = json.dumps(test_response)

        result = await agent.think("Тестовый запрос")
        assert result == test_response
        mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_think_error(agent):
    """Тест ошибки при размышлении"""
    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.side_effect = Exception("Тестовая ошибка")

        result = await agent.think("Тестовый запрос")
        assert result["action"] == "send_message"
        assert "Произошла ошибка при анализе запроса" in result["text"]

@pytest.mark.asyncio
async def test_get_response_success(agent):
    """Тест успешного получения ответа"""
    test_response = {
        "action": "send_message",
        "text": "Тестовый ответ"
    }

    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = json.dumps(test_response)

        result = await agent.get_response("Тестовый запрос")
        assert result == test_response
        mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_get_response_error(agent):
    """Тест ошибки при получении ответа"""
    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.side_effect = Exception("Тестовая ошибка")

        result = await agent.get_response("Тестовый запрос")
        assert result["action"] == "send_message"
        assert "Произошла ошибка при генерации ответа" in result["text"]

@pytest.mark.asyncio
async def test_analyze_image_success(agent):
    """Тест успешного анализа изображения"""
    test_response = {
        "action": "send_message",
        "text": "Тестовое описание изображения"
    }

    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = json.dumps(test_response)

        result = await agent.analyze_image("test_image.jpg")
        assert result == test_response
        mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_image_error(agent):
    """Тест ошибки при анализе изображения"""
    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.side_effect = Exception("Тестовая ошибка")

        result = await agent.analyze_image("test_image.jpg")
        assert result["action"] == "send_message"
        assert "Произошла ошибка при анализе изображения" in result["text"]

@pytest.mark.asyncio
async def test_is_private_chat(agent):
    """Тест проверки приватного чата"""
    assert agent.is_private_chat(123456) == True
    assert agent.is_private_chat(-123456) == False

@pytest.mark.asyncio
async def test_get_response_empty(agent):
    """Тест обработки пустого ответа"""
    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = ""

        result = await agent.get_response("Тестовый запрос")
        assert result["action"] == "send_message"
        assert "Не удалось сгенерировать ответ" in result["text"]

@pytest.mark.asyncio
async def test_get_response_none(agent):
    """Тест обработки ответа None"""
    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = None

        result = await agent.get_response("Тестовый запрос")
        assert result["action"] == "send_message"
        assert "Не удалось сгенерировать ответ" in result["text"] 