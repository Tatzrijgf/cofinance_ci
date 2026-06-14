from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, marquer_lu_web

router = DefaultRouter()
router.register(r'api/notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('notifications/<int:pk>/lu/', marquer_lu_web, name='marquer_lu_web'),
]
