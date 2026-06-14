from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EcheancierViewSet, PaiementViewSet, rembourser_web

router = DefaultRouter()
router.register(r'api/echeances', EcheancierViewSet, basename='echeance')
router.register(r'api/paiements', PaiementViewSet, basename='paiement')

urlpatterns = [
    path('', include(router.urls)),
    path('repayments/payer/', rembourser_web, name='rembourser_web'),
]
