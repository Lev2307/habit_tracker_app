from django.db import models
from django.utils import timezone
# Create your models here.

HABIT_LOG_STATUS_INCOMPLITED = 'incomplited'
HABIT_LOG_STATUS_COMPLITED = 'complited'

HABIT_DATETYPES = [
    ('week', 'Кол-во раз в неделю'),
    ('every_day', 'Каждый день')
]
HABIT_LOG_STATUS = [
    ('complited', 'Выполнено'),
    (HABIT_LOG_STATUS_INCOMPLITED, 'Не выполнено'),
    (HABIT_LOG_STATUS_COMPLITED, 'Забыли записать!')
]
class Habit(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title = models.CharField('Название', max_length=100)
    purpose = models.CharField('Цель', max_length=150, blank=True)
    habit_datetype = models.CharField('Как вы хотите выполнять привычку?', choices=HABIT_DATETYPES, default='week')
    streak = models.IntegerField(default=0)
    creation_date = models.DateTimeField(auto_now_add=True)
    frequency = models.PositiveSmallIntegerField(
        'Сколько раз в неделю вы хотите выполнять привычку', 
        default=1, 
        choices=((i,i) for i in range(1, 8))
    )

    class Meta:
        ordering = ['-creation_date']

    def __str__(self):
        return self.title


class HabitLog(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    status = models.CharField(choices=HABIT_LOG_STATUS)
    date = models.DateField(default=timezone.now)
    comment = models.CharField(max_length=100)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        if self.comment:
            return f'Лог: `{self.comment}` к привычке `{self.habit}` - {self.status}'
        
    

