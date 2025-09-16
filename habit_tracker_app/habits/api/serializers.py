from rest_framework import serializers

from ..models import Habit, HabitLog
from ..helpers import divide_habit_logs_of_weekly_habit_by_week_blocks

class HabitSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    habit_logs = serializers.SerializerMethodField('habit_logs_divided_into_blocks', read_only=True)
    class Meta:
        model = Habit
        fields = ['id', 'user', 'title', 'purpose', 'habit_datetype', 'frequency', 'streak', 'habit_logs']
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
        habit = self.context.get('habit')
        if habit is None:
            return 'None is returned as habit.'
        habit_logs_json = HabitLogSerializer(HabitLog.objects.filter(habit=habit), many=True).data
        if habit.habit_datetype == 'week':
            divided_into_blocks = divide_habit_logs_of_weekly_habit_by_week_blocks(habit_logs_json, is_json=True)
            return divided_into_blocks
        return habit_logs_json
    
    def validate(self, data):
        habit_datetype = data.get('habit_datetype')
        frequency = data.get('frequency')
        if habit_datetype == 'every_day' and frequency != 1:
            raise serializers.ValidationError({'frequency': 'Если вы выбрали выполнять привычку каждый день, поле периодичности должно быть равным 1'})
        return data
    
    def update(self, instance, validated_data):
        habit_datetype = validated_data.get('habit_datetype')
        frequency = validated_data.get('frequency')
        if (habit_datetype != instance.habit_datetype) or (frequency != instance.frequency):
            HabitLog.objects.filter(habit=instance).delete()
        return instance
    
class HabitLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitLog
        fields = ['id', 'status', 'date', 'comment']
        