from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from interfaces.agent_base import AgentBase

class AgentMiddleware(BaseMiddleware):
    def __init__(self, agent: AgentBase):
        self.agent = agent
        
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Добавляем агента в данные
        data["agent"] = self.agent
        return await handler(event, data) 