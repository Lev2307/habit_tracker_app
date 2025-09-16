from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .factories import create_user, create_habit, create_habit_log
from ..models import Habit, HabitLog, HABIT_LOG_STATUS_INCOMPLITED

User = get_user_model()

class HabitFormTest(TestCase):
    def setUp(self):
        self.username1 = 'admin1_forms'
        self.password1 = 'password123_forms'
        
        self.user = create_user(self.username1, self.password1)
        self.habit_weekly = create_habit(self.user, 'Habit weekly test habit_forms ', 'habit form purpose', 'week', 2)
        self.habit_everyday = create_habit(self.user, 'Habit every day  test habit_forms', 'habit form purpose', 'every_day')

    def test_creating_habit_log_to_the_same_date_as_previous_not_allowed(self):
        '''Проверка, что нельзя создать лог о привычке, дата которого совпадает с датой последнего созданного лога'''
        habit = Habit.objects.all().first()
        url = reverse('habits:set_habit_status_for_today', args=(habit.id, ), query={'status': HABIT_LOG_STATUS_INCOMPLITED})
        create_habit_log(habit, 'New log', HABIT_LOG_STATUS_INCOMPLITED)
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

    def test_validation_of_creating_habit(self):
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