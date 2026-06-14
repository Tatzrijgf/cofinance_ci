from django.contrib import admin
from .models import ProduitAssurance, SouscriptionAssurance

@admin.register(ProduitAssurance)
class ProduitAssuranceAdmin(admin.ModelAdmin):
    list_display = ['id', 'nom', 'categorie', 'prime_mensuelle', 'duree_validite_mois', 'couverture_max', 'actif']
    list_filter = ['categorie', 'actif']
    search_fields = ['nom', 'description']

@admin.register(SouscriptionAssurance)
class SouscriptionAssuranceAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'produit', 'date_debut', 'date_fin', 'statut', 'alerte_expiration_envoyee']
    list_filter = ['statut', 'alerte_expiration_envoyee', 'date_debut', 'date_fin']
    search_fields = ['client__username', 'produit__nom']
