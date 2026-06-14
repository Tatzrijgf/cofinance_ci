from django.contrib import admin
from .models import Paiement

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['id', 'echeancier', 'capital_paye', 'penalites_payees', 'mode_paiement', 'reference_transaction', 'date_paiement', 'enregistre_par']
    list_filter = ['mode_paiement', 'date_paiement']
    search_fields = ['echeancier__credit__client__username', 'reference_transaction']
    readonly_fields = ['date_paiement']
