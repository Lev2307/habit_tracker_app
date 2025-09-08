from datetime import timedelta

from django.utils import timezone
from django.db.models import F

from .models import Habit, HabitLog

HABITLOG_STATUS_COMPLITED = 'complited'

def set_habit_logs_status_forgot_to_mark(habit: Habit, last_habit_log_date):
    '''
        Создаёт модели HabitLog, которые не были созданы пользователем в промежутке хотя бы два дня между последним HabitLog (его датой) и текущей датой и присваивает им статус - forgot_to_mark 
    '''
    diff_in_days_between_last_log_date_and_now = (timezone.now().date() - last_habit_log_date).days
    if diff_in_days_between_last_log_date_and_now >= 2:
        for i in range(diff_in_days_between_last_log_date_and_now-1):
            date = timezone.now() + timedelta(days=-(diff_in_days_between_last_log_date_and_now-i-1))
            habitLog = HabitLog(habit=habit, comment='Забыли сделать отчёт!!', status='forgot_to_mark', date=date)
            habitLog.save()

def increase_habit_streak_field(habit: Habit, habit_logs, new_habit_log_status: str):
    datetype = habit.habit_datetype
    last_created_habitLog = habit_logs.first()
    if datetype == 'week':
        lk = list(habit_logs)
        habit_logs_list = [[] for _ in range((len(lk) // 7)+1)]
        count_complited_habit_logs_in_each_block = [0 for _ in range(len(habit_logs_list))]
        for i in range(len(lk)):
            habit_logs_list[(i // 7)].append(lk[i])
            if lk[i].status == HABITLOG_STATUS_COMPLITED:
                count_complited_habit_logs_in_each_block[(i//7)] += 1
        if len(habit_logs_list[-1])+1 == 7 and new_habit_log_status == HABITLOG_STATUS_COMPLITED:
            if count_complited_habit_logs_in_each_block[-1] + 1 >= habit.frequency:
                habit.streak = F("streak") + 1
                habit.save()
        elif new_habit_log_status != HABITLOG_STATUS_COMPLITED:
            if count_complited_habit_logs_in_each_block[-1] >= habit.frequency:
                habit.streak = F("streak") + 1
                habit.save()
    elif datetype == 'every_day':
        if habit_logs.count() == 0 and new_habit_log_status == HABITLOG_STATUS_COMPLITED:
                habit.streak = F("streak") + 1
                habit.save()
        elif new_habit_log_status == HABITLOG_STATUS_COMPLITED and last_created_habitLog.status == HABITLOG_STATUS_COMPLITED:
                habit.streak = F("streak") + 1
                habit.save()
        else:
            habit.streak = 0
            habit.save()



