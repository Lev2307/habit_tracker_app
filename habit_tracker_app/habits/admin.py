from django.contrib import admin

from .models import Habit, HabitLog

# Register your models here.

class HabitAdmin(admin.ModelAdmin):
   readonly_fields = ['streak']

class HabitLogAdmin(admin.ModelAdmin):
   pass
   # readonly_fields = ['date']

admin.site.register(Habit, HabitAdmin)
admin.site.register(HabitLog, HabitLogAdmin)