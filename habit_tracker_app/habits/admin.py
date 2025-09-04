from django.contrib import admin

from .models import Habit

# Register your models here.

class HabitAdmin(admin.ModelAdmin):
   readonly_fields = ['streak']

admin.site.register(Habit, HabitAdmin)