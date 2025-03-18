import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from framework.agents.message_agent import MessageAgent

@pytest.fixture
def config():
    return {
        "bot": {
            "name": "TestBot",
            "username": "test_bot"
        },
        "models": {
            "default": "test_model"
        }
    }

@pytest.fixture
def agent(config):
    return MessageAgent(config)

@pytest.mark.asyncio
async def test_process_message_success(agent):
    """Тест успешной обработки сообщения"""
    test_response = {
        "action": "answer",
        "needs_image": False,
        "needs_additional_info": False,
        "additional_info": None
    }
    
    with patch.object(agent, 'think') as mock_think, \
         patch.object(agent, 'get_response') as mock_get_response:
        mock_think.return_value = json.dumps(test_response)
        mock_get_response.return_value = "Тестовый ответ"
        
        result = await agent.process_message("Тестовый запрос", 123456, 789)
        
        assert result["action"] == "send_message"
        assert result["text"] == "Тестовый ответ"

@pytest.mark.asyncio
async def test_process_message_image_request(agent):
    """Тест запроса изображения"""
    test_response = {
        "action": "analyze_image",
        "needs_image": True,
        "needs_additional_info": False,
        "additional_info": None
    }
    
    with patch.object(agent, 'think') as mock_think:
        mock_think.return_value = json.dumps(test_response)
        
        result = await agent.process_message("Проанализируй изображение", 123456, 789)
        
        assert result["action"] == "request_image"
        assert "отправьте изображение" in result["text"].lower()

@pytest.mark.asyncio
async def test_process_message_error(agent):
    """Тест обработки ошибки"""
    test_response = {
        "action": "error",
        "error": "Тестовая ошибка"
    }
    
    with patch.object(agent, 'think') as mock_think:
        mock_think.return_value = json.dumps(test_response)
        
        result = await agent.process_message("Тестовый запрос", 123456, 789)
        
        assert result["action"] == "send_message"
        assert "ошибка" in result["text"].lower()

def test_is_bot_mentioned(agent):
    """Тест проверки упоминания бота"""
    # Проверяем упоминание по имени
    assert agent.is_bot_mentioned("Привет, TestBot!") is True
    
    # Проверяем упоминание по username
    assert agent.is_bot_mentioned("Привет, @test_bot!") is True
    
    # Проверяем отсутствие упоминания
    assert agent.is_bot_mentioned("Привет!") is False

def test_is_private_chat(agent):
    """Тест проверки приватного чата"""
    # Проверяем приватный чат (положительный ID)
    assert agent.is_private_chat(123456) is True
    
    # Проверяем групповой чат (отрицательный ID)
    assert agent.is_private_chat(-123456) is False 