from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from .models import Notification
from .serializers import NotificationSerializer


@extend_schema(tags=['Notifications'])
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Notifications in-app de l'utilisateur connecté.

    Utiliser l'action /marquer-lu/ pour marquer une notification comme lue.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(destinataire=self.request.user)
        # Filtre optionnel : ?non_lues=1
        if self.request.query_params.get('non_lues'):
            qs = qs.filter(lu=False)
        return qs

    @extend_schema(responses={200: NotificationSerializer})
    @action(detail=True, methods=['post'], url_path='marquer-lu')
    def marquer_lu(self, request, pk=None):
        """Marquer une notification comme lue."""
        notif = self.get_object()
        notif.lu = True
        notif.save()
        return Response(NotificationSerializer(notif).data)

    @extend_schema(responses={200: {'type': 'object', 'properties': {'marked': {'type': 'integer'}}}})
    @action(detail=False, methods=['post'], url_path='tout-marquer-lu')
    def tout_marquer_lu(self, request):
        """Marquer toutes les notifications non lues comme lues."""
        count = Notification.objects.filter(destinataire=request.user, lu=False).update(lu=True)
        return Response({'marked': count})


# ─── WEB VIEW ─────────────────────────────────────────────────────────────────

@login_required(login_url='login_web')
def marquer_lu_web(request, pk):
    """Marquer une notification comme lue via le portail web."""
    notif = get_object_or_404(Notification, id=pk, destinataire=request.user)
    notif.lu = True
    notif.save()
    return redirect('home_web')
