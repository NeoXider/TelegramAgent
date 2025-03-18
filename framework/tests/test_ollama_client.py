import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from framework.ollama_client import OllamaClient

@pytest.fixture
def config():
    return {
        "models": {
            "default": "test_model"
        }
    }

@pytest.fixture
def client(config):
    return OllamaClient(config)

@pytest.mark.asyncio
async def test_ensure_model_loaded(client):
    """Тест загрузки модели"""
    with patch('asyncio.create_subprocess_exec') as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"success", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        await client._ensure_model_loaded("test_model")
        mock_exec.assert_called_once_with(
            "ollama", "pull", "test_model",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

@pytest.mark.asyncio
async def test_generate_stream_success(client):
    """Тест успешной генерации потока"""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.content.__aiter__.return_value = [b'{"response": "test chunk"}'].__iter__()

    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        async for chunk in client.generate_stream("test_prompt"):
            assert chunk == "test chunk"

@pytest.mark.asyncio
async def test_generate_stream_error(client):
    """Тест ошибки при генерации потока"""
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text.return_value = "Тестовая ошибка"

    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        async for chunk in client.generate_stream("test_prompt"):
            assert "Ошибка API" in chunk
            assert "Тестовая ошибка" in chunk

@pytest.mark.asyncio
async def test_generate_success(client):
    """Тест успешной генерации полного ответа"""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"response": "test response"}

    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await client.generate("test_prompt")
        assert result == "test response"

@pytest.mark.asyncio
async def test_generate_error(client):
    """Тест ошибки при генерации полного ответа"""
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text.return_value = "Тестовая ошибка"

    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await client.generate("test_prompt")
        assert "Ошибка API" in result
        assert "Тестовая ошибка" in result

@pytest.mark.asyncio
async def test_generate_stream_invalid_json(client):
    """Тест обработки некорректного JSON"""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.content.__aiter__.return_value = [b"invalid json"].__iter__()

    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        async for chunk in client.generate_stream("test_prompt"):
            assert "Ошибка при обработке ответа" in chunk

@pytest.mark.asyncio
async def test_generate_stream_timeout(client):
    """Тест обработки таймаута"""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.side_effect = asyncio.TimeoutError()

        async for chunk in client.generate_stream("test_prompt"):
            assert "Произошла ошибка при генерации ответа" in chunk

@pytest.mark.asyncio
async def test_generate_connection_error(client):
    """Тест ошибки подключения"""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.side_effect = ConnectionError("Ошибка подключения")

        result = await client.generate("test_prompt")
        assert "Произошла ошибка при генерации ответа" in result
        assert "Ошибка подключения" in result

@pytest.mark.asyncio
async def test_generate_full_response(client):
    """Тест генерации полного ответа"""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"response": "test response"}

    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await client.generate("test_prompt")
        assert result == "test response"
        mock_post.assert_called_once() 