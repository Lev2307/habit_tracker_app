from django.urls import path

from . import views

app_name = 'habits'
urlpatterns = [
    path('', views.HabitsList.as_view(), name="habits_list"),
    path('create/', views.CreateHabit.as_view(), name="create_habit"),
    path('<int:pk>/', views.HabitDetail.as_view(), name="detail_habit"),
    path('<int:pk>/update', views.UpdateHabit.as_view(), name="update_habit"),
    path('<int:pk>/delete', views.DeleteHabit.as_view(), name="delete_habit"),
    path('<int:pk>/habit_log_status', views.set_habitLog_status, name="set_habit_status_for_today"),
]