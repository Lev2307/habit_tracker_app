from django.test import TestCase
from django.urls import reverse

from .factories import create_user, create_habit, create_habit_log
from ..models import Habit, HabitLog, HABIT_LOG_STATUS_COMPLITED, HABIT_LOG_STATUS_INCOMPLITED


class HabitHelpersTests(TestCase):
    def setUp(self):
        self.username1 = 'admin1_helpers'
        self.password1 = 'password123_helpers'

        self.user = create_user(self.username1, self.password1)
        self.habit_weekly = create_habit(self.user, 'Habit weekly test habit_helpers', 'habit helpers purpose', 'weekly', 2)
        self.habit_daily = create_habit(self.user, 'Habit every day  test habit_helpers', 'habit helpers purpose', 'daily')

    def test_creation_habitlogs_with_status_forgot_to_mark(self):
        '''
            Проверка создания логов привычки, которые не были созданы пользователем в промежутке хотя бы в два дня между последним логом и текущей датой.
            И также присваивает им статус - forgot_to_mark
        '''
        days_before = 4
        habit = Habit.objects.all().first()
        url = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': HABIT_LOG_STATUS_INCOMPLITED})
        create_habit_log(habit, 'New log )', HABIT_LOG_STATUS_INCOMPLITED, days_before) 
        habit_logs_before_resp = HabitLog.objects.filter(habit=habit).count()

        self.client.login(username=self.username1, password=self.password1)
        data = {
            'comment': 'Log for today',
        }
        self.client.post(url, data)
        habit_logs_after_resp = HabitLog.objects.filter(habit=habit).count()
        self.assertNotEqual(habit_logs_before_resp, habit_logs_after_resp)
        self.assertEqual(habit_logs_before_resp+days_before, habit_logs_after_resp)
        self.assertTrue(HabitLog.objects.filter(status='forgot_to_mark').exists())
        self.assertEqual(HabitLog.objects.filter(status='forgot_to_mark').count(), days_before-1)

    def test_increase_streak_for_habit_datetype_daily_with_no_logs_added_before(self):
        '''Проверка увеличения поля streak при создания лога у ежедневной привычки, у которой до этого не было логов. При этом статус созданного лога - complited'''
        habit = Habit.objects.get(datetype='daily')
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': HABIT_LOG_STATUS_COMPLITED})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        streak_status_from_response_status_complited = Habit.objects.get(datetype='daily').streak

        self.assertEqual(streak_status_from_response_status_complited, 1)

    def test_increase_streak_for_habit_datetype_daily_with_logs_added_before(self):
        '''Проверка увеличения поля streak у ежедневной при создания лога у ежедневной привычки, у которой последний лог со статусом complited. При этом статус созданного лога - complited'''
        habit = Habit.objects.get(datetype='daily')
        habit.streak += 1
        habit.save() # так как ниже мы создаём лог со статусом complited, => увеличиваем streak
        create_habit_log(habit, 'NEw log', 'complited', 1)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': HABIT_LOG_STATUS_COMPLITED})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        self.assertEqual(Habit.objects.get(datetype='daily').streak, habit.streak+1) # 2 1+1

    def test_zeroing_out_streak_for_habit_datetype_daily_with_logs_added_before(self):
        '''Проверка обнуление поля streak у ежедневной при создания лога у ежедневной привычки, у которой последний лог со статусом complited. При этом статус созданного лога - incomplited'''
        habit = Habit.objects.get(datetype='daily')
        habit.streak += 1
        habit.save() # так как ниже мы создаём лог со статусом complited, => увеличиваем streak
        create_habit_log(habit, 'New log', 'incomplited', 1)
        url_status_incomplited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': HABIT_LOG_STATUS_INCOMPLITED})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_incomplited, data)
        self.assertEqual(Habit.objects.get(datetype='daily').streak, 0) # streak стал из 1 -> 0

    def test_increase_streak_for_habit_datetype_weekly_when_created_log_is_complited(self):
        '''
            Проверка увеличения поля streak у еженедельной привычки только в том случае, если кол-во логов со статусом complited >= периодичности привычки (frequency).
            При этом созданный лог имеет статус - complited и кол-во созданных логов кратно 7
        '''
        habit = Habit.objects.get(datetype='weekly')
        create_habit_log(habit, 'New log 1', 'complited', 1)
        for _ in range(2, 7):
            create_habit_log(habit, f'New log {_+1} день назад', 'incomplited', _)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': HABIT_LOG_STATUS_COMPLITED})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        self.assertEqual(Habit.objects.get(datetype='weekly').streak, 1)

    def test_increase_streak_for_habit_datetype_weekly_while_created_log_is_incompleted_and_habitlogs_with_status_complited_is_over_frequency(self):
        '''
            Проверка увеличения поля streak у еженедельной привычки, если кол-во логов со статусом complited >= периодичности привычки (frequency).
            При этом созданный лог имеет статус - incomplited и кол-во созданных логов кратно 7
        '''
        habit = Habit.objects.get(datetype='weekly')
        create_habit_log(habit, 'New log 1', 'complited', 1)
        create_habit_log(habit, 'New log 2', 'complited', 2)

        for _ in range(3, 7):
            create_habit_log(habit, f'New log {_+1} день назад', 'incomplited', _)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': HABIT_LOG_STATUS_INCOMPLITED})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        self.assertEqual(Habit.objects.get(datetype='weekly').streak, 1)

    def test_no_increase_streak_for_habit_datetype_weekly_when_created_log_is_complited_but_habitlogs_not_multiple_of_7(self):
        '''
            Проверка НЕ увеличения поля streak у еженедельной привычки, если кол-во логов со статусом complited >= периодичности привычки (frequency). 
            При этом созданный лог имеет статус - complited и кол-во созданных логов не кратно 7
        '''
        habit = Habit.objects.get(datetype='weekly')
        create_habit_log(habit, 'New log 1', 'complited', 1)
        for _ in range(2, 7):
            create_habit_log(habit, f'New log {_+1} день назад', 'incomplited', _)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': HABIT_LOG_STATUS_INCOMPLITED})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        self.assertEqual(Habit.objects.get(datetype='weekly').streak, 0)

    def test_no_increase_streak_for_habit_datetype_weekly_when_created_log_is_incomplited(self):
        '''
            Проверка НЕ увеличения поля streak у еженедельной привычки, если кол-во логов со статусом complited < периодичности привычки (frequency).
            При этом созданный лог имеет статус - incomplited и кол-во созданных логов кратно 7
        '''
        habit = Habit.objects.get(datetype='weekly')
        create_habit_log(habit, 'New log 1', 'complited', 1)
        for _ in range(2, 7):
            create_habit_log(habit, f'New log {_+1} день назад', 'incomplited', _)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': HABIT_LOG_STATUS_INCOMPLITED})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        self.assertEqual(Habit.objects.get(datetype='weekly').streak, 0)

    def test_zeroing_out_streak_for_habit_datetype_weekly(self):
        '''
            Проверка обнуления поля streak у еженедельной привычки, если кол-во логов со статусом complited < периодичности привычки (frequency).
            При этом созданный лог имеет статус - incomplited и кол-во созданных логов кратно 7
        '''
        habit = Habit.objects.get(datetype='weekly')
        for _ in range(1, 6):
            create_habit_log(habit, f'New log {_} день назад', 'incomplited', _)
        for _ in range(6, 9):
            create_habit_log(habit, f'New log {_} день назад', 'complited', _)
        for _ in range(9, 14):
            create_habit_log(habit, f'New log {_}', 'incomplited', _)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': HABIT_LOG_STATUS_INCOMPLITED})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)

        self.assertEqual(Habit.objects.get(datetype='weekly').streak, 0)