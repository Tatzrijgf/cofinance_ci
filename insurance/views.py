from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from .models import ProduitAssurance, SouscriptionAssurance
from .serializers import ProduitAssuranceSerializer, SouscriptionAssuranceSerializer
from users.permissions import IsAdmin


@extend_schema(tags=['Assurances'])
class ProduitAssuranceViewSet(viewsets.ReadOnlyModelViewSet):
    """Catalogue des produits d'assurance (lecture seule pour tous)."""
    queryset = ProduitAssurance.objects.filter(actif=True)
    serializer_class = ProduitAssuranceSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['Assurances'])
class SouscriptionAssuranceViewSet(viewsets.ModelViewSet):
    """
    Souscriptions d'assurance.

    - CLIENT : crée et consulte ses propres souscriptions.
    - AGENT/ADMIN : consulte toutes les souscriptions.
    """
    serializer_class = SouscriptionAssuranceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = SouscriptionAssurance.objects.select_related('client', 'produit')
        if user.role == 'CLIENT':
            return qs.filter(client=user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        produit = serializer.validated_data['produit']
        date_debut = timezone.now().date()
        souscription = serializer.save(client=user, date_debut=date_debut)

        # Notification de confirmation
        try:
            from notifications.models import Notification
            Notification.objects.create(
                destinataire=user,
                titre="Souscription assurance confirmée",
                message=(
                    f"Votre souscription à '{produit.nom}' est activée jusqu'au "
                    f"{souscription.date_fin.strftime('%d/%m/%Y')}."
                ),
            )
        except Exception:
            pass


# ─── WEB VIEW ─────────────────────────────────────────────────────────────────

@login_required(login_url='login_web')
def souscrire_web(request):
    """Souscrire à un produit d'assurance depuis le portail web."""
    if request.method == 'POST':
        produit_id = request.POST.get('produit')
        produit = get_object_or_404(ProduitAssurance, id=produit_id, actif=True)
        souscription = SouscriptionAssurance.objects.create(
            client=request.user,
            produit=produit,
        )
        try:
            from notifications.models import Notification
            Notification.objects.create(
                destinataire=request.user,
                titre="Souscription assurance confirmée",
                message=(
                    f"Souscription à '{produit.nom}' validée jusqu'au "
                    f"{souscription.date_fin.strftime('%d/%m/%Y')}."
                ),
            )
        except Exception:
            pass
        messages.success(request, f"Souscription à '{produit.nom}' validée avec succès !")
    return redirect('home_web')
