from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import Habit, HabitLog

User = get_user_model()

def create_user(username: str, password: str):
    user = User.objects.create_user(username=username, password=password)
    return user

def create_habit(owner, title: str, purpose: str, datetype: str, freq=1):
    habit = Habit.objects.create(
        user=owner, 
        title=title, 
        purpose=purpose, 
        datetype=datetype, 
        frequency=freq
    )
    return habit

def create_habit_log(habit, comment: str, status: bool, days_before=0):
    instance = HabitLog.objects.create(
        habit=habit, 
        comment=comment, 
        status=status, 
        date=timezone.localtime(timezone.now()) + timedelta(days=-days_before)
    )
    return instance

def generate_habit_input_data(title: str, datetype: str, frequency=1, purpose=''):
    return {
        'title': title,
        'purpose': purpose,
        'datetype': datetype,
        'frequency': frequency
    }

def generate_habit_log_data(comment: str, status: bool):
    return {
        'comment': comment,
        'status': status
    }