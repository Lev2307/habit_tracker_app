from django.urls import path, include

from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from .views import HabitsViewSet, create_habit_log

router = DefaultRouter()
router.register(r'habits', HabitsViewSet, basename='habit')

app_name = 'api'
urlpatterns = [
    path('', include(router.urls)),
    path('habits/<int:pk>/create_habit_log/', create_habit_log, name='api_create_habit_log'),

    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
]