import os
import django
import sys
import logging
from aiogram import Bot
from datetime import timedelta
from django.utils import timezone
from asgiref.sync import sync_to_async

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from bot_app.models import User
from bot_app.handlers.habit_handlers import generate_habits_keyboard, check_all_habits_completed

logger = logging.getLogger(__name__)

async def get_bot():
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN is not set")
    return Bot(token=bot_token)

async def daily_habit_checkin(ctx):
    """
    Рассылка опроса по привычкам каждый вечер.
    """
    bot = await get_bot()
    today = timezone.now().date()
    
    # Получаем всех пользователей, у которых включены уведомления
    users = await sync_to_async(list)(User.objects.filter(notifications_enabled=True))
    
    for user in users:
        try:
            keyboard = await generate_habits_keyboard(user, today)
            await bot.send_message(
                chat_id=user.telegram_id,
                text="Привет! Как прошел день? Отметь выполненные привычки:",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error sending habit checkin to {user.telegram_id}: {e}")

async def weekly_measurement_reminder(ctx):
    """
    Напоминание о взвешивании и замерах.
    """
    bot = await get_bot()
    users = await sync_to_async(list)(User.objects.filter(notifications_enabled=True))
    
    for user in users:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text="📅 Прошла неделя! Пора занести свежие данные.\n"
                     "Введи новый вес командой /weight\n"
                     "И обнови замеры тела: /measurements"
            )
        except Exception as e:
            logger.error(f"Error sending weekly reminder to {user.telegram_id}: {e}")

async def deadline_shifter_job(ctx):
    """
    Проверяет вчерашний день, если не все привычки выполнены - сдвигает дедлайн.
    """
    yesterday = timezone.now().date() - timedelta(days=1)
    users = await sync_to_async(list)(User.objects.all())
    
    for user in users:
        # Проверяем, все ли привычки выполнены за вчера
        all_completed = await check_all_habits_completed(user, yesterday)
        if not all_completed:
            # Сдвигаем дедлайн
            user.habit_fail_days += 1
            if user.calculated_deadline:
                user.calculated_deadline += timedelta(days=1)
            await sync_to_async(user.save)()
            
            # Можно уведомить пользователя
            if user.notifications_enabled:
                bot = await get_bot()
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text="⚠️ Вчера ты не отметил все привычки, поэтому дедлайн достижения цели сдвинут на 1 день."
                    )
                except Exception:
                    pass