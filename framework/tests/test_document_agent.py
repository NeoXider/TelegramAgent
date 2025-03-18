import pytest
import json
from unittest.mock import patch, MagicMock
from framework.agents.document_agent import DocumentAgent

@pytest.fixture
def config():
    return {
        "models": {
            "default": "test_model"
        }
    }

@pytest.fixture
def agent(config):
    return DocumentAgent(config)

@pytest.mark.asyncio
async def test_process_document_success(agent):
    """Тест успешной обработки документа"""
    test_response = {
        "action": "send_message",
        "text": "Тестовое содержимое документа"
    }

    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = json.dumps(test_response)

        result = await agent.process_document("test_doc.txt", 123456, 789012)
        assert result == test_response
        mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_process_document_error(agent):
    """Тест ошибки при обработке документа"""
    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.side_effect = Exception("Тестовая ошибка")

        result = await agent.process_document("test_doc.txt", 123456, 789012)
        assert result["action"] == "send_message"
        assert "Произошла ошибка при обработке документа" in result["text"]

@pytest.mark.asyncio
async def test_process_document_needs_info(agent):
    """Тест запроса дополнительной информации"""
    test_response = {
        "needs_additional_info": True,
        "additional_info": "Нужна дополнительная информация"
    }

    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = json.dumps(test_response)

        result = await agent.process_document("test_doc.txt", 123456, 789012)
        assert result["action"] == "request_info"
        assert result["text"] == "Нужна дополнительная информация"

@pytest.mark.asyncio
async def test_process_document_empty_response(agent):
    """Тест обработки пустого ответа"""
    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = ""

        result = await agent.process_document("test_doc.txt", 123456, 789012)
        assert result["action"] == "send_message"
        assert "Произошла ошибка при обработке документа" in result["text"]

@pytest.mark.asyncio
async def test_process_document_none_response(agent):
    """Тест обработки ответа None"""
    with patch.object(agent.ollama_client, 'generate') as mock_generate:
        mock_generate.return_value = None

        result = await agent.process_document("test_doc.txt", 123456, 789012)
        assert result["action"] == "send_message"
        assert "Произошла ошибка при обработке документа" in result["text"]

@pytest.mark.asyncio
async def test_is_private_chat(agent):
    """Тест проверки приватного чата"""
    assert agent.is_private_chat(123456) == True
    assert agent.is_private_chat(-123456) == False 