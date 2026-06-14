from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['expediteur', 'contenu', 'envoye_le', 'lu_par_agent', 'lu_par_client']
    can_delete = False

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'agent', 'sujet', 'statut', 'cree_le', 'ferme_le']
    list_filter = ['statut', 'cree_le', 'ferme_le']
    search_fields = ['client__username', 'agent__username', 'sujet']
    inlines = [MessageInline]
    readonly_fields = ['cree_le', 'ferme_le']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'expediteur', 'envoye_le', 'lu_par_agent', 'lu_par_client']
    list_filter = ['lu_par_agent', 'lu_par_client', 'envoye_le']
    search_fields = ['conversation__sujet', 'expediteur__username', 'contenu']
    readonly_fields = ['envoye_le']
