from django import forms
from django.utils import timezone

from .models import Habit, HabitLog

class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['title', 'purpose', 'datetype', 'frequency']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        datetype = self.cleaned_data.get('datetype')
        frequency = self.cleaned_data.get('frequency')
        if datetype == 'daily' and frequency != 1:
            raise forms.ValidationError('Если вы выбрали выполнять привычку каждый день, поле периодичности должно быть равным 1')
     
    def save(self, commit=True, **kwargs):
        upd = kwargs.pop('upd', None) 
        instance = super().save(commit=False)
        instance.user = self.user

        if upd:
            instance.streak = 0
            
        if commit:
            instance.save()
        return instance
    
class CreateHabitLogForm(forms.ModelForm):
    class Meta:
        model = HabitLog
        fields = ['comment']
    
    def __init__(self, habit, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.habit = habit
        self.habit_logs = HabitLog.objects.filter(habit=habit)

    def clean(self):
        if len(self.habit_logs) > 0:
            last_habit_log_date = self.habit_logs.first().date
            if last_habit_log_date == timezone.localtime(timezone.now()).date():
                raise forms.ValidationError(f'Нельзя создать отчёт о привычке в дату, в которую был создан последний отчёт ({last_habit_log_date}).')

