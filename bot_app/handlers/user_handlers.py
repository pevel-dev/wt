from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from bot_app.models import User
from bot_app.services import calculate_and_save_onboarding

router = Router()

class Registration(StatesGroup):
    waiting_for_current_weight = State()
    waiting_for_target_weight = State()

@sync_to_async
def get_or_create_user(telegram_id: int, username: str, first_name: str):
    user, created = User.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'username': username,
            'first_name': first_name
        }
    )
    return user, created

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    user, created = await get_or_create_user(user_id, username, first_name)
    
    if created or not user.current_weight or not user.target_weight:
        await message.answer(f"Привет, {first_name}! Я бот для трекинга похудения. Введи свой текущий вес (кг), например 85.5:")
        await state.set_state(Registration.waiting_for_current_weight)
    else:
        await message.answer(f"С возвращением, {first_name}! Твой текущий вес: {user.current_weight}кг, цель: {user.target_weight}кг. Дедлайн: {user.calculated_deadline}")
        # Здесь можно вывести меню или стату

@router.message(Registration.waiting_for_current_weight)
async def process_current_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.replace(',', '.'))
        if weight <= 0 or weight > 300:
            raise ValueError
        
        await state.update_data(current_weight=weight)
        await message.answer("Отлично. Теперь введи свой целевой вес (кг), который планируешь достичь:")
        await state.set_state(Registration.waiting_for_target_weight)
    except ValueError:
        await message.answer("Пожалуйста, введи корректный вес числом, например 85.5.")

@router.message(Registration.waiting_for_target_weight)
async def process_target_weight(message: types.Message, state: FSMContext):
    try:
        target_weight = float(message.text.replace(',', '.'))
        if target_weight <= 0 or target_weight > 300:
            raise ValueError
        
        data = await state.get_data()
        current_weight = data['current_weight']

        if target_weight >= current_weight:
            await message.answer("Целевой вес должен быть меньше текущего. Попробуй еще раз:")
            return

        user_id = message.from_user.id
        user, _ = await get_or_create_user(user_id, message.from_user.username, message.from_user.first_name)
        
        await calculate_and_save_onboarding(user, current_weight, target_weight)

        await message.answer(
            f"Регистрация завершена! 🎉\n"
            f"Текущий вес: {current_weight} кг.\n"
            f"Целевой вес: {target_weight} кг.\n"
            f"Расчетный дедлайн (при потере 1% в неделю): {user.calculated_deadline}\n\n"
            f"Я разбил твой путь на этапы! Буду помогать тебе отслеживать их. Не забудь добавить привычки с помощью команды /habits"
        )
        await state.clear()
        
    except ValueError:
        await message.answer("Пожалуйста, введи корректный вес числом, например 75.0.")
