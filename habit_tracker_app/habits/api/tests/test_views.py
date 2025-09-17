from django.urls import reverse

from rest_framework.test import APITestCase, APIClient
from rest_framework import status


from ...models import Habit, HabitLog
from ...tests.factories import generate_habit_input_data, create_user, create_habit, create_habit_log


class HabitViewsApiTests(APITestCase):
    def setUp(self):
        self.username1 = 'admin_api_views'
        self.password1 = 'api_views1234'
        self.username2 = 'admin2_api_views'
        self.password2 = 'api_views1234_2'

        self.user1 = create_user(self.username1, self.password1)
        self.user2 = create_user(self.username2, self.password2)
        self.client = APIClient()

        self.habit_daily = create_habit(self.user1, 'api habit every day', 'api habit purpose', 'daily')
        self.habit_weekly = create_habit(self.user1, 'api habit weekly', 'api habit purp', 'weekly', 3)

    def test_api_habit_list_is_login_required(self):
        '''Проверка, что список привычек может получить только залогиненный пользователь (GET)'''
        anonymous_response = self.client.get(reverse('api:habit-list'), format='json')
        self.assertEqual(anonymous_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_habit_list_only_owner_access(self):
        '''Проверка, что пользователь не может получить список привычек другого пользователя (GET)'''
        self.client.login(username=self.username1, password=self.password1) # создатель привычек
        owner_response = self.client.get(reverse('api:habit-list'))
        self.client.logout()

        self.client.login(username=self.username2, password=self.password2)
        other_user_response = self.client.get(reverse('api:habit-list'))

        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(owner_response.data), 2)

        self.assertEqual(other_user_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(other_user_response.data), 0)

    def test_api_habit_create_is_login_required(self):
        '''Проверка, что создать привычку может только залогиненный пользователь (POST)'''
        data = generate_habit_input_data('New habit', 'daily')
        anonymous_response = self.client.post(reverse('api:habit-list'), data=data)
        self.assertEqual(anonymous_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_create_daily_habit(self):
        '''Проверка создания ежедневной привычки с различными входными данными (POST)'''
        correct_data = generate_habit_input_data('New habit daily', 'daily')
        wrong_data = generate_habit_input_data('New habit daily wrong', 'daily', 4)

        self.client.login(username=self.username1, password=self.password1)
        correct_data_response = self.client.post(reverse('api:habit-list'), data=correct_data)
        wrong_data_response = self.client.post(reverse('api:habit-list'), data=wrong_data)

        self.assertEqual(correct_data_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Habit.objects.filter(title=correct_data['title']).exists(), True)

        self.assertEqual(wrong_data_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(wrong_data_response.data['frequency'][0]), 'If you have chosen to perform a habit every day, the frequency field should be equal to 1.')
        self.assertEqual(Habit.objects.filter(title=wrong_data['title']).exists(), False)

    def test_api_create_weekly_habit(self):
        '''Проверка создания еженедельной привычки с различными входными данными (POST)'''
        correct_data = generate_habit_input_data('New habit weekly', 'weekly', 2)
        wrong_data = generate_habit_input_data('New habit weekly wrong', 'weekly', 0)

        self.client.login(username=self.username1, password=self.password1)
        correct_data_response = self.client.post(reverse('api:habit-list'), data=correct_data)
        wrong_data_response = self.client.post(reverse('api:habit-list'), data=wrong_data)

        self.assertEqual(correct_data_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Habit.objects.filter(title=correct_data['title']).exists(), True)

        self.assertEqual(wrong_data_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(wrong_data_response.data['frequency'][0]), f'"{wrong_data['frequency']}" is not a valid choice.')
        self.assertEqual(Habit.objects.filter(title=wrong_data['title']).exists(), False)

    def test_api_habit_detail_is_login_required(self):
        '''Проверка, что детальную информацию о привычке может получить только залогиненный пользователь (GET)'''
        habit = Habit.objects.get(datetype='daily')
        anonymous_response = self.client.get(reverse('api:habit-detail', args={habit.id, }))
        self.assertEqual(anonymous_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_habit_detail_only_owner_access(self):
        '''Проверка, что детальную информацию о привычке может получить только создатель привычки (GET)'''
        habit = Habit.objects.get(datetype='daily')

        self.client.login(username=self.username1, password=self.password1)
        owner_response = self.client.get(reverse('api:habit-detail', args=(habit.id, )))
        self.client.logout()

        self.client.login(username=self.username2, password=self.password2)
        other_user_response = self.client.get(reverse('api:habit-detail', args=(habit.id, )))

        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertEqual(owner_response.data['title'], habit.title)
        self.assertEqual(owner_response.data['purpose'], habit.purpose)
        self.assertEqual(owner_response.data['datetype'], habit.datetype)
        self.assertEqual(owner_response.data['frequency'], habit.frequency)
        self.assertEqual(owner_response.data['streak'], habit.streak)

        self.assertEqual(other_user_response.status_code, status.HTTP_404_NOT_FOUND)
