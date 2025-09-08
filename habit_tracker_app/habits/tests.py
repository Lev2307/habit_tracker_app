from datetime import timedelta

from django.db.models import F
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import Habit, HabitLog

def create_habit(owner, title, datetype, freq=1):
    return Habit.objects.create(user=owner, title=title, habit_datetype=datetype, frequency=freq)

def create_habit_log(habit, comment: str, status, days_before=0):
    instance = HabitLog(habit=habit, comment=comment, status=status, date=timezone.now() + timedelta(days=-days_before))
    instance.save()
    return instance

class HabitViewTest(TestCase):
    def setUp(self):
        self.habit_log_status_incomplited = 'incomplited'
        self.habit_log_status_complited = 'complited'
        self.username1 = 'admin1'
        self.password1 = 'password123'
        self.user1 = User.objects.create_user(username=self.username1, password=self.password1)
        self.habit_weekly = create_habit(self.user1, 'New habit', 'week', 2)
        self.habit_everyday = create_habit(self.user1, 'Habit every day', 'every_day')

        self.username2 = 'admin2'
        self.password2 = 'password1234'
        self.user2 = User.objects.create_user(username=self.username2, password=self.password2)

    def test_habits_list_is_login_required(self):
        '''Проверка, что только залогиненный пользователь может посетить страницу со списком привычек.'''
        response_anonymous = self.client.get(reverse('habits:habits_list'))

        self.client.login(username=self.username1, password=self.password1)
        loggined_user_response = self.client.get(reverse('habits:habits_list'))

        self.assertEqual(response_anonymous.status_code, 302)
        self.assertEqual(loggined_user_response.status_code, 200)

    def test_habitslist_display_created_user_habits(self):
        '''Проверка, что пользователь видит список со своими созданными привычками.'''
        self.client.login(username=self.username1, password=self.password1)
        response = self.client.get(reverse('habits:habits_list'))

        self.assertQuerySetEqual(response.context['habits'], [Habit.objects.get(habit_datetype='every_day'), Habit.objects.get(habit_datetype='week')])

    def test_habitslist_dont_display_other_user_habits(self):
        '''Проверка, что пользователь не может видеть привычки других пользователей, а только свои.'''
        self.client.login(username=self.username2, password=self.password2)
        response = self.client.get(reverse('habits:habits_list'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['habits'], [])
        self.assertContains(response, 'У вас пока что нет привычек.')
    
    def test_habit_create_page_is_login_required(self):
        '''Проверка, что только залогиненный пользователь может зайти на страницу создания привычки'''
        response_unloggined = self.client.get(reverse('habits:create_habit'))

        self.client.login(username=self.username1, password=self.password1)
        loggined_user_response = self.client.get(reverse('habits:create_habit'))

        self.assertEqual(response_unloggined.status_code, 302)
        self.assertEqual(loggined_user_response.status_code, 200)

    def test_create_habit_weekly_correct_data(self):
        '''Проверка создания недельной привычки c правильными данными'''
        self.client.login(username=self.username1, password=self.password1)
        habit_queryset_before_creating = Habit.objects.all()
        correct_data = {
            'title': 'Change mindset',
            'purpose': 'To become better',
            'habit_datetype': 'week',
            'frequency': 3
        }
        response_correct_data = self.client.post(reverse('habits:create_habit'), data=correct_data)
        habit_queryset_after_creating = Habit.objects.all()

        self.assertEqual(response_correct_data.status_code, 302)
        self.assertQuerySetEqual(habit_queryset_before_creating, habit_queryset_after_creating)
        self.assertTrue(Habit.objects.filter(title='Change mindset').exists())

    def test_create_habit_weekly_wrong_data(self):
        '''Проверка создания недельной привычки c неправильными данными'''

        self.client.login(username=self.username1, password=self.password1)
        # кол-во повторений < 1 
        wrong_data_1 = {
            'title': 'Change mindset wrong 1',
            'purpose': 'To become better',
            'habit_datetype': 'week',
            'frequency': 0
        }
        wrong_data_2 = {
            'title': 'Change mindset wrong 2',
            'purpose': 'To become better',
            'habit_datetype': 'week',
            'frequency': 14
        }
        response_wrong_data1 = self.client.post(reverse('habits:create_habit'), data=wrong_data_1)
        response_wrong_data2 = self.client.post(reverse('habits:create_habit'), data=wrong_data_2)

        self.assertEqual(response_wrong_data1.status_code, 200)
        self.assertEqual(Habit.objects.filter(title=wrong_data_1['title']).exists(), False)

        self.assertEqual(response_wrong_data2.status_code, 200)
        self.assertEqual(Habit.objects.filter(title=wrong_data_2['title']).exists(), False)

    def test_create_habit_every_day_correct_data(self):
        '''Проверка создания ежедневной привычки c правильными данными'''
        self.client.login(username=self.username1, password=self.password1)
        correct_data = { # значение frequency равное 1
            'title': 'Change mindset every day',
            'purpose': 'To become better',
            'habit_datetype': 'every_day',
            'frequency': 1
        }
        resp = self.client.post(reverse('habits:create_habit'), correct_data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Habit.objects.filter(title=correct_data['title']).exists())

    def test_create_habit_every_day_wrong_data(self):
        '''Проверка создания ежедневной привычки c неправильными данными'''
        self.client.login(username=self.username1, password=self.password1)
        wrong_data = { # любое другое значение frequency отличное от 1
            'title': 'Change mindset every day wrong',
            'purpose': 'To become better',
            'habit_datetype': 'every_day',
            'frequency': 3
        }
        resp = self.client.post(reverse('habits:create_habit'), wrong_data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Habit.objects.filter(title=wrong_data['title']).exists())
        self.assertContains(resp, 'Если вы выбрали выполнять привычку каждый день, поле периодичности должно быть равным 1')

    def test_habit_detail_page_is_login_required(self):
        '''Проверка, что только залогиненный пользователь может зайти на страницу с детальной информацией о привычке'''
        habit = Habit.objects.all().first()
        response_unloggined = self.client.get(reverse('habits:detail_habit', args=(habit.id,)))
        
        self.client.login(username=self.username1, password=self.password1)
        response = self.client.get(reverse('habits:detail_habit', args=(habit.id,)))

        self.assertEqual(response_unloggined.status_code, 302)
        self.assertEqual(response.status_code, 200)

    def test_only_owner_of_habit_can_access_detail_page(self):
        '''Проверка, что только создатель привычки может посетить страницу с её детальной информацией'''
        habit = Habit.objects.all().first()
        
        self.client.login(username=self.username2, password=self.password2) # другой пользователь
        response_non_owner = self.client.get(reverse('habits:detail_habit', args=(habit.id, )))

        self.client.logout()

        self.client.login(username=self.username1, password=self.password1) # создатель привычки
        response_owner = self.client.get(reverse('habits:detail_habit', args=(habit.id, )))

        self.assertEqual(response_non_owner.status_code, 302)
        self.assertEqual(response_non_owner.url, reverse('habits:habits_list'))
        self.assertEqual(response_owner.status_code, 200)
        self.assertQuerySetEqual(response_owner.context['habitLogs'], [])

    def test_add_log_to_habit_is_login_required(self):
        '''Проверка, что только залогиненный пользователь может посетить страницу создания лога'''
        habit = Habit.objects.all().first()

        response_unloggined = self.client.get(reverse('habits:set_habit_status_for_today', args=(habit.id, )))

        self.client.login(username=self.username1, password=self.password1)
        response_loggined = self.client.get(reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': 'complited'}))

        self.assertEqual(response_unloggined.status_code, 302)
        self.assertEqual(response_loggined.status_code, 200)

    def test_add_log_to_habit_url_query_is_only_complited_or_incomplited(self):
        '''
            Проверка, что query keyword argument будет или complited, или incomplited, т.е. валидными url являются:
            (.../habit_log_status?=complited, .../habit_log_status?=incomplited)
        '''
        habit = Habit.objects.all().first()
        self.client.login(username=self.username1, password=self.password1)
        response_habit_log_complited = self.client.get(reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': 'complited'}))
        response_habit_log_status_incomplited = self.client.get(reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': 'incomplited'}))
        response_habit_log_no_status = self.client.get(reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': ''}))
        response_habit_log_other_status = self.client.get(reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': 'half_complited'}))

        self.assertEqual(response_habit_log_complited.status_code, 200)
        self.assertContains(response_habit_log_complited, 'Поздравляю! Вы сегодня смогли выполнить свою привычку')
        self.assertEqual(response_habit_log_status_incomplited.status_code, 200)
        self.assertContains(response_habit_log_status_incomplited, 'Почему вам не удалось выполнить привычку?')

        self.assertEqual(response_habit_log_no_status.status_code, 302)
        self.assertEqual(response_habit_log_no_status.url, reverse('habits:habits_list'))
        self.assertEqual(response_habit_log_other_status.status_code, 302)
        self.assertEqual(response_habit_log_other_status.url, reverse('habits:habits_list'))

    def test_only_owner_of_habit_can_access_add_log_to_habit(self):
        '''Проверка, что только создатель привычки может взаимодействовать со страницей создания лога привычки (GET, POST соответственно)'''
        habit = Habit.objects.all().first()
        url = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': self.habit_log_status_incomplited})
        
        self.client.login(username=self.username2, password=self.password2) # другой пользователь
        response_non_owner_get = self.client.get(url)

        before_creating_habitlogs_queryset = HabitLog.objects.filter(habit=habit)
        non_owner_data = {
            'comment': 'Non owner comment',
        }
        response_non_owner_post = self.client.post(url, non_owner_data)
        after_creating_habitlogs_queryset = HabitLog.objects.filter(habit=habit)

        self.assertEqual(response_non_owner_get.status_code, 302)
        self.assertEqual(response_non_owner_get.url, reverse('habits:habits_list'))
        self.assertEqual(response_non_owner_post.status_code, 302)
        self.assertQuerySetEqual(before_creating_habitlogs_queryset, after_creating_habitlogs_queryset)

        self.client.logout()

        self.client.login(username=self.username1, password=self.password1) # создатель привычки
        response_owner_get = self.client.get(url)

        owner_data = {
            'comment': 'Owner comment',
        }
        response_owner_post = self.client.post(url, owner_data)
        after_creating_habitlogs_queryset = HabitLog.objects.filter(habit=habit)

        self.assertEqual(response_owner_get.status_code, 200)
        self.assertEqual(response_owner_post.status_code, 302)
        self.assertNotEqual(before_creating_habitlogs_queryset, after_creating_habitlogs_queryset)

    def test_creation_habitlogs_with_status_forgot_to_mark(self):
        '''
            Проверка создания логов привычки, которые не были созданы пользователем в промежутке хотя бы в два дня между последним логом и текущей датой.
            И также присваивает им статус - forgot_to_mark
        '''
        days_before = 4
        habit = Habit.objects.all().first()
        url = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': self.habit_log_status_incomplited})
        create_habit_log(habit, 'New log )', self.habit_log_status_incomplited, days_before) 
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

    def test_creating_habit_log_to_the_same_date_as_previous_not_allowed(self):
        '''Проверка, что нельзя создать лог о привычке, дата которого совпадает с датой последнего созданного лога'''
        habit = Habit.objects.all().first()
        url = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': self.habit_log_status_incomplited})
        create_habit_log(habit, 'New log', self.habit_log_status_incomplited)
        habit_logs_prev = HabitLog.objects.filter(habit=habit)

        self.client.login(username=self.username1, password=self.password1)
        data = {
            'comment': 'New log',
        }
        response = self.client.post(url, data)
        habit_logs_after_rep = HabitLog.objects.filter(habit=habit)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Нельзя создать отчёт о привычке в дату, в которую был создан последний отчёт')
        self.assertQuerySetEqual(habit_logs_prev, habit_logs_after_rep)

    def test_increase_streak_for_habit_datetype_every_day_with_no_logs_added_before(self):
        '''Проверка увеличения поля streak при создания лога у ежедневной привычки, у которой до этого не было логов. При этом статус созданного лога - complited'''
        habit = Habit.objects.get(habit_datetype='every_day')
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': self.habit_log_status_complited})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        streak_status_from_response_status_complited = Habit.objects.get(habit_datetype='every_day').streak

        self.assertEqual(streak_status_from_response_status_complited, 1)

    def test_increase_streak_for_habit_datetype_every_day_with_logs_added_before(self):
        '''Проверка увеличения поля streak у ежедневной при создания лога у ежедневной привычки, у которой последний лог со статусом complited. При этом статус созданного лога - complited'''
        habit = Habit.objects.get(habit_datetype='every_day')
        habit.streak += 1
        habit.save() # так как ниже мы создаём лог со статусом complited, => увеличиваем streak
        create_habit_log(habit, 'NEw log', 'complited', 1)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': self.habit_log_status_complited})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        self.assertEqual(Habit.objects.get(habit_datetype='every_day').streak, habit.streak+1) # 2 1+1

    def test_zeroing_out_streak_for_habit_datetype_every_day_with_logs_added_before(self):
        '''Проверка обнуление поля streak у ежедневной при создания лога у ежедневной привычки, у которой последний лог со статусом complited. При этом статус созданного лога - incomplited'''
        habit = Habit.objects.get(habit_datetype='every_day')
        habit.streak += 1
        habit.save() # так как ниже мы создаём лог со статусом complited, => увеличиваем streak
        create_habit_log(habit, 'New log', 'incomplited', 1)
        url_status_incomplited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': self.habit_log_status_incomplited})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_incomplited, data)
        self.assertEqual(Habit.objects.get(habit_datetype='every_day').streak, 0) # streak стал из 1 -> 0

    def test_increase_streak_for_habit_datetype_when_created_log_is_complited(self):
        '''
            Проверка увеличения поля streak у еженедельной привычки только в том случае, если кол-во логов со статусом complited >= периодичности привычки (frequency).
            При этом созданный лог имеет статус - complited и кол-во созданных логов кратно 7
        '''
        habit = Habit.objects.get(habit_datetype='week')
        create_habit_log(habit, 'New log 1', 'complited', 1)
        for _ in range(2, 7):
            create_habit_log(habit, f'New log {_+1} день назад', 'incomplited', _)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': self.habit_log_status_complited})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        self.assertEqual(Habit.objects.get(habit_datetype='week').streak, 1)

    def test_increase_streak_for_habit_datetype_while_created_log_is_incompleted_and_habitlogs_with_status_complited_is_over_frequency(self):
        '''
            Проверка увеличения поля streak у еженедельной привычки, если кол-во логов со статусом complited >= периодичности привычки (frequency).
            При этом созданный лог имеет статус - incomplited и кол-во созданных логов кратно 7
        '''
        habit = Habit.objects.get(habit_datetype='week')
        create_habit_log(habit, 'New log 1', 'complited', 1)
        create_habit_log(habit, 'New log 2', 'complited', 2)

        for _ in range(3, 7):
            create_habit_log(habit, f'New log {_+1} день назад', 'incomplited', _)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': self.habit_log_status_incomplited})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        self.assertEqual(Habit.objects.get(habit_datetype='week').streak, 1)

    def test_no_increase_streak_for_habit_datetype_when_created_log_is_complited_but_habitlogs_not_multiple_of_7(self):
        '''
            Проверка НЕ увеличения поля streak у еженедельной привычки, если кол-во логов со статусом complited >= периодичности привычки (frequency). 
            При этом созданный лог имеет статус - complited и кол-во созданных логов не кратно 7
        '''
        habit = Habit.objects.get(habit_datetype='week')
        create_habit_log(habit, 'New log 1', 'complited', 1)
        for _ in range(2, 7):
            create_habit_log(habit, f'New log {_+1} день назад', 'incomplited', _)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': self.habit_log_status_incomplited})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        self.assertEqual(Habit.objects.get(habit_datetype='week').streak, 0)

    def test_no_increase_streak_for_habit_datetype_when_created_log_is_incomplited(self):
        '''
            Проверка НЕ увеличения поля streak у еженедельной привычки, если кол-во логов со статусом complited < периодичности привычки (frequency).
            При этом созданный лог имеет статус - incomplited и кол-во созданных логов кратно 7
        '''
        habit = Habit.objects.get(habit_datetype='week')
        create_habit_log(habit, 'New log 1', 'complited', 1)
        for _ in range(2, 7):
            create_habit_log(habit, f'New log {_+1} день назад', 'incomplited', _)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': self.habit_log_status_incomplited})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)
        self.assertEqual(Habit.objects.get(habit_datetype='week').streak, 0)

    def test_zeroing_out_streak_for_habit_datetype(self):
        '''
            Проверка обнуления поля streak у еженедельной привычки, если кол-во логов со статусом complited < периодичности привычки (frequency).
            При этом созданный лог имеет статус - incomplited и кол-во созданных логов кратно 7
        '''
        habit = Habit.objects.get(habit_datetype='week')
        for _ in range(1, 6):
            create_habit_log(habit, f'New log {_} день назад', 'incomplited', _)
        for _ in range(6, 9):
            create_habit_log(habit, f'New log {_} день назад', 'complited', _)
        for _ in range(9, 14):
            create_habit_log(habit, f'New log {_}', 'incomplited', _)
        url_status_complited = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': self.habit_log_status_incomplited})
        data = {
            'comment': 'Log for today',
        }
        self.client.login(username=self.username1, password=self.password1)

        self.client.post(url_status_complited, data)

        self.assertEqual(Habit.objects.get(habit_datetype='week').streak, 0)