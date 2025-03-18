import ssl
from aiohttp import web
from aiogram import Bot, Dispatcher
from ..config import (
    WEBHOOK_HOST, 
    WEBHOOK_PORT, 
    WEBHOOK_URL_BASE,
    WEBHOOK_SSL_CERT,
    WEBHOOK_SSL_PRIV
)
from .logger import setup_logger

logger = setup_logger(__name__)

async def on_startup(bot: Bot, webhook_url: str = WEBHOOK_URL_BASE):
    """Действия при запуске webhook сервера"""
    logger.info("Настройка webhook...")
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != webhook_url:
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        logger.info(f"Webhook установлен: {webhook_url}")
    else:
        logger.info("Webhook уже установлен")

async def on_shutdown(bot: Bot):
    """Действия при остановке webhook сервера"""
    logger.info("Удаление webhook...")
    await bot.delete_webhook()
    logger.info("Webhook удален")

def setup_webhook_app(bot: Bot, dp: Dispatcher) -> web.Application:
    """Настраивает и возвращает webhook приложение"""
    app = web.Application()
    app['bot'] = bot
    app['dp'] = dp
    
    # Настраиваем обработчик для webhook
    async def handle_webhook(request):
        update_data = await request.json()
        await dp.feed_update(bot, update_data)
        return web.Response()
    
    # Регистрируем обработчик
    app.router.add_post('/webhook', handle_webhook)
    
    # Служебный маршрут для проверки работы сервера
    async def health_check(request):
        return web.Response(text="Bot webhook is running!")
    
    app.router.add_get('/', health_check)
    
    return app

def get_ssl_context():
    """Создает и возвращает SSL контекст для webhook"""
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)
    return ssl_context 