from django.contrib import admin

from .models import Habit, HabitLog

class HabitAdmin(admin.ModelAdmin):
   readonly_fields = ['streak']

class HabitLogAdmin(admin.ModelAdmin):
   readonly_fields = ['date']

admin.site.register(Habit, HabitAdmin)
admin.site.register(HabitLog, HabitLogAdmin)