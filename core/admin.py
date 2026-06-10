from django.contrib import admin

# Register your models here.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Credit, PieceJustificative, Echeancier, Paiement

# Enregistrement de l'utilisateur personnalisé
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Nous ajoutons nos champs personnalisés (role, telephone, region) à l'affichage de l'admin
    fieldsets = UserAdmin.fieldsets + (
        ('Informations COFINANCE', {'fields': ('role', 'telephone', 'region')}),
    )
    list_display = ['username', 'email', 'role', 'telephone', 'region', 'is_staff']
    list_filter = ['role', 'region']

# Enregistrement simple des autres modèles pour commencer
admin.site.register(Credit)
admin.site.register(PieceJustificative)
admin.site.register(Echeancier)
admin.site.register(Paiement)