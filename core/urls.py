# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, UserProfileView, CreditViewSet, 
    PieceJustificativeViewSet, EcheancierViewSet, PaiementViewSet,
    ProduitAssuranceViewSet, SouscriptionAssuranceViewSet
)

# Configuration globale de notre routeur API
router = DefaultRouter()
router.register(r'credits', CreditViewSet, basename='credit')
router.register(r'justificatifs', PieceJustificativeViewSet, basename='justificatif')
router.register(r'echeances', EcheancierViewSet, basename='echeance')
router.register(r'paiements', PaiementViewSet, basename='paiement')

# Nouvelles routes de gestion des Assurances
router.register(r'produits-assurance', ProduitAssuranceViewSet, basename='produit-assurance')
router.register(r'souscriptions-assurance', SouscriptionAssuranceViewSet, basename='souscription-assurance')

urlpatterns = [
    path('', include(router.urls)),

    # Authentification
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/profile/', UserProfileView.as_view(), name='auth_profile'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]