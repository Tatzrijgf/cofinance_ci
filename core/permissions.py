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


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permet à n'importe quel utilisateur connecté de lire les données (GET, SAFE_METHODS),
    mais restreint la création ou la modification uniquement aux Administrateurs.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and (request.user.is_superuser or request.user.role == 'ADMIN')