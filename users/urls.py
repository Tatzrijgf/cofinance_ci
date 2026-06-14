from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, UserProfileView, UserListView,
    login_web, register_web, logout_web, home_web,
)

urlpatterns = [
    # Web
    path('', home_web, name='home_web'),
    path('login/', login_web, name='login_web'),
    path('register/', register_web, name='register_web'),
    path('logout/', logout_web, name='logout_web'),

    # API — Auth
    path('api/auth/register/', RegisterView.as_view(), name='api-register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='api-login'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('api/auth/profile/', UserProfileView.as_view(), name='api-profile'),
    path('api/auth/users/', UserListView.as_view(), name='api-users'),
]
