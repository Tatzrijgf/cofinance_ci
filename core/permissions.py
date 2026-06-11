from rest_framework import permissions

class IsAgentOrAdmin(permissions.BasePermission):
    """
    Permet l'accès uniquement aux Agents de terrain ou aux Administrateurs.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['AGENT', 'ADMIN']


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Permet au client de voir et gérer uniquement ses propres objets,
    mais donne un accès total aux agents et administrateurs.
    """
    def has_object_permission(self, request, view, obj):
        # Si l'utilisateur est Agent ou Admin, l'accès est accordé
        if request.user.role in ['AGENT', 'ADMIN']:
            return True
        # Sinon, l'utilisateur doit être le propriétaire de l'objet
        return obj.client == request.user