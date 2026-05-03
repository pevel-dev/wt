from aiogram import Router, types
from aiogram.filters import Command
from asgiref.sync import sync_to_async
from bot_app.models import User, Habit, DailyHabitLog, Stage
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q

router = Router()

@sync_to_async
def get_user(telegram_id: int):
    try:
        return User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        return None

@sync_to_async
def get_stats(user: User):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    habits = Habit.objects.filter(user=user, is_active=True)
    stats_text = "📊 Твоя статистика привычек:\n\n"
    
    if not habits.exists():
        return "У тебя нет активных привычек для статистики."

    for habit in habits:
        # Всего
        total_days = DailyHabitLog.objects.filter(habit=habit).count()
        completed_days = DailyHabitLog.objects.filter(habit=habit, is_completed=True).count()
        
        # Неделя
        week_completed = DailyHabitLog.objects.filter(habit=habit, is_completed=True, date__gte=start_of_week).count()
        
        # Месяц
        month_completed = DailyHabitLog.objects.filter(habit=habit, is_completed=True, date__gte=start_of_month).count()
        
        stats_text += f"🔹 {habit.name}:\n"
        stats_text += f"   На этой неделе: {week_completed} раз\n"
        stats_text += f"   В этом месяце: {month_completed} раз\n"
        stats_text += f"   За все время: {completed_days}/{total_days} ({round(completed_days/max(1, total_days)*100)}%)\n\n"
        
    return stats_text

@sync_to_async
def get_progress(user: User):
    stages = list(Stage.objects.filter(user=user).order_by('-target_weight'))
    
    text = f"📈 Твой прогресс:\n\n"
    text += f"Старт: {user.current_weight} кг (TODO: сохранить начальный вес, пока берем текущий как есть, но мы его обновляем)\n"
    text += f"Текущий вес: {user.current_weight} кг\n"
    text += f"Цель: {user.target_weight} кг\n"
    text += f"Сдвиг дедлайна из-за пропусков: +{user.habit_fail_days} дней\n"
    text += f"Расчетный дедлайн: {user.calculated_deadline}\n\n"
    
    text += "🚩 Этапы:\n"
    for stage in stages:
        status = "✅ Достигнут" if stage.is_achieved else "⏳ В процессе"
        date_achieved = f" ({stage.achieved_date.strftime('%Y-%m-%d')})" if stage.achieved_date else ""
        text += f"• {stage.target_weight} кг - {status}{date_achieved}\n"
        
    return text

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user = await get_user(message.from_user.id)
    if not user:
        return
        
    stats = await get_stats(user)
    await message.answer(stats)

@router.message(Command("progress"))
async def cmd_progress(message: types.Message):
    user = await get_user(message.from_user.id)
    if not user:
        return
        
    progress = await get_progress(user)
    await message.answer(progress)