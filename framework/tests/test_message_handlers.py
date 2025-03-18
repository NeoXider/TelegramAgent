import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from framework.handlers.message_handlers import MessageHandlers

@pytest.fixture
def config():
    return {
        "models": {
            "default": "test_model"
        },
        "bot": {
            "name": "TestBot",
            "username": "test_bot"
        }
    }

@pytest.fixture
def handlers(config):
    return MessageHandlers(config)

def create_message_mock(chat_id, is_private=True, text="test", mentions_bot=False):
    message = MagicMock()
    message.chat.id = chat_id
    message.chat.type = "private" if is_private else "group"
    message.text = text
    message.entities = []
    message.caption = None
    message.caption_entities = []
    message.answer = AsyncMock()
    
    # Создаем объект from_user
    from_user = MagicMock()
    from_user.id = abs(chat_id)  # Используем абсолютное значение chat_id как user_id
    message.from_user = from_user
    
    if mentions_bot:
        mention = MagicMock()
        mention.type = "mention"
        mention.text = "@test_bot"
        message.entities.append(mention)
        message.caption_entities.append(mention)
    
    return message

@pytest.mark.asyncio
async def test_handle_message_private_chat(handlers):
    """Тест обработки сообщения в приватном чате"""
    message = create_message_mock(123456, is_private=True)
    
    with patch('framework.agents.message_agent.MessageAgent.process_message') as mock_process:
        mock_process.return_value = {
            "action": "send_message",
            "text": "Тестовый ответ"
        }
        
        result = await handlers.handle_message(message)
        assert result["action"] == "send_message"
        assert result["text"] == "Тестовый ответ"
        mock_process.assert_called_once()

