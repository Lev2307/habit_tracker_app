from django.urls import reverse

from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from ...models import Habit, HabitLog, HABIT_LOG_STATUS_COMPLITED, HABIT_LOG_STATUS_INCOMPLITED
from ...tests.factories import generate_habit_input_data, create_user, create_habit, create_habit_log, generate_habit_log_data


class HabitViewsAPITests(APITestCase):
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

    def test_api_update_habit_is_login_required(self):
        '''Проверка, что редактировать привычку может только залогиненный пользователь (PUT)'''
        habit = Habit.objects.get(datetype='daily')
        anonymous_response = self.client.put(reverse('api:habit-detail', args=(habit.id, )), data={})
        self.assertEqual(anonymous_response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_api_update_habit_only_owner_access(self):
        '''Проверка, что доступ к редактированию привычки имеет только создатель привычки (PUT)'''
        habit = Habit.objects.get(datetype='daily')
        data = generate_habit_input_data('Edited title', habit.datetype, habit.frequency, 'Edited purpose')

        self.client.login(username=self.username1, password=self.password1) # owner
        owner_response = self.client.put(reverse('api:habit-detail', args=(habit.id, )), data=data)
        self.client.logout()

        self.client.login(username=self.username2, password=self.password2) # other user
        other_user_response = self.client.put(reverse('api:habit-detail', args=(habit.id, )), data=data)

        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertEqual(other_user_response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_api_update_habit_from_daily_to_weekly(self):
        '''Проверка редактирования привычки с ежедневной на недельную (PUT)'''
        habit = Habit.objects.get(datetype='daily')
        create_habit_log(habit, 'First Log', HABIT_LOG_STATUS_COMPLITED, 2)
        habit.streak = 1
        habit.save()
        weekly_data = generate_habit_input_data('Edited title', 'weekly', 2, 'Edited purpose')
        
        self.client.login(username=self.username1, password=self.password1)
        response = self.client.put(reverse('api:habit-detail', args=(habit.id, )), data=weekly_data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Habit.objects.filter(title=weekly_data['title']).exists())
        self.assertEqual(response.data['habit_logs'], []) # удалился лог из-за смены datetype
        self.assertEqual(response.data["streak"], 0) # сбросился стрик из-за смены datetype

    def test_api_update_habit_from_weekly_to_daily(self):
        '''Проверка редактирования привычки с недельной на ежедневную (PUT)'''
        habit = Habit.objects.get(datetype='weekly')
        create_habit_log(habit, 'First Log', HABIT_LOG_STATUS_COMPLITED, 2)
        daily_data = generate_habit_input_data('Edited title to daily', 'daily', 1, 'Edited purpose to daily')
        
        self.client.login(username=self.username1, password=self.password1)
        response = self.client.put(reverse('api:habit-detail', args=(habit.id, )), data=daily_data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Habit.objects.filter(title=daily_data['title']).exists())
        self.assertEqual(response.data['habit_logs'], []) # удалился лог из-за смены datetype

    def test_api_update_habit_from_weekly_to_daily_wrong_data(self):
        '''Проверка редактирования привычки с недельной на ежедневную c неправильными данными (PUT)'''
        habit = Habit.objects.get(datetype='weekly')
        create_habit_log(habit, 'First Log', HABIT_LOG_STATUS_COMPLITED, 2)
        daily_data_wrong_data = generate_habit_input_data('Edited title to daily', 'daily', 4, 'Edited purpose to daily')
        
        self.client.login(username=self.username1, password=self.password1)
        response = self.client.put(reverse('api:habit-detail', args=(habit.id, )), data=daily_data_wrong_data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data['frequency'][0]), 'If you have chosen to perform a habit every day, the frequency field should be equal to 1.')
        self.assertFalse(Habit.objects.filter(title=daily_data_wrong_data['title']).exists())

    def test_habit_delete_is_login_required(self):
        '''Проверка, что удалять привычку может только залогиненный пользователь (DELETE)'''
        habit = Habit.objects.get(datetype='daily')
        anonymous_response = self.client.delete(reverse('api:habit-detail', args=(habit.id, )))
        self.assertEqual(anonymous_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_delete_habit_only_owner_access(self):
        '''Проверка, что доступ к удалению привычки имеет только создатель привычки (DELETE)'''
        habit = Habit.objects.get(datetype='daily')

        self.client.login(username=self.username1, password=self.password1) # owner
        owner_response = self.client.delete(reverse('api:habit-detail', args=(habit.id, )))
        self.client.logout()

        self.client.login(username=self.username2, password=self.password2) # other user
        other_user_response = self.client.delete(reverse('api:habit-detail', args=(habit.id, )))

        self.assertEqual(owner_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(other_user_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_delete_habit(self):
        '''Проверка удаления привычки (DELETE)'''
        habit = Habit.objects.get(datetype='daily')

        self.client.login(username=self.username1, password=self.password1)
        response = self.client.delete(reverse('api:habit-detail', args=(habit.id, )))
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Habit.objects.filter(datetype='daily').count(), 0)
    
    def test_api_create_habit_log_is_login_required(self):
        '''Проверка, что создавать лог для привычки может только залогиненный пользователь (POST)'''
        habit = Habit.objects.get(datetype="daily")
        anonymous_response = self.client.post(reverse('api:api_create_habit_log', args=(habit.id, ), query={'status': 'complited'}), data={})
        self.assertEqual(anonymous_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_create_habit_log_only_owner_access(self):
        '''Проверка, что только создатель привычки может создавать лог к ней (POST)'''
        habit = Habit.objects.get(datetype="daily")
        owner_data = generate_habit_log_data('owner com', HABIT_LOG_STATUS_COMPLITED)
        other_user_data = generate_habit_log_data('other com', HABIT_LOG_STATUS_COMPLITED)

        self.client.login(username=self.username1, password=self.password1)
        owner_response = self.client.post(reverse('api:api_create_habit_log', args=(habit.id, ), query={'status': owner_data['status']}), data=owner_data) # owner
        self.client.logout()

        self.client.login(username=self.username2, password=self.password2)
        other_user_response = self.client.post(reverse('api:api_create_habit_log', args=(habit.id, ), query={'status': other_user_data['status']}), data=other_user_data) # other user

        self.assertEqual(owner_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(HabitLog.objects.filter(comment=owner_data['comment']).exists())
        self.assertEqual(HabitLog.objects.filter(habit=habit).count(), 1)

        self.assertEqual(other_user_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(other_user_response.data["message"], "You are not allowed to create log for this habit.")

    def test_api_create_habit_log(self):
        '''Проверка создания лога привычки (POST)'''
        self.client.login(username=self.username1, password=self.password1)
        habit = Habit.objects.get(datetype="daily")
        data = generate_habit_log_data('com', HABIT_LOG_STATUS_INCOMPLITED)
        response = self.client.post(reverse('api:api_create_habit_log', args=(habit.id, ), query={'status': data['status']}), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(HabitLog.objects.filter(comment=data['comment']).exists())
        self.assertEqual(HabitLog.objects.filter(habit=habit).count(), 1)
