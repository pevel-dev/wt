from django.db import models
from django.utils import timezone
from datetime import timedelta

class User(models.fields.related.Model if False else models.Model):
    telegram_id = models.BigIntegerField(primary_key=True, unique=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=255, null=True, blank=True, verbose_name="Username")
    first_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="First Name")
    current_weight = models.FloatField(null=True, blank=True, verbose_name="Текущий вес")
    target_weight = models.FloatField(null=True, blank=True, verbose_name="Целевой вес")
    start_date = models.DateField(auto_now_add=True, verbose_name="Дата начала")
    calculated_deadline = models.DateField(null=True, blank=True, verbose_name="Расчетный дедлайн")
    habit_fail_days = models.IntegerField(default=0, verbose_name="Дни провала привычек (сдвиг дедлайна)")
    
    # settings
    notifications_enabled = models.BooleanField(default=True, verbose_name="Уведомления включены")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name or self.username or self.telegram_id}"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class WeightRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="weight_records", verbose_name="Пользователь")
    weight = models.FloatField(verbose_name="Вес")
    date = models.DateTimeField(default=timezone.now, verbose_name="Дата записи")

    def __str__(self):
        return f"{self.user} - {self.weight}kg ({self.date.strftime('%Y-%m-%d')})"

    class Meta:
        verbose_name = "Запись веса"
        verbose_name_plural = "Записи веса"
        ordering = ['-date']


class MeasurementRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="measurements", verbose_name="Пользователь")
    date = models.DateTimeField(default=timezone.now, verbose_name="Дата записи")
    chest = models.FloatField(null=True, blank=True, verbose_name="Грудь (см)")
    waist = models.FloatField(null=True, blank=True, verbose_name="Талия (см)")
    hips = models.FloatField(null=True, blank=True, verbose_name="Бедра (см)")
    
    def __str__(self):
        return f"{self.user} measurements ({self.date.strftime('%Y-%m-%d')})"

    class Meta:
        verbose_name = "Замеры тела"
        verbose_name_plural = "Замеры тела"
        ordering = ['-date']


class Stage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stages", verbose_name="Пользователь")
    target_weight = models.FloatField(verbose_name="Целевой вес этапа")
    is_achieved = models.BooleanField(default=False, verbose_name="Достигнут")
    achieved_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата достижения")

    def __str__(self):
        return f"Этап {self.target_weight}kg для {self.user}"

    class Meta:
        verbose_name = "Этап (Микро-цель)"
        verbose_name_plural = "Этапы"
        ordering = ['-target_weight'] # desc


class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="habits", verbose_name="Пользователь")
    name = models.CharField(max_length=255, verbose_name="Название привычки")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user})"

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"


class DailyHabitLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="habit_logs", verbose_name="Пользователь")
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="logs", verbose_name="Привычка")
    date = models.DateField(default=timezone.now, verbose_name="Дата")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")

    def __str__(self):
        return f"{self.habit.name} - {self.date} - {'✅' if self.is_completed else '❌'}"

    class Meta:
        verbose_name = "Лог привычки"
        verbose_name_plural = "Логи привычек"
        unique_together = ('user', 'habit', 'date')
