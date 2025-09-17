from django.test import TestCase
from django.urls import reverse

from .factories import create_user, create_habit, create_habit_log
from ..models import Habit, HabitLog, HABIT_LOG_STATUS_INCOMPLITED

class HabitViewTests(TestCase):
    def setUp(self):
        self.username1 = 'admin_views'
        self.password1 = 'password123_views'
        self.username2 = 'admin2_views'
        self.password2 = 'password123_views'

        self.user1 = create_user(self.username1, self.password1)
        self.user2 = create_user(self.username2, self.password2)
        self.habit_weekly = create_habit(self.user1, 'New habit test_views', 'habit views purpose', 'weekly', 2)
        self.habit_daily = create_habit(self.user1, 'Habit every day test_views', 'habit views purpose', 'daily')

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

        self.assertQuerySetEqual(response.context['habits'], [Habit.objects.get(datetype='daily'), Habit.objects.get(datetype='weekly')])

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
            'datetype': 'weekly',
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
            'datetype': 'weekly',
            'frequency': 0
        }
        wrong_data_2 = {
            'title': 'Change mindset wrong 2',
            'purpose': 'To become better',
            'datetype': 'weekly',
            'frequency': 14
        }
        response_wrong_data1 = self.client.post(reverse('habits:create_habit'), data=wrong_data_1)
        response_wrong_data2 = self.client.post(reverse('habits:create_habit'), data=wrong_data_2)

        self.assertEqual(response_wrong_data1.status_code, 200)
        self.assertEqual(Habit.objects.filter(title=wrong_data_1['title']).exists(), False)

        self.assertEqual(response_wrong_data2.status_code, 200)
        self.assertEqual(Habit.objects.filter(title=wrong_data_2['title']).exists(), False)

    def test_create_habit_daily_correct_data(self):
        '''Проверка создания ежедневной привычки c правильными данными'''
        self.client.login(username=self.username1, password=self.password1)
        correct_data = { # значение frequency равное 1
            'title': 'Change mindset every day',
            'purpose': 'To become better',
            'datetype': 'daily',
            'frequency': 1
        }
        resp = self.client.post(reverse('habits:create_habit'), correct_data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Habit.objects.filter(title=correct_data['title']).exists())

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
        url = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': HABIT_LOG_STATUS_INCOMPLITED})
        
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

    def test_habit_delete_page_is_login_required(self):
        '''Проверка, что только залогиненный пользователь может зайти на страницу удаления привычки'''
        habit = Habit.objects.get(datetype='daily')
        response_unloggined = self.client.get(reverse('habits:delete_habit', args=(habit.id, )))

        self.client.login(username=self.username1, password=self.password1)
        loggined_user_response = self.client.get(reverse('habits:delete_habit', args=(habit.id, )))

        self.assertEqual(response_unloggined.status_code, 302)
        self.assertEqual(loggined_user_response.status_code, 200)

    def test_other_user_access_to_delete_habit(self):
        '''Проверка, что другой пользователь не может удалить чужую привычку'''
        habit = Habit.objects.get(datetype='daily')
        self.client.login(username=self.username2, password=self.password2)
        response = self.client.delete(reverse('habits:delete_habit', args=(habit.id, )))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Habit.objects.filter(datetype='daily').count(), 1)
    
    def test_delete_habit(self):
        '''Проверка удаления привычки'''
        habit = Habit.objects.get(datetype='daily')

        self.client.login(username=self.username1, password=self.password1)
        response = self.client.delete(reverse('habits:delete_habit', args=(habit.id, )))
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Habit.objects.filter(datetype='daily').count(), 0)
    
    def test_habit_update_page_is_login_required(self):
        '''Проверка, что только залогиненный пользователь может зайти на страницу редактирования привычки'''
        habit = Habit.objects.get(datetype='daily')
        response_unloggined = self.client.get(reverse('habits:update_habit', args=(habit.id, )))

        self.client.login(username=self.username1, password=self.password1)
        loggined_user_response = self.client.get(reverse('habits:update_habit', args=(habit.id, )))

        self.assertEqual(response_unloggined.status_code, 302)
        self.assertEqual(loggined_user_response.status_code, 200)

    def test_other_user_access_to_update_habit(self):
        '''Проверка, что другой пользователь не может редактировать чужую привычку'''
        habit = Habit.objects.get(datetype='daily')
        data = {
            'title': habit.title + 'Edited',
            'purpose': habit.purpose + 'Edited',
            'datetype': habit.datetype,
            'frequency': habit.frequency
        }
        self.client.login(username=self.username2, password=self.password2)
        response = self.client.post(reverse('habits:update_habit', args=(habit.id, )), data=data)

        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(Habit.objects.get(datetype='daily').title, data['title'])

    def test_update_habit_with_changed_freq(self):
        '''Проверка обновления привычки, у которой изменено поле периодичности'''
        habit = Habit.objects.get(datetype='weekly')
        create_habit_log(habit, 'New log', HABIT_LOG_STATUS_INCOMPLITED)
        data = {
            'title': habit.title,
            'purpose': habit.purpose,
            'datetype': habit.datetype,
            'frequency': 4
        }
        self.client.login(username=self.username1, password=self.password1)

        response = self.client.post(reverse('habits:update_habit', args=(habit.id, )), data=data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Habit.objects.get(datetype='weekly').frequency, data['frequency'])
        self.assertEqual(HabitLog.objects.filter(habit=habit).count(), 0) # логи удалились

    def test_update_habit_with_changed_datetype(self):
        '''Проверка обновления привычки, у которой изменено поле типа даты'''
        habit = Habit.objects.get(datetype='weekly')
        create_habit_log(habit, 'New log', HABIT_LOG_STATUS_INCOMPLITED)
        data = {
            'title': habit.title,
            'purpose': habit.purpose,
            'datetype': 'daily',
            'frequency': 1,
        }
        self.client.login(username=self.username1, password=self.password1)

        response = self.client.post(reverse('habits:update_habit', args=(habit.id, )), data=data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Habit.objects.get(title=habit).frequency, 1)
        self.assertEqual(Habit.objects.get(title=habit).datetype, data['datetype'])
        self.assertEqual(HabitLog.objects.filter(habit=habit).count(), 0) # логи удалились

    def test_update_habit_with_changed_title_or_purpose(self):
        '''Проверка обновления привычки, у которой изменено название или цель'''
        habit = Habit.objects.get(datetype='weekly')
        create_habit_log(habit, 'New log', HABIT_LOG_STATUS_INCOMPLITED)
        data = {
            'title': habit.title + ' edited',
            'purpose': habit.purpose + ' edited',
            'datetype': habit.datetype,
            'frequency' : habit.frequency
        }
        self.client.login(username=self.username1, password=self.password1)

        response = self.client.post(reverse('habits:update_habit', args=(habit.id, )), data=data)
        edited_habit = Habit.objects.get(datetype='weekly')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(edited_habit.title, data['title'])
        self.assertEqual(edited_habit.purpose, data['purpose'])
        self.assertEqual(HabitLog.objects.filter(habit=habit).count(), 1) # логи не удалились