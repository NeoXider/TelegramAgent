import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
import os
from PIL import Image
import io
from framework.agents.web_search_agent import WebSearchAgent
from framework.agents.web_browser_agent import WebBrowserAgent

@pytest.fixture
def config():
    return {
        "models": {
            "default": "test_model"
        },
        "search_engine": "https://test-search.com",
        "name": "test_agent"
    }

@pytest.fixture
def web_search_agent(config):
    return WebSearchAgent(config)

@pytest.fixture
def web_browser_agent(config):
    return WebBrowserAgent(config)

@pytest.fixture
def test_image():
    # Создаем тестовое изображение
    img = Image.new('RGB', (100, 100), color='red')
    img_path = os.path.join('assets', 'test_image.jpg')
    img.save(img_path)
    yield img_path
    # Очищаем после теста
    if os.path.exists(img_path):
        os.remove(img_path)

@pytest.mark.asyncio
async def test_web_search_agent_initialization(web_search_agent):
    assert web_search_agent.search_engine == 'https://test-search.com'
    assert web_search_agent.headers['User-Agent'] is not None

@pytest.mark.asyncio
async def test_web_browser_agent_initialization(web_browser_agent):
    assert web_browser_agent.headers['User-Agent'] is not None
    expected_path = os.path.join('data', 'temp', 'screenshots')
    assert os.path.normpath(web_browser_agent.screenshot_dir) == os.path.normpath(expected_path)

@pytest.mark.asyncio
async def test_web_search_agent_process_message(web_search_agent):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='''
            <html>
                <div class="g">
                    <h3>Test Result</h3>
                    <a href="https://test.com">Test Link</a>
                    <div class="VwiC3b">Test Snippet</div>
                </div>
            </html>
        ''')
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await web_search_agent.process_message({'text': 'test query'})
        
        assert result['status'] == 'success'
        assert 'Test Result' in result['message']
        assert 'https://test.com' in result['message']
        assert 'Test Snippet' in result['message']

@pytest.mark.asyncio
async def test_web_browser_agent_process_message(web_browser_agent):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='''
            <html>
                <title>Test Page</title>
                <p>Test content</p>
                <img src="test.jpg" alt="Test Image">
            </html>
        ''')
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await web_browser_agent.process_message({'text': 'https://test.com'})
        
        assert result['status'] == 'success'
        assert 'Test Page' in result['message']
        assert 'Test content' in result['message']
        assert 'Found 1 images' in result['message']

@pytest.mark.asyncio
async def test_web_browser_agent_with_image(web_browser_agent, test_image):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=f'''
            <html>
                <title>Test Page with Image</title>
                <p>Test content with image</p>
                <img src="{test_image}" alt="Test Image">
            </html>
        ''')
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await web_browser_agent.process_message({'text': 'https://test.com'})
        
        assert result['status'] == 'success'
        assert 'Test Page with Image' in result['message']
        assert 'Test content with image' in result['message']
        assert 'Found 1 images' in result['message']
        assert test_image in result['data']['images']

@pytest.mark.asyncio
async def test_web_search_agent_error_handling(web_search_agent):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.side_effect = Exception('Test error')
        
        result = await web_search_agent.process_message({'text': 'test query'})
        
        assert result['status'] == 'error'
        assert 'Test error' in result['message']

@pytest.mark.asyncio
async def test_web_browser_agent_error_handling(web_browser_agent):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.side_effect = Exception('Test error')
        
        result = await web_browser_agent.process_message({'text': 'https://test.com'})
        
        assert result['status'] == 'error'
        assert 'Test error' in result['message'] 