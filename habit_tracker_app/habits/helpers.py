from datetime import timedelta

from django.utils import timezone
from django.db.models import F

from .models import Habit, HabitLog, HABIT_LOG_STATUS_COMPLITED

def divide_habit_logs_of_weekly_habit_by_week_blocks(habit_logs):
    '''
        Создаёт двумерный массив логов a, где a[i] - список логов за 1 неделю. Также создаёт список ck, где ck[i] - сколько логов a[i] имеет статус 'complited'
    '''
    lk = list(habit_logs) # список всех логов
    a = [[] for _ in range((len(lk) // 7)+1)] # разбиение логов на недельные блоки ( двумерный массив ) 
    ck = [0 for _ in range(len(a))]
    for i in range(len(lk)):
        a[(i // 7)].append(lk[i])
        if lk[i].status == HABIT_LOG_STATUS_COMPLITED:
            ck[(i//7)] += 1
    return a, ck

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
    '''
        Функция увеличивает или обнуляет значение streak у привычки
    '''
    datetype = habit.habit_datetype
    last_created_habitLog = habit_logs.first()
    if datetype == 'week':
        habit_logs_list, count_complited_habit_logs_in_each_block = divide_habit_logs_of_weekly_habit_by_week_blocks(habit_logs)
        if len(habit_logs_list[-1])+1 == 7 and new_habit_log_status == HABIT_LOG_STATUS_COMPLITED: # +1 поскольку новый созданный (со статусом new_habit_log_status) нет в недельном блоке
            if count_complited_habit_logs_in_each_block[-1] + 1 >= habit.frequency:
                habit.streak = F("streak") + 1
                habit.save()
        elif new_habit_log_status != HABIT_LOG_STATUS_COMPLITED:
            if count_complited_habit_logs_in_each_block[-1] >= habit.frequency:
                habit.streak = F("streak") + 1
                habit.save()
    elif datetype == 'every_day':
        if habit_logs.count() == 0 and new_habit_log_status == HABIT_LOG_STATUS_COMPLITED:
                habit.streak = F("streak") + 1
                habit.save()
        elif new_habit_log_status == HABIT_LOG_STATUS_COMPLITED and last_created_habitLog.status == HABIT_LOG_STATUS_COMPLITED:
                habit.streak = F("streak") + 1
                habit.save()
        else:
            habit.streak = 0
            habit.save()


