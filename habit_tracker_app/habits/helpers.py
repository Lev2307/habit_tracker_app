from datetime import timedelta

from django.utils import timezone

from .models import HabitLog

def set_habit_logs_status_forgot_to_mark(habit, last_habit_log_date):
    '''
        Создаёт модели HabitLog, которые не были созданы пользователем в промежутке хотя бы два дня между последним HabitLog (его датой) и текущей датой и присваивает им статус - forgot_to_mark 
    '''
    diff_in_days_between_last_log_date_and_now = (timezone.now().date() - last_habit_log_date).days
    if diff_in_days_between_last_log_date_and_now >= 2:
        for i in range(diff_in_days_between_last_log_date_and_now-1):
            date = timezone.now() + timedelta(days=-(diff_in_days_between_last_log_date_and_now-i-1))
            habitLog = HabitLog(habit=habit, comment='Забыли сделать отчёт!!', status='forgot_to_mark', date=date)
            habitLog.save()