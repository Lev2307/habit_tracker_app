from rest_framework import serializers

from ..models import Habit, HabitLog
from ..helpers import divide_habit_logs_of_weekly_habit_by_week_blocks, set_habit_logs_status_forgot_to_mark, increase_habit_streak_field

class HabitSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    habit_logs = serializers.SerializerMethodField('habit_logs_divided_into_blocks', read_only=True)
    class Meta:
        model = Habit
        fields = ['id', 'user', 'title', 'purpose', 'datetype', 'frequency', 'streak', 'habit_logs']
        read_only_fields = ('streak', )

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def habit_logs_divided_into_blocks(self, *args):
        habit = self.context.get('habit', '')
        if habit == '':
            return []
        habit_logs_json = HabitLogSerializer(HabitLog.objects.filter(habit=habit).order_by("-date"), many=True).data
        if habit.datetype == 'weekly':
            divided_into_blocks = divide_habit_logs_of_weekly_habit_by_week_blocks(habit_logs_json, is_json=True)
            return divided_into_blocks
        return habit_logs_json
    
    def validate(self, data):
        datetype = data.get('datetype')
        frequency = data.get('frequency')
        if datetype == 'daily' and frequency != 1:
            raise serializers.ValidationError({'frequency': 'If you have chosen to perform a habit every day, the frequency field should be equal to 1.'})
        return data
    
    def update(self, instance, validated_data):
        datetype = validated_data.get('datetype')
        frequency = validated_data.get('frequency')
        if (datetype != instance.datetype) or (frequency != instance.frequency):
            HabitLog.objects.filter(habit=instance).delete()
            instance.streak = 0
        instance.title = validated_data.get('title')
        instance.purpose = validated_data.get('purpose')
        instance.datetype = datetype
        instance.frequency = frequency
        instance.save()
        return instance
    
class HabitLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitLog
        fields = ['id', 'status', 'comment']

    def __init__(self, *args, **kwargs):
        self.habit = kwargs.pop('habit', None)
        super().__init__(*args, **kwargs)

        self.habit_logs = HabitLog.objects.filter(habit=self.habit)
    
    def create(self, validated_data):
        if self.habit_logs.count() > 0:
            last_habit_log_date = self.habit_logs.last().date
            set_habit_logs_status_forgot_to_mark(self.habit, last_habit_log_date)
        increase_habit_streak_field(self.habit, self.habit_logs, self.validated_data['status'])

        instance = HabitLog.objects.create(
            habit=self.habit,
            comment=validated_data['comment'],
            status=validated_data['status']
        )
        return instance
