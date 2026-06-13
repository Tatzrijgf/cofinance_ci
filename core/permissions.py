# core/permissions.py
from rest_framework import permissions

class IsAgentOrAdmin(permissions.BasePermission):
    """
    Permet l'accès uniquement aux Agents de terrain, aux Administrateurs,
    ou à n'importe quel Superutilisateur Django.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Ajout de 'or request.user.is_superuser' pour gérer les comptes créés en terminal
        return request.user.role in ['AGENT', 'ADMIN'] or request.user.is_superuser


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Permet au client de voir et gérer uniquement ses propres objets,
    mais donne un accès total aux agents, administrateurs et superutilisateurs.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['AGENT', 'ADMIN'] or request.user.is_superuser:
            return True
        return obj.client == request.user