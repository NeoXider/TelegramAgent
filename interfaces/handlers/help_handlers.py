from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from ..utils.logger import setup_logger
from ..utils.admin_manager import AdminManager
from ..config import ADMIN_PASSWORD

logger = setup_logger(__name__)
router = Router()

# Инициализация менеджера администраторов
admin_manager = AdminManager(ADMIN_PASSWORD)

# Список команд для BotFather
BOT_COMMANDS = """
about - Информация о боте и его возможностях
help - Показать справку по командам
models - Показать текущие модели
list_models - Показать список всех доступных моделей
auth - Авторизация администратора
set_model - Установить модель (только для администраторов)
"""

@router.message(Command("help"))
async def help_command(message: Message):
    """Показать справку по командам"""
    response_lines = [
        "*Доступные команды*:",
        "\\- `/about` \\- информация о боте и его возможностях",
        "\\- `/help` \\- показать эту справку",
        "\\- `/models` \\- показать текущие модели",
        "\\- `/list_models` \\- показать список всех доступных моделей",
        "\n*Использование бота*:",
        "\\- Отправьте текстовое сообщение для получения ответа",
        "\\- Отправьте изображение для его анализа",
        "\\- В групповых чатах используйте упоминание бота или ответ на его сообщение"
    ]
    
    # Добавляем информацию для администраторов или потенциальных администраторов
    if admin_manager.is_admin(message.from_user.id):
        response_lines.extend([
            "\n*Команды администратора*:",
            "\\- `/set_model основная ИМЯ_МОДЕЛИ` \\- установить основную модель",
            "\\- `/set_model зрение ИМЯ_МОДЕЛИ` \\- установить модель для изображений",
            "\nДля просмотра доступных моделей используйте `/list_models`"
        ])
    else:
        remaining = admin_manager.get_remaining_attempts(message.from_user.id)
        if remaining is not None and remaining > 0:
            response_lines.extend([
                "\n*Авторизация администратора*:",
                "\\- `/auth ПАРОЛЬ` \\- получить права администратора",
                f"Осталось попыток: `{remaining}`"
            ])
    
    await message.reply(
        "\n".join(response_lines),
        parse_mode=ParseMode.MARKDOWN_V2
    ) 