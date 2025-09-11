from django.shortcuts import render, HttpResponseRedirect, get_object_or_404, Http404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy

from .models import Habit, HabitLog
from .forms import CreateHabitForm, CreateHabitLogForm
from .helpers import set_habit_logs_status_forgot_to_mark, increase_habit_streak_field

# Create your views here.

def redirect_to_habits(request):
    return HttpResponseRedirect(reverse('habits:habits_list'))

class HabitsList(LoginRequiredMixin, generic.ListView):
    model = Habit
    context_object_name = 'habits'
    template_name = 'habits/habits_list.html'
    success_url = reverse_lazy('habits:habits_list')
    
    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)
        data['habitlog_form'] = CreateHabitLogForm
        return data

class CreateHabit(LoginRequiredMixin, generic.CreateView):
    model = Habit
    form_class = CreateHabitForm
    template_name = 'habits/create_habit.html'
    success_url = reverse_lazy('habits:habits_list')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['user'] = self.request.user
        return kw
    
class DeleteHabit(LoginRequiredMixin, generic.DeleteView):
    model = Habit
    template_name = 'habits/delete_habit.html'
    success_url = reverse_lazy('habits:habits_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.user != self.request.user:
            return self.handle_habit_not_found()

        return super().dispatch(request, *args, **kwargs)

    def handle_habit_not_found(self):
        return HttpResponseRedirect(reverse('habits:habits_list'))

class HabitDetail(LoginRequiredMixin, generic.DetailView):
    model = Habit
    template_name = 'habits/habit_detail.html'
    success_url = reverse_lazy('habits:habits_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.user != self.request.user:
            return self.handle_habit_not_found()

        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['habitLogs'] = HabitLog.objects.filter(habit=Habit.objects.get(id=self.kwargs['pk']))
        return context
    
    def handle_habit_not_found(self):
        return HttpResponseRedirect(reverse('habits:habits_list'))

@login_required
def set_habitLog_status(request, pk):
    status = request.GET.get('status')
    try:
        habit = get_object_or_404(Habit, user=request.user, pk=pk)
    except Http404:
        return HttpResponseRedirect(reverse('habits:habits_list'))
    
    habit_logs = HabitLog.objects.filter(habit=habit)

    if status == 'complited' or status == 'incomplited':
        form = CreateHabitLogForm(habit=habit)
        if request.method == "POST":
            form = CreateHabitLogForm(habit=habit, data=request.POST)
            if form.is_valid():
                if habit_logs.count() > 0:
                    last_habit_log_date = habit_logs.first().date
                    set_habit_logs_status_forgot_to_mark(habit, last_habit_log_date)
                increase_habit_streak_field(habit, habit_logs, status)
                habitLog = HabitLog(habit=habit, comment=form.cleaned_data.get('comment'), status=status)
                habitLog.save()
                return HttpResponseRedirect(reverse("habits:habits_list"))
            
        return render(request, 'habits/set_habit_log_status.html', {'habit': habit, 'form': form, 'status': status})
    else:
        return HttpResponseRedirect(reverse('habits:habits_list'))
    
