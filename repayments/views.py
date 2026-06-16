from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from .models import Paiement
from .serializers import PaiementSerializer, EcheancierDetailSerializer
from credits.models import Echeancier
from users.permissions import IsAdminOrAgent


@extend_schema(tags=['Remboursements'])
class EcheancierViewSet(viewsets.ReadOnlyModelViewSet):
    """Consulter les échéanciers de remboursement."""
    serializer_class = EcheancierDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Echeancier.objects.select_related('credit__client').prefetch_related('paiements')
        if user.role == 'CLIENT':
            return qs.filter(credit__client=user)
        # Filtre optionnel par statut
        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)
        return qs


@extend_schema(tags=['Remboursements'])
class PaiementViewSet(viewsets.ModelViewSet):
    """
    Enregistrement des paiements de remboursement.

    POST : AGENT/ADMIN uniquement.
    GET  : AGENT/ADMIN ou CLIENT (ses propres paiements).
    """
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Paiement.objects.select_related('echeancier__credit__client', 'enregistre_par')
        if user.role == 'CLIENT':
            return qs.filter(echeancier__credit__client=user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'CLIENT':
            echeancier = serializer.validated_data['echeancier']
            if echeancier.credit.client != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Vous n'êtes pas autorisé à régler cette échéance.")
            
            mode = serializer.validated_data.get('mode_paiement')
            if mode not in ['WAVE', 'ORANGE_MONEY', 'MTN_MOMO']:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("Les clients ne peuvent régler que par Mobile Money (Wave, Orange Money, MTN MoMo).")
            
            ref = serializer.validated_data.get('reference_transaction', '').strip()
            if not ref:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("La référence de transaction Mobile Money est obligatoire.")
            
            # Forcer le règlement du montant exact dû (reste à payer + pénalités)
            serializer.save(
                enregistre_par=user,
                capital_paye=echeancier.reste_a_payer,
                penalites_payees=echeancier.penalite_courante
            )
        else:
            serializer.save(enregistre_par=user)

    def http_method_not_allowed(self, request, *args, **kwargs):
        return super().http_method_not_allowed(request, *args, **kwargs)


# ─── WEB VIEW ─────────────────────────────────────────────────────────────────

@login_required(login_url='login_web')
def rembourser_web(request):
    """Enregistrer un paiement depuis le portail web (client ou agent)."""
    if request.method == 'POST':
        echeancier_id = request.POST.get('echeancier')
        mode = request.POST.get('mode', 'ESPECES')
        reference = request.POST.get('reference', '')

        echeance = get_object_or_404(Echeancier, id=echeancier_id)

        if request.user.role == 'CLIENT':
            # Vérifications client
            if echeance.credit.client != request.user:
                messages.error(request, "Vous n'êtes pas autorisé à régler cette échéance.")
                return redirect('home_web')
            if mode == 'ESPECES':
                messages.error(request, "Les paiements en espèces doivent être enregistrés par un agent.")
                return redirect('home_web')
            if not reference.strip():
                messages.error(request, "La référence de transaction Mobile Money est obligatoire.")
                return redirect('home_web')
            
            capital_dec = echeance.reste_a_payer
            penalites_dec = echeance.penalite_courante
        else:
            # Agent/Admin
            capital = request.POST.get('capital', '0')
            penalites = request.POST.get('penalites', '0')
            try:
                from decimal import Decimal
                capital_dec = Decimal(capital)
                penalites_dec = Decimal(penalites)
            except Exception:
                messages.error(request, "Montant invalide.")
                return redirect('home_web')

        Paiement.objects.create(
            echeancier=echeance,
            enregistre_par=request.user,
            capital_paye=capital_dec,
            penalites_payees=penalites_dec,
            mode_paiement=mode,
            reference_transaction=reference,
        )
        messages.success(request, f"Remboursement de {capital_dec + penalites_dec:,.0f} FCFA enregistré avec succès !")
    return redirect('home_web')
