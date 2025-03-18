from aiogram import Router, types
from aiogram.filters import Command
from ..utils.logger import setup_logger
from framework.agent_base import AIAgent

logger = setup_logger(__name__)
router = Router()

@router.message(Command("recall_memory"))
async def cmd_recall_memory(message: types.Message, agent: AIAgent):
    """Обработчик команды /recall_memory"""
    logger.info(f"Получена команда /recall_memory от пользователя {message.from_user.id}")
    memory = agent.recall_memory()
    result = "\n".join(memory) if memory else "Память пуста"
    await message.answer(result)
    logger.info(f"Отправлена память агента пользователю {message.from_user.id}") 