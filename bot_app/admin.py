from django.contrib import admin
from .models import User, WeightRecord, MeasurementRecord, Stage, Habit, DailyHabitLog

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'first_name', 'current_weight', 'target_weight', 'calculated_deadline', 'habit_fail_days')
    search_fields = ('telegram_id', 'username', 'first_name')

@admin.register(WeightRecord)
class WeightRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'weight', 'date')
    list_filter = ('date',)
    search_fields = ('user__telegram_id', 'user__username', 'user__first_name')

@admin.register(MeasurementRecord)
class MeasurementRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'chest', 'waist', 'hips')
    list_filter = ('date',)
    search_fields = ('user__telegram_id', 'user__username', 'user__first_name')

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_weight', 'is_achieved', 'achieved_date')
    list_filter = ('is_achieved', 'achieved_date')
    search_fields = ('user__telegram_id', 'user__username', 'user__first_name')

@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__telegram_id', 'user__username', 'user__first_name')

@admin.register(DailyHabitLog)
class DailyHabitLogAdmin(admin.ModelAdmin):
    list_display = ('habit', 'user', 'date', 'is_completed')
    list_filter = ('is_completed', 'date')
    search_fields = ('habit__name', 'user__telegram_id', 'user__username', 'user__first_name')