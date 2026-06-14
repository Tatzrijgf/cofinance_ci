from django.urls import path
from .views import AdminDashboardView, AlertesView

urlpatterns = [
    path('api/admin/dashboard/', AdminDashboardView.as_view(), name='api-dashboard'),
    path('api/admin/alertes/', AlertesView.as_view(), name='api-alertes'),
]
