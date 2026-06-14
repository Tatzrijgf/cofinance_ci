from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProduitAssuranceViewSet, SouscriptionAssuranceViewSet, souscrire_web

router = DefaultRouter()
router.register(r'api/produits-assurance', ProduitAssuranceViewSet, basename='produit-assurance')
router.register(r'api/souscriptions-assurance', SouscriptionAssuranceViewSet, basename='souscription-assurance')

urlpatterns = [
    path('', include(router.urls)),
    path('insurance/souscrire/', souscrire_web, name='souscrire_web'),
]
