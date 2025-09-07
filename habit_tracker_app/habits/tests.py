from django.test import TestCase
from django.contrib.auth.models import User

from django.urls import reverse

from .models import Habit

def create_habit(owner, title, datetype, freq=1):
    return Habit.objects.create(user=owner, title=title, habit_datetype=datetype, frequency=freq)

class HabitViewTest(TestCase):

    def setUp(self):
        self.username1 = 'admin1'
        self.password1 = 'password123'
        self.user1 = User.objects.create_user(username=self.username1, password=self.password1)
        self.habit_user1 = create_habit(self.user1, 'New habit', 'week')

        self.username2 = 'admin2'
        self.password2 = 'password1234'
        self.user2 = User.objects.create_user(username=self.username2, password=self.password2)

    def test_habits_list_is_login_required(self):
        '''Проверка, что только авторизованный пользователь может посетить страницу со списком привычек.'''

        response_anonymous = self.client.get(reverse('habits:habits_list'))
        self.assertEqual(response_anonymous.status_code, 302)

        self.client.login(username=self.username1, password=self.password1)
        loggined_user_response = self.client.get(reverse('habits:habits_list'))
        self.assertEqual(loggined_user_response.status_code, 200)

    def test_habitslist_display_created_user_habits(self):
        '''Проверка, что пользователь видит список со своими созданными привычками.'''

        self.client.login(username=self.username1, password=self.password1)
        response = self.client.get(reverse('habits:habits_list'))
        self.assertQuerySetEqual(response.context['habits'], [self.habit_user1])

    def test_habitslist_dont_display_other_user_habits(self):
        '''Проверка, что пользователь не может видеть привычки других пользователей, а только свои.'''

        self.client.login(username=self.username2, password=self.password2)
        response = self.client.get(reverse('habits:habits_list'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['habits'], [])
        self.assertContains(response, 'У вас пока что нет привычек.')
    
    def test_habit_create_page_is_login_required(self):
        '''Проверка, что только авторизованный пользователь может зайти на страницу создания привычки'''
        
        response = self.client.get(reverse('habits:create_habit'))
        self.assertEqual(response.status_code, 302)

        self.client.login(username=self.username1, password=self.password1)
        loggined_user_response = self.client.get(reverse('habits:create_habit'))
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
        self.assertTrue(Habit.objects.filter(title='Change mindset').exists(), True)

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
    
    def test_habit_detail_page_is_login_required(self):
        '''Проверка, что только авторизованный пользователь может зайти на страницу с детальной информацией о привычке'''
        habit = Habit.objects.all().first()
        response = self.client.get(reverse('habits:detail_habit', args=(habit.id,)))
        self.assertEqual(response.status_code, 302)

        self.client.login(username=self.username1, password=self.password1)
        response = self.client.get(reverse('habits:detail_habit', args=(habit.id,)))
        self.assertEqual(response.status_code, 200)
