from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from ..utils.logger import setup_logger
from ..utils.admin_manager import AdminManager
from ..utils.global_model_manager import GlobalModelManager
from ..utils.model_manager import model_manager
from ..config import ADMIN_PASSWORD

logger = setup_logger(__name__)
router = Router()

# Инициализация менеджеров
admin_manager = AdminManager(ADMIN_PASSWORD)
global_model_manager = GlobalModelManager()

@router.message(Command("list_models"))
async def list_models_command(message: Message):
    """Показать список всех доступных моделей"""
    try:
        # Получаем список всех моделей
        models = await model_manager.get_available_models()
        
        if not models:
            await message.reply(
                "*Ошибка*: Не удалось получить список моделей\\. Проверьте, запущен ли Ollama\\.",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return

        # Проверяем поддержку изображений для каждой модели
        vision_models = []
        text_models = []
        
        for model in models:
            # Экранируем специальные символы для Markdown
            safe_model = model.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_")
            
            if await model_manager.check_model_vision_support(model):
                vision_models.append(safe_model)
            text_models.append(safe_model)

        # Формируем ответное сообщение
        response_lines = ["*Доступные модели*:"]
        
        response_lines.append("\n*Модели с поддержкой изображений*:")
        for model in vision_models:
            response_lines.append(f"\\- `{model}`")
        
        response_lines.append("\n*Все модели*:")
        for model in text_models:
            response_lines.append(f"\\- `{model}`")

        # Добавляем инструкцию для администраторов
        if admin_manager.is_admin(message.from_user.id):
            response_lines.append("\nДля установки модели используйте команду:")
            response_lines.append("`/set_model основная ИМЯ_МОДЕЛИ`")
            response_lines.append("`/set_model зрение ИМЯ_МОДЕЛИ`")

        await message.reply(
            "\n".join(response_lines),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка моделей: {e}")
        await message.reply(
            "*Ошибка*: Произошла ошибка при получении списка моделей\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )

@router.message(Command("models"))
async def show_models_command(message: Message):
    """Показать текущие модели"""
    models = global_model_manager.get_all_models()
    response_lines = ["*Текущие модели*:"]
    
    for model_type, model_name in models.items():
        model_str = model_name if model_name else "не выбрана"
        # Экранируем специальные символы для Markdown
        model_type = model_type.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_")
        model_str = model_str.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_")
        response_lines.append(f"`{model_type}`: `{model_str}`")
    
    if admin_manager.is_admin(message.from_user.id):
        response_lines.append("\nВы администратор и можете менять модели с помощью команды `/set_model`")
        response_lines.append("Для просмотра всех доступных моделей используйте `/list_models`")
    else:
        remaining = admin_manager.get_remaining_attempts(message.from_user.id)
        if remaining is not None and remaining > 0:
            response_lines.append(f"\nДля изменения моделей необходимо стать администратором\\. Осталось попыток: `{remaining}`")
        elif remaining == 0:
            response_lines.append("\nУ вас закончились попытки стать администратором")
    
    await message.reply(
        "\n".join(response_lines),
        parse_mode=ParseMode.MARKDOWN_V2
    )

@router.message(Command("auth"))
async def auth_command(message: Message):
    """Аутентификация администратора"""
    if admin_manager.is_admin(message.from_user.id):
        await message.reply(
            "*Вы уже являетесь администратором*",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    remaining = admin_manager.get_remaining_attempts(message.from_user.id)
    if remaining == 0:
        await message.reply(
            "*У вас закончились попытки*\\. Обратитесь к владельцу бота\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    # Проверяем формат команды
    args = message.text.split()
    if len(args) != 2:
        await message.reply(
            "Используйте формат: `/auth ПАРОЛЬ`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    password = args[1]
    if admin_manager.check_password(message.from_user.id, password):
        await message.reply(
            "*Аутентификация успешна\\!* Теперь вы администратор",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        remaining = admin_manager.get_remaining_attempts(message.from_user.id)
        await message.reply(
            f"*Неверный пароль*\\. Осталось попыток: `{remaining}`",
            parse_mode=ParseMode.MARKDOWN_V2
        )

@router.message(Command("set_model"))
async def set_model_command(message: Message):
    """Установка модели (только для администраторов)"""
    if not admin_manager.is_admin(message.from_user.id):
        await message.reply(
            "*Ошибка*: Эта команда доступна только администраторам\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    args = message.text.split()
    if len(args) != 3:
        await message.reply(
            "Используйте формат: `/set_model ТИП_МОДЕЛИ ИМЯ_МОДЕЛИ`\n\n"
            "*Типы моделей*:\n"
            "\\- `основная`\n"
            "\\- `зрение`\n\n"
            "Для просмотра доступных моделей используйте `/list_models`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    model_type = args[1]
    model_name = args[2]

    # Проверяем существование модели
    available_models = await model_manager.get_available_models()
    if model_name not in available_models:
        # Экранируем специальные символы для ответа
        safe_model_name = model_name.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_")
        await message.reply(
            f"*Ошибка*: Модель `{safe_model_name}` не найдена\\.\n"
            "Используйте команду `/list_models` для просмотра доступных моделей\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    # Проверяем поддержку изображений для модели зрения
    if model_type == "зрение" and not await model_manager.check_model_vision_support(model_name):
        # Экранируем специальные символы для ответа
        safe_model_name = model_name.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_")
        await message.reply(
            f"*Ошибка*: Модель `{safe_model_name}` не поддерживает работу с изображениями\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    # Экранируем специальные символы для ответа
    safe_model_name = model_name.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_")
    safe_model_type = model_type.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_")

    if global_model_manager.set_model(model_type, model_name):
        await message.reply(
            f"*Успешно\\!* Модель `{safe_model_name}` установлена для типа `{safe_model_type}`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await message.reply(
            "*Ошибка*: Неверный тип модели\\.\n"
            "*Доступные типы*:\n"
            "\\- `основная`\n"
            "\\- `зрение`",
            parse_mode=ParseMode.MARKDOWN_V2
        )

@router.message(Command("about"))
async def about_command(message: Message):
    """Показать информацию о текущей модели и возможностях бота"""
    models = global_model_manager.get_all_models()
    
    # Получаем информацию о текущих моделях
    main_model = models.get("основная", "не выбрана")
    vision_model = models.get("зрение", "не выбрана")
    
    # Экранируем специальные символы для Markdown
    safe_main_model = main_model.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_") if main_model else "не выбрана"
    safe_vision_model = vision_model.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_") if vision_model else "не выбрана"
    
    response_lines = [
        "*О боте*",
        f"\n*Текущая модель*: `{safe_main_model}`",
        f"*Модель для изображений*: `{safe_vision_model}`",
        "\n*Возможности*:",
        "\\- Ответы на вопросы",
        "\\- Анализ изображений",
        "\\- Помощь с кодом",
        "\\- Объяснение сложных тем",
        "\n*Команды*:",
        "\\- `/about` \\- информация о боте",
        "\\- `/models` \\- список текущих моделей",
        "\\- `/list_models` \\- список всех доступных моделей"
    ]
    
    if admin_manager.is_admin(message.from_user.id):
        response_lines.extend([
            "\n*Команды администратора*:",
            "\\- `/set_model` \\- изменить модель"
        ])
    else:
        remaining = admin_manager.get_remaining_attempts(message.from_user.id)
        if remaining is not None and remaining > 0:
            response_lines.append(f"\nДля доступа к дополнительным возможностям используйте `/auth`\\. Осталось попыток: `{remaining}`")
    
    await message.reply(
        "\n".join(response_lines),
        parse_mode=ParseMode.MARKDOWN_V2
    ) 