from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from bot_app.models import User, MeasurementRecord
from bot_app.services import update_user_weight

router = Router()

class UpdateWeight(StatesGroup):
    waiting_for_weight = State()

class UpdateMeasurements(StatesGroup):
    waiting_for_chest = State()
    waiting_for_waist = State()
    waiting_for_hips = State()

@sync_to_async
def get_user(telegram_id: int):
    try:
        return User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        return None

@sync_to_async
def save_measurements(user: User, chest: float, waist: float, hips: float):
    MeasurementRecord.objects.create(user=user, chest=chest, waist=waist, hips=hips)

@router.message(Command("weight"))
async def cmd_update_weight(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала пройди регистрацию /start")
        return
        
    await message.answer(f"Введи свой новый вес (кг), текущий: {user.current_weight}кг:")
    await state.set_state(UpdateWeight.waiting_for_weight)

@router.message(UpdateWeight.waiting_for_weight)
async def process_new_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.replace(',', '.'))
        if weight <= 0 or weight > 300:
            raise ValueError
            
        user = await get_user(message.from_user.id)
        if not user:
            return
            
        messages = await update_user_weight(user, weight)
        
        response = f"Вес обновлен: {weight} кг.\nНовый расчетный дедлайн: {user.calculated_deadline}"
        if messages:
            response += "\n\n" + "\n".join(messages)
            
        await message.answer(response)
        await state.clear()
        
    except ValueError:
        await message.answer("Пожалуйста, введи корректный вес числом.")

@router.message(Command("measurements"))
async def cmd_update_measurements(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала пройди регистрацию /start")
        return
        
    await message.answer("Давай сделаем замеры. Введи обхват груди (см):")
    await state.set_state(UpdateMeasurements.waiting_for_chest)

@router.message(UpdateMeasurements.waiting_for_chest)
async def process_chest(message: types.Message, state: FSMContext):
    try:
        chest = float(message.text.replace(',', '.'))
        await state.update_data(chest=chest)
        await message.answer("Введи обхват талии (см):")
        await state.set_state(UpdateMeasurements.waiting_for_waist)
    except ValueError:
        await message.answer("Пожалуйста, введи число.")

@router.message(UpdateMeasurements.waiting_for_waist)
async def process_waist(message: types.Message, state: FSMContext):
    try:
        waist = float(message.text.replace(',', '.'))
        await state.update_data(waist=waist)
        await message.answer("Введи обхват бедер (см):")
        await state.set_state(UpdateMeasurements.waiting_for_hips)
    except ValueError:
        await message.answer("Пожалуйста, введи число.")

@router.message(UpdateMeasurements.waiting_for_hips)
async def process_hips(message: types.Message, state: FSMContext):
    try:
        hips = float(message.text.replace(',', '.'))
        data = await state.get_data()
        
        user = await get_user(message.from_user.id)
        if not user:
            return
            
        await save_measurements(user, data['chest'], data['waist'], hips)
        await message.answer("Замеры успешно сохранены! 📏")
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введи число.")