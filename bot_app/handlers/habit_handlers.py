from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from bot_app.models import User, Habit, DailyHabitLog
from django.utils import timezone
import datetime

router = Router()

class HabitStates(StatesGroup):
    waiting_for_habit_name = State()

@sync_to_async
def get_user(telegram_id: int):
    try:
        return User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        return None

@sync_to_async
def get_active_habits(user: User):
    return list(Habit.objects.filter(user=user, is_active=True).order_by('created_at'))

@sync_to_async
def create_habit(user: User, name: str):
    Habit.objects.create(user=user, name=name)

@sync_to_async
def get_habit_log(user: User, habit: Habit, date: datetime.date):
    log, created = DailyHabitLog.objects.get_or_create(user=user, habit=habit, date=date)
    return log

@sync_to_async
def toggle_habit_log(user: User, habit_id: int, date: datetime.date):
    habit = Habit.objects.get(id=habit_id, user=user)
    log, created = DailyHabitLog.objects.get_or_create(user=user, habit=habit, date=date)
    log.is_completed = not log.is_completed
    log.save()
    return log.is_completed

@sync_to_async
def check_all_habits_completed(user: User, date: datetime.date):
    active_habits = Habit.objects.filter(user=user, is_active=True)
    if not active_habits.exists():
        return True
    
    logs = DailyHabitLog.objects.filter(user=user, date=date, habit__in=active_habits)
    # Если логов меньше чем привычек, или есть невыполненные
    if logs.count() < active_habits.count() or logs.filter(is_completed=False).exists():
        return False
    return True

@router.message(Command("habits"))
async def cmd_habits(message: types.Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала пройди регистрацию /start")
        return
        
    habits = await get_active_habits(user)
    
    if not habits:
        await message.answer("У тебя пока нет активных привычек.\nДобавь новую: /add_habit")
    else:
        text = "Твои привычки для похудения:\n"
        for idx, habit in enumerate(habits, 1):
            text += f"{idx}. {habit.name}\n"
        text += "\nДобавить новую: /add_habit"
        await message.answer(text)

@router.message(Command("add_habit"))
async def cmd_add_habit(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        return
    await message.answer("Введи название новой привычки (например, 'Пить 2л воды' или 'Тренировка 30 мин'):")
    await state.set_state(HabitStates.waiting_for_habit_name)

@router.message(HabitStates.waiting_for_habit_name)
async def process_habit_name(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        return
        
    habit_name = message.text.strip()
    if len(habit_name) > 255:
        await message.answer("Название слишком длинное. Попробуй покороче:")
        return
        
    await create_habit(user, habit_name)
    await message.answer(f"Привычка '{habit_name}' добавлена! ✅\nОна появится в ежедневном отчете.")
    await state.clear()

async def generate_habits_keyboard(user: User, date: datetime.date):
    habits = await get_active_habits(user)
    builder = InlineKeyboardBuilder()
    
    for habit in habits:
        log = await get_habit_log(user, habit, date)
        status_icon = "✅" if log.is_completed else "❌"
        builder.row(types.InlineKeyboardButton(
            text=f"{status_icon} {habit.name}",
            callback_data=f"toggle_habit_{habit.id}_{date.isoformat()}"
        ))
        
    builder.row(types.InlineKeyboardButton(
        text="🏁 Завершить день",
        callback_data=f"finish_day_{date.isoformat()}"
    ))
    return builder.as_markup()

@router.message(Command("today"))
async def cmd_today_habits(message: types.Message):
    user = await get_user(message.from_user.id)
    if not user:
        return
        
    today = timezone.now().date()
    habits = await get_active_habits(user)
    
    if not habits:
        await message.answer("У тебя нет добавленных привычек. Добавь их командой /add_habit")
        return
        
    keyboard = await generate_habits_keyboard(user, today)
    await message.answer("Отметь выполненные привычки на сегодня:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("toggle_habit_"))
async def process_habit_toggle(callback: types.CallbackQuery):
    _, _, habit_id, date_str = callback.data.split("_")
    date = datetime.date.fromisoformat(date_str)
    
    user = await get_user(callback.from_user.id)
    if not user:
        return
        
    is_completed = await toggle_habit_log(user, int(habit_id), date)
    
    # Обновляем клавиатуру
    keyboard = await generate_habits_keyboard(user, date)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer("Статус обновлен")

@router.callback_query(F.data.startswith("finish_day_"))
async def process_finish_day(callback: types.CallbackQuery):
    _, _, date_str = callback.data.split("_")
    date = datetime.date.fromisoformat(date_str)
    
    user = await get_user(callback.from_user.id)
    if not user:
        return
        
    all_completed = await check_all_habits_completed(user, date)
    
    if all_completed:
        await callback.message.edit_text(f"День завершен ({date_str})! Молодец, все привычки выполнены! 🌟")
    else:
        # Не все привычки выполнены - день будет сдвинут ночной джобой
        await callback.message.edit_text(f"День завершен ({date_str}). Ты выполнил не все привычки 😢. Дедлайн будет сдвинут на 1 день.")
    
    await callback.answer()