@pytest.mark.asyncio
async def test_handle_message_group_chat(handlers):
    """Тест обработки сообщения в групповом чате с упоминанием бота"""
    message = create_message_mock(-123456, is_private=False, mentions_bot=True)

    with patch('framework.agents.message_agent.MessageAgent.process_message', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {
            "action": "send_message",
            "text": "Тестовый ответ"
        }

        result = await handlers.handle_message(message)
        assert result["action"] == "send_message"
        assert result["text"] == "Тестовый ответ"
        mock_process.assert_called_once_with(message.text, message.from_user.id, message.chat.id)

@pytest.mark.asyncio
async def test_handle_message_ignore(handlers):
    """Тест игнорирования сообщения в групповом чате без упоминания бота"""
    message = create_message_mock(-123456, is_private=False)
    
    result = await handlers.handle_message(message)
    assert result["action"] == "ignore"

@pytest.mark.asyncio
async def test_handle_photo_private_chat(handlers):
    """Тест обработки фото в приватном чате"""
    message = create_message_mock(123456, is_private=True)
    message.photo = [MagicMock()]
    message.photo[-1].file_id = "test_file_id"

    with patch('framework.agents.image_agent.ImageAgent.process_image', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {
            "action": "send_message",
            "text": "Описание изображения"
        }

        result = await handlers.handle_photo(message)
        assert result["action"] == "send_message"
        assert result["text"] == "Описание изображения"
        mock_process.assert_called_once_with("test_file_id", message.from_user.id, message.chat.id)

@pytest.mark.asyncio
async def test_handle_photo_group_chat(handlers):
    """Тест обработки фото в групповом чате с упоминанием бота"""
    message = create_message_mock(-123456, is_private=False, mentions_bot=True)
    message.photo = [MagicMock()]
    message.photo[-1].file_id = "test_file_id"

    with patch('framework.agents.image_agent.ImageAgent.process_image', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {
            "action": "send_message",
            "text": "Описание изображения"
        }

        result = await handlers.handle_photo(message)
        assert result["action"] == "send_message"
        assert result["text"] == "Описание изображения"
        mock_process.assert_called_once_with("test_file_id", message.from_user.id, message.chat.id)

@pytest.mark.asyncio
async def test_handle_document_private_chat(handlers):
    """Тест обработки документа в приватном чате"""
    message = create_message_mock(123456, is_private=True)
    message.document = MagicMock()
    message.document.file_id = "test_file_id"

    with patch('framework.agents.document_agent.DocumentAgent.process_document', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {
            "action": "send_message",
            "text": "Содержание документа"
        }

        result = await handlers.handle_document(message)
        assert result["action"] == "send_message"
        assert result["text"] == "Содержание документа"
        mock_process.assert_called_once_with("test_file_id", message.from_user.id, message.chat.id)

@pytest.mark.asyncio
async def test_handle_document_group_chat(handlers):
    """Тест обработки документа в групповом чате с упоминанием бота"""
    message = create_message_mock(-123456, is_private=False, mentions_bot=True)
    message.document = MagicMock()
    message.document.file_id = "test_file_id"

    with patch('framework.agents.document_agent.DocumentAgent.process_document', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {
            "action": "send_message",
            "text": "Содержание документа"
        }

        result = await handlers.handle_document(message)
        assert result["action"] == "send_message"
        assert result["text"] == "Содержание документа"
        mock_process.assert_called_once_with("test_file_id", message.from_user.id, message.chat.id)

@pytest.mark.asyncio
async def test_handle_message_error(handlers):
    """Тест обработки ошибки в сообщении"""
    message = create_message_mock(123456, is_private=True)
    
    with patch('framework.agents.message_agent.MessageAgent.process_message', new_callable=AsyncMock) as mock_process:
        mock_process.side_effect = Exception("Тестовая ошибка")
        
        result = await handlers.handle_message(message)
        assert result["action"] == "send_message"
        assert "Произошла ошибка при обработке сообщения" in result["text"]
        mock_process.assert_called_once()

@pytest.mark.asyncio
async def test_handle_photo_error(handlers):
    """Тест обработки ошибки в фото"""
    message = create_message_mock(123456, is_private=True)
    message.photo = [MagicMock()]
    message.photo[-1].file_id = "test_file_id"

    with patch('framework.agents.image_agent.ImageAgent.process_image', new_callable=AsyncMock) as mock_process:
        mock_process.side_effect = Exception("Тестовая ошибка")

        result = await handlers.handle_photo(message)
        assert result["action"] == "send_message"
        assert "Произошла ошибка при обработке фото" in result["text"]
        mock_process.assert_called_once_with("test_file_id", message.from_user.id, message.chat.id)

@pytest.mark.asyncio
async def test_handle_document_error(handlers):
    """Тест обработки ошибки в документе"""
    message = create_message_mock(123456, is_private=True)
    message.document = MagicMock()
    message.document.file_id = "test_file_id"

    with patch('framework.agents.document_agent.DocumentAgent.process_document', new_callable=AsyncMock) as mock_process:
        mock_process.side_effect = Exception("Тестовая ошибка")

        result = await handlers.handle_document(message)
        assert result["action"] == "send_message"
        assert "Произошла ошибка при обработке документа" in result["text"]
        mock_process.assert_called_once_with("test_file_id", message.from_user.id, message.chat.id)

@pytest.mark.asyncio
async def test_handle_message_empty_text(handlers):
    """Тест обработки сообщения с пустым текстом"""
    message = create_message_mock(123456, is_private=True)
    message.text = ""

    result = await handlers.handle_message(message)
    assert result["action"] == "ignore"

@pytest.mark.asyncio
async def test_handle_photo_no_file_id(handlers):
    """Тест обработки фото без file_id"""
    message = create_message_mock(123456, is_private=True)
    message.photo = [MagicMock()]
    message.photo[-1].file_id = None

    result = await handlers.handle_photo(message)
    assert result["action"] == "ignore"

@pytest.mark.asyncio
async def test_handle_document_no_file_id(handlers):
    """Тест обработки документа без file_id"""
    message = create_message_mock(123456, is_private=True)
    message.document = MagicMock()
    message.document.file_id = None

    result = await handlers.handle_document(message)
    assert result["action"] == "ignore" 