from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'region', 'telephone', 'is_staff']
    list_filter = ['role', 'region', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Métier', {'fields': ('role', 'telephone', 'region', 'revenu_mensuel')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Métier', {'fields': ('role', 'telephone', 'region', 'revenu_mensuel')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
