from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Credit, Echeancier, DocumentCredit
from .serializers import (
    CreditSerializer, CreditCreateSerializer,
    EcheancierSerializer, DocumentCreditSerializer, WorkflowActionSerializer,
)
from .scoring import CreditScoringService
from users.permissions import IsClient, IsAdminOrAgent, IsAdmin


# ─── API VIEWS ────────────────────────────────────────────────────────────────

@extend_schema(tags=['Crédits'])
class CreditViewSet(viewsets.ModelViewSet):
    """
    Gestion complète des demandes de microcrédits.

    - CLIENT : peut créer et voir ses propres demandes.
    - AGENT / ADMIN : peut voir toutes les demandes et effectuer les transitions.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Credit.objects.select_related('client', 'agent').prefetch_related('echeances', 'documents')
        if user.role == 'CLIENT':
            return qs.filter(client=user)
        return qs.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreditCreateSerializer
        return CreditSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'CLIENT':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seuls les clients peuvent soumettre une demande de crédit.")

        montant = serializer.validated_data['montant']
        duree = serializer.validated_data['duree_mois']
        score = CreditScoringService.calculate(user, montant, duree)
        credit = serializer.save(client=user, score_eligibilite=score)

        # Notification de confirmation
        try:
            from notifications.models import Notification
            Notification.objects.create(
                destinataire=user,
                titre="Demande de crédit soumise",
                message=f"Votre demande de {montant:,.0f} FCFA a été reçue. Score : {score}/100. Nous vous répondons sous 48h.",
            )
        except Exception:
            pass

    @extend_schema(request=WorkflowActionSerializer, responses={200: CreditSerializer})
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrAgent], url_path='analyser')
    def analyser(self, request, pk=None):
        """Passer la demande en phase d'analyse (AGENT/ADMIN)."""
        credit = self.get_object()
        try:
            credit.passer_en_analyse(agent=request.user)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CreditSerializer(credit).data)

    @extend_schema(request=WorkflowActionSerializer, responses={200: CreditSerializer})
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrAgent], url_path='approuver')
    def approuver(self, request, pk=None):
        """Approuver la demande et générer l'échéancier (AGENT/ADMIN)."""
        credit = self.get_object()
        try:
            credit.approuver()
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CreditSerializer(credit).data)

    @extend_schema(request=WorkflowActionSerializer, responses={200: CreditSerializer})
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrAgent], url_path='rejeter')
    def rejeter(self, request, pk=None):
        """Rejeter la demande avec un motif (AGENT/ADMIN)."""
        credit = self.get_object()
        motif = request.data.get('motif', '')
        try:
            credit.rejeter(motif=motif)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CreditSerializer(credit).data)

    @extend_schema(responses={200: CreditSerializer})
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrAgent], url_path='decaisser')
    def decaisser(self, request, pk=None):
        """Décaisser le crédit approuvé (AGENT/ADMIN)."""
        credit = self.get_object()
        try:
            credit.decaisser()
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CreditSerializer(credit).data)

    @extend_schema(responses={200: EcheancierSerializer(many=True)})
    @action(detail=True, methods=['get'], url_path='echeancier')
    def echeancier(self, request, pk=None):
        """Consulter l'échéancier de remboursement d'un crédit."""
        credit = self.get_object()
        echeances = credit.echeances.all()
        return Response(EcheancierSerializer(echeances, many=True).data)


@extend_schema(tags=['Crédits'])
class DocumentCreditViewSet(viewsets.ModelViewSet):
    """Upload et consultation des pièces justificatives."""
    serializer_class = DocumentCreditSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'CLIENT':
            return DocumentCredit.objects.filter(credit__client=user)
        return DocumentCredit.objects.all()


# ─── WEB VIEWS ────────────────────────────────────────────────────────────────

@login_required(login_url='login_web')
def credit_creer_web(request):
    """Soumettre une nouvelle demande de crédit via le formulaire web."""
    if request.method == 'POST':
        montant = request.POST.get('montant', '0')
        duree = request.POST.get('duree', '1')
        frequence = request.POST.get('frequence', 'MENSUEL')
        objet = request.POST.get('objet', 'AUTRE')

        try:
            from decimal import Decimal
            montant_dec = Decimal(montant)
            duree_int = int(duree)
            if montant_dec <= 0 or duree_int <= 0:
                raise ValueError()
        except Exception:
            messages.error(request, "Montant et durée invalides.")
            return redirect('home_web')

        score = CreditScoringService.calculate(request.user, montant_dec, duree_int)
        credit = Credit.objects.create(
            client=request.user,
            montant=montant_dec,
            duree_mois=duree_int,
            frequence=frequence,
            objet=objet,
            score_eligibilite=score,
        )
        try:
            from notifications.models import Notification
            Notification.objects.create(
                destinataire=request.user,
                titre="Demande de crédit soumise",
                message=f"Votre demande de {montant_dec:,.0f} FCFA a été enregistrée (score : {score}/100).",
            )
        except Exception:
            pass
        messages.success(request, f"Demande de crédit soumise avec succès ! Score d'éligibilité : {score}/100.")
    return redirect('home_web')


@login_required(login_url='login_web')
def credit_action_web(request, pk, action_name):
    """Actions sur un crédit via le portail web (agent/admin)."""
    credit = get_object_or_404(Credit, pk=pk)
    try:
        if action_name == 'analyser':
            credit.passer_en_analyse(agent=request.user)
            messages.success(request, f"Crédit #{pk} passé en analyse.")
        elif action_name == 'approuver':
            credit.approuver()
            messages.success(request, f"Crédit #{pk} approuvé. Échéancier généré.")
        elif action_name == 'decaisser':
            credit.decaisser()
            messages.success(request, f"Crédit #{pk} décaissé.")
        elif action_name == 'rejeter':
            motif = request.POST.get('motif', '')
            credit.rejeter(motif=motif)
            messages.warning(request, f"Crédit #{pk} rejeté.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('home_web')
