from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import HabitSerializer
from ..models import Habit


class HabitsViewSet(viewsets.ModelViewSet):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True, fields=('id', 'title', 'purpose', 'datetype', 'frequency', 'streak'))
        return Response(serializer.data)
    
    def retrieve(self, request, pk):
        habit = self.get_object()
        serializer = self.get_serializer(habit, context={'habit': habit})
        return Response(serializer.data)