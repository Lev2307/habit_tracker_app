from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from .serializers import HabitSerializer, HabitLogSerializer
from ..models import Habit

class HabitsViewSet(ModelViewSet):
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
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_habit_log(request, pk):
    try:
        habit = Habit.objects.get(id=pk)
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if habit.user != request.user:
        return Response({"message": "You are not allowed to create log for this habit."}, status=status.HTTP_403_FORBIDDEN)
    
    habit_log_serializer = HabitLogSerializer(data=request.data, habit=habit)
    if habit_log_serializer.is_valid(raise_exception=True):
        habit_log_serializer.save()
        return Response(habit_log_serializer.data, status=status.HTTP_201_CREATED)
