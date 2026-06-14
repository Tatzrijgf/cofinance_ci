from django.contrib import admin
from .models import Credit, Echeancier, DocumentCredit

class EcheancierInline(admin.TabularInline):
    model = Echeancier
    extra = 0
    can_delete = False
    fields = ['numero', 'date_echeance', 'montant_du', 'statut']
    readonly_fields = ['numero', 'date_echeance', 'montant_du', 'statut']

class DocumentCreditInline(admin.TabularInline):
    model = DocumentCredit
    extra = 1

@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'montant', 'statut', 'score_eligibilite', 'date_demande', 'agent']
    list_filter = ['statut', 'frequence', 'objet', 'date_demande']
    search_fields = ['client__username', 'client__telephone', 'agent__username']
    inlines = [EcheancierInline, DocumentCreditInline]
    readonly_fields = ['score_eligibilite', 'date_demande']

@admin.register(Echeancier)
class EcheancierAdmin(admin.ModelAdmin):
    list_display = ['id', 'credit', 'numero', 'date_echeance', 'montant_du', 'statut', 'penalite_courante']
    list_filter = ['statut', 'date_echeance']
    search_fields = ['credit__client__username', 'credit__client__telephone']
    readonly_fields = ['penalite_courante']

admin.site.register(DocumentCredit)
