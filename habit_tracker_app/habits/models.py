from django.db import models

# Create your models here.
HABIT_DATETYPES = [
    ('every_day', 'Every day'),
    ('week', 'Week')
]
class Habit(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    habit_datetype = models.CharField(choices=HABIT_DATETYPES, default='every_day')
    purpose = models.CharField(max_length=150, blank=True)
    streak = models.IntegerField(default=0)
    creation_date = models.DateTimeField(auto_now_add=True)
    frequency = models.PositiveBigIntegerField(default=1)

    class Meta:
        ordering = ['-creation_date']

class HabitLog(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)
    comment = models.CharField(max_length=100)

