from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Réservé aux administrateurs COFINANCE CI."""
    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role == 'ADMIN' or request.user.is_superuser)
        )


class IsAgent(BasePermission):
    """Réservé aux agents de terrain."""
    message = "Accès réservé aux agents."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'AGENT'
        )


class IsClient(BasePermission):
    """Réservé aux clients."""
    message = "Accès réservé aux clients."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'CLIENT'
        )


class IsAdminOrAgent(BasePermission):
    """Accessible aux administrateurs et agents."""
    message = "Accès réservé aux agents et administrateurs."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('ADMIN', 'AGENT')
        )


class IsOwnerOrAdminOrAgent(BasePermission):
    """Le propriétaire, un agent ou un admin peut accéder."""

    def has_object_permission(self, request, view, obj):
        if request.user.role in ('ADMIN', 'AGENT') or request.user.is_superuser:
            return True
        # Supporte les objets avec .client ou .user
        owner = getattr(obj, 'client', None) or getattr(obj, 'user', None)
        return owner == request.user
