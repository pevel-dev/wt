import os
from arq.connections import RedisSettings
from arq.cron import cron
from bot_app.tasks import daily_habit_checkin, weekly_measurement_reminder, deadline_shifter_job

redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(redis_url)
    functions = [
        daily_habit_checkin,
        weekly_measurement_reminder,
        deadline_shifter_job,
    ]
    cron_jobs = [
        # Ежедневный опрос в 20:00
        cron(daily_habit_checkin, hour=20, minute=0),
        # Еженедельное напоминание по воскресеньям в 10:00 (weekday=6 — воскресенье, как datetime.weekday())
        cron(weekly_measurement_reminder, weekday=6, hour=10, minute=0),
        # Проверка дедлайнов ночью в 01:00
        cron(deadline_shifter_job, hour=1, minute=0),
    ]