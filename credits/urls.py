from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreditViewSet, DocumentCreditViewSet, credit_creer_web, credit_action_web

router = DefaultRouter()
router.register(r'api/credits', CreditViewSet, basename='credit')
router.register(r'api/documents-credit', DocumentCreditViewSet, basename='document-credit')

urlpatterns = [
    path('', include(router.urls)),
    # Web
    path('credits/creer/', credit_creer_web, name='credit_creer_web'),
    path('credits/<int:pk>/<str:action_name>/', credit_action_web, name='credit_action_web'),
]
