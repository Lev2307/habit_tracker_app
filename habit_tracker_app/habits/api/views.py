from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.response import Response

from .serializers import HabitSerializer
from ..models import Habit


class HabitsViewSet(viewsets.ModelViewSet):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True, fields=('id', 'title', 'purpose', 'habit_datetype', 'frequency', 'streak'))
        return Response(serializer.data)
    
    def retrieve(self, request, pk):
        habit = self.get_object()
        serializer = HabitSerializer(habit, context={'habit': habit})
        return Response(serializer.data)
