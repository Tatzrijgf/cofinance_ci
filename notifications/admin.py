from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'destinataire', 'titre', 'lu', 'cree_le']
    list_filter = ['lu', 'cree_le']
    search_fields = ['destinataire__username', 'titre', 'message']
    readonly_fields = ['cree_le']
