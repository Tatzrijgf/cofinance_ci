from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserProfileView, CreditViewSet, PieceJustificativeViewSet

# Utilisation d'un routeur pour lister automatiquement nos ViewSets
router = DefaultRouter()
router.register(r'credits', CreditViewSet, basename='credit')
router.register(r'justificatifs', PieceJustificativeViewSet, basename='justificatif')

urlpatterns = [
    # Inclusion des URLs générées par le routeur
    path('', include(router.urls)),

    # Authentification
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/profile/', UserProfileView.as_view(), name='auth_profile'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]