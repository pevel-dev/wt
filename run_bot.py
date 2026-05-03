import os
import django
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from bot_app.handlers import user_handlers, progress_handlers, habit_handlers, stats_handlers

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Регистрация / Главное меню"),
        BotCommand(command="weight", description="Обновить вес"),
        BotCommand(command="measurements", description="Внести замеры"),
        BotCommand(command="add_habit", description="Добавить привычку"),
        BotCommand(command="habits", description="Мои привычки"),
        BotCommand(command="today", description="Отметить привычки за сегодня"),
        BotCommand(command="progress", description="Посмотреть прогресс (этапы, дедлайн)"),
        BotCommand(command="stats", description="Статистика по привычкам"),
    ]
    await bot.set_my_commands(commands)

async def main():
    load_dotenv()
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN environment variable is not set.")
        return

    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register handlers
    dp.include_router(user_handlers.router)
    dp.include_router(progress_handlers.router)
    dp.include_router(habit_handlers.router)
    dp.include_router(stats_handlers.router)
    
    await setup_bot_commands(bot)

    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")