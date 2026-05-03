from datetime import timedelta
from django.utils import timezone
from bot_app.models import User, Stage, WeightRecord
from asgiref.sync import sync_to_async

@sync_to_async
def calculate_and_save_onboarding(user: User, current_weight: float, target_weight: float):
    """
    Рассчитывает дедлайн и этапы при регистрации.
    """
    user.current_weight = current_weight
    user.target_weight = target_weight
    
    _recalculate_deadline(user, current_weight, target_weight)
    
    # Сохраняем первую запись веса
    WeightRecord.objects.create(user=user, weight=current_weight)

    # Генерация этапов
    generate_stages(user, current_weight, target_weight)

def _recalculate_deadline(user: User, current_weight: float, target_weight: float):
    weight_diff = current_weight - target_weight
    if weight_diff <= 0:
        user.calculated_deadline = timezone.now().date()
        user.save()
        return

    # 1% от текущего веса в неделю
    avg_loss_per_week = current_weight * 0.01
    weeks_needed = weight_diff / avg_loss_per_week
    days_needed = int(weeks_needed * 7)
    
    user.calculated_deadline = timezone.now().date() + timedelta(days=days_needed)
    user.save()

@sync_to_async
def update_user_weight(user: User, new_weight: float):
    """
    Обновляет вес, пересчитывает дедлайн, отмечает/сбрасывает этапы
    Возвращает список сообщений о достигнутых этапах или откатах
    """
    old_weight = user.current_weight
    user.current_weight = new_weight
    
    # Пересчет дедлайна с новым весом (как "остаток пути")
    _recalculate_deadline(user, new_weight, user.target_weight)
    
    WeightRecord.objects.create(user=user, weight=new_weight)
    
    messages = []
    
    # Проверка этапов (они отсортированы по убыванию, от большего веса к меньшему)
    # Например: 88, 83, 80, 78, 76
    stages = list(Stage.objects.filter(user=user).order_by('-target_weight'))
    
    for stage in stages:
        if new_weight <= stage.target_weight and not stage.is_achieved:
            stage.is_achieved = True
            stage.achieved_date = timezone.now()
            stage.save()
            messages.append(f"🎉 Поздравляю! Ты достиг этапа {stage.target_weight} кг!")
        elif new_weight > stage.target_weight and stage.is_achieved:
            # Откат: вес стал больше, чем граница этапа.
            # По ТЗ: "отменяет при достижении границы предыдущего этапа"
            # Чтобы не было "моргания" туда-сюда на 100 грамм, можно отменять, если превышен на +X,
            # но по ТЗ четко: отменяет при достижении границы *предыдущего* этапа.
            # Найдем границу предыдущего (более тяжелого) этапа.
            idx = stages.index(stage)
            prev_stage_target = stages[idx-1].target_weight if idx > 0 else (user.target_weight + 100) # Если первый этап, берем условный старт
            
            # Если вес превысил границу *предыдущего* этапа (который тяжелее), откатываем текущий достигнутый
            if new_weight >= prev_stage_target:
                stage.is_achieved = False
                stage.achieved_date = None
                stage.save()
                messages.append(f"⚠️ Внимание! Произошел откат: этап {stage.target_weight} кг сброшен. Не сдавайся!")
    
    if new_weight <= user.target_weight:
         messages.append(f"🏆 УРА! ЦЕЛЕВОЙ ВЕС {user.target_weight} КГ ДОСТИГНУТ!")

    return messages

def generate_stages(user: User, current_weight: float, target_weight: float):
    Stage.objects.filter(user=user).delete()
    
    stages = []
    current_stage_target = current_weight

    while current_stage_target > target_weight:
        if current_stage_target > 80:
            current_stage_target -= 5
            if current_stage_target < 80:
                current_stage_target = 80
        else:
            current_stage_target -= 2
        
        if current_stage_target < target_weight:
            current_stage_target = target_weight
            
        if current_stage_target >= current_weight:
            break
            
        stages.append(Stage(user=user, target_weight=round(current_stage_target, 1)))

    if stages:
        Stage.objects.bulk_create(stages)

@sync_to_async
def get_user_stages(user: User):
    return list(Stage.objects.filter(user=user).order_by('-target_weight'))