# core/views.py
from rest_framework import status, generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework import serializers

# Importation pour documenter Swagger explicitement (OAS 3.0)
from drf_spectacular.utils import extend_schema

from django.db import models
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    CustomUser, Credit, PieceJustificative, Echeancier, 
    Paiement, ProduitAssurance, SouscriptionAssurance, Notification, Conversation
)
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, CreditSerializer, 
    PieceJustificativeSerializer, EcheancierSerializer, PaiementSerializer,
    ProduitAssuranceSerializer, SouscriptionAssuranceSerializer, NotificationSerializer
)
from .permissions import IsOwnerOrStaff, IsAgentOrAdmin, IsAdminOrReadOnly

# ==========================================
# UTILITAIRE : SYSTÈME D'ALERTES / NOTIFICATIONS AUTOMATIQUES
# ==========================================

def declencher_notification(user, titre, message, type_notif):
    """
    Crée automatiquement une notification pour l'utilisateur en base de données.
    """
    Notification.objects.create(
        destinataire=user,
        titre=titre,
        message=message,
        type_notification=type_notif
    )

# ==========================================
# AUTOMATIONS ÉCHÉANCIERS
# ==========================================

def generer_echeancier_credit(credit):
    if credit.echeances.exists():
        return

    total_interets = credit.montant * (credit.taux_interet / Decimal('100.00'))
    total_a_rembourser = credit.montant + total_interets
    montant_mensuel = total_a_rembourser / Decimal(str(credit.duree_mois))

    montant_mensuel = montant_mensuel.quantize(Decimal('0.01'))
    date_courante = date.today()

    for i in range(1, credit.duree_mois + 1):
        date_echeance = date_courante + timedelta(days=30 * i)
        
        if i == credit.duree_mois:
            montant_deja_planifie = montant_mensuel * (credit.duree_mois - 1)
            montant_du = total_a_rembourser - montant_deja_planifie
        else:
            montant_du = montant_mensuel

        Echeancier.objects.create(
            credit=credit,
            date_echeance=date_echeance,
            montant_du=montant_du,
            statut='A_PAYER'
        )

# ==========================================
# VIEWS & VIEWSETS
# ==========================================

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreditViewSet(viewsets.ModelViewSet):
    queryset = Credit.objects.all()
    serializer_class = CreditSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_superuser:
            return Credit.objects.all()
        return Credit.objects.filter(client=user)

    def perform_create(self, serializer):
        credit = serializer.save(client=self.request.user)
        declencher_notification(
            self.request.user, 
            "Demande de crédit soumise", 
            f"Votre demande de microcrédit de {credit.montant} FCFA a été enregistrée avec succès.", 
            "CHANGEMENT_STATUT_CREDIT"
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAgentOrAdmin])
    def changer_statut(self, request, pk=None):
        credit = self.get_object()
        nouveau_statut = request.data.get('statut')
        
        valid_statuses = [choice[0] for choice in Credit.STATUS_CHOICES]
        if nouveau_statut not in valid_statuses:
            return Response(
                {"error": f"Statut invalide. Choisissez parmi : {', '.join(valid_statuses)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        credit.statut = nouveau_statut
        credit.save()

        declencher_notification(
            credit.client, 
            "Mise à jour de votre demande de crédit", 
            f"Le statut de votre demande de crédit {credit.id} a changé. Nouveau statut : {nouveau_statut}.", 
            "CHANGEMENT_STATUT_CREDIT"
        )

        if nouveau_statut == 'APPROUVEE':
            generer_echeancier_credit(credit)
        
        return Response(CreditSerializer(credit).data, status=status.HTTP_200_OK)


class PieceJustificativeViewSet(viewsets.ModelViewSet):
    queryset = PieceJustificative.objects.all()
    serializer_class = PieceJustificativeSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        credit_id = self.request.data.get('credit')
        try:
            credit = Credit.objects.get(id=credit_id)
            if credit.client != self.request.user and self.request.user.role not in ['AGENT', 'ADMIN'] and not self.request.user.is_superuser:
                raise serializers.ValidationError("Vous n'avez pas l'autorisation d'ajouter des fichiers à ce crédit.")
            serializer.save(credit=credit)
        except Credit.DoesNotExist:
            raise serializers.ValidationError("Le crédit spécifié n'existe pas.")


class EcheancierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Echeancier.objects.all()
    serializer_class = EcheancierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_superuser:
            return Echeancier.objects.all()
        return Echeancier.objects.filter(credit__client=user)


class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAgentOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_superuser:
            return Paiement.objects.all()
        return Paiement.objects.filter(echeancier__credit__client=user)

    def perform_create(self, serializer):
        # 1. Sauvegarde du paiement
        paiement = serializer.save(enregistre_par=self.request.user)
        echeance = paiement.echeancier
        
        # 2. Clôture automatique de l'échéance si montant couvert
        if echeance.total_paye_capital >= echeance.montant_du:
            echeance.statut = 'PAYE'
            echeance.save()

        # Calcul du solde restant dû
        solde_restant = echeance.montant_du - echeance.total_paye_capital
        if solde_restant < 0:
            solde_restant = Decimal('0.00')

        solde_msg = (
            "Cette échéance est désormais entièrement soldée !" 
            if echeance.statut == 'PAYE' 
            else f"Solde restant dû sur cette échéance : {solde_restant} FCFA."
        )

        # AUTOMATION NOTIFICATION ENRICHIE
        declencher_notification(
            echeance.credit.client, 
            "Remboursement enregistré", 
            f"Un paiement de {paiement.capital_paye} FCFA a été comptabilisé sur votre échéance du {echeance.date_echeance}. {solde_msg}", 
            "RAPPEL_ECHEANCE_REMBOUSEMENT"
        )

        # 3. Clôture automatique du crédit
        credit = echeance.credit
        if not credit.echeances.exclude(statut='PAYE').exists():
            credit.statut = 'CLOTUREE'
            credit.save()


class ProduitAssuranceViewSet(viewsets.ModelViewSet):
    queryset = ProduitAssurance.objects.all()
    serializer_class = ProduitAssuranceSerializer
    permission_classes = [IsAdminOrReadOnly]


class SouscriptionAssuranceViewSet(viewsets.ModelViewSet):
    queryset = SouscriptionAssurance.objects.all()
    serializer_class = SouscriptionAssuranceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_superuser:
            return SouscriptionAssurance.objects.all()
        return SouscriptionAssurance.objects.filter(client=user)

    def perform_create(self, serializer):
        souscription = serializer.save(client=self.request.user)
        declencher_notification(
            self.request.user, 
            "Assurance validée", 
            f"Félicitations, votre souscription au produit '{souscription.produit.nom}' a bien été confirmée. Votre couverture se terminera le {souscription.date_fin}.", 
            "EXPIRATION_ASSURANCE"
        )


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(destinataire=self.request.user).order_by('-cree_le')

    @action(detail=True, methods=['post'])
    def marquer_lu(self, request, pk=None):
        notification = self.get_object()
        notification.lu = True
        notification.save()
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)


# ==========================================
# SÉRIALISATEUR POUR LA DOCUMENTATION DES FILTRES DU DASHBOARD
# ==========================================

class DashboardFilterSerializer(serializers.Serializer):
    """
    Déclare la structure des paramètres de filtrage pour que Swagger 
    les affiche correctement dans son interface de test.
    """
    date_debut = serializers.DateField(required=False, help_text="Format AAAA-MM-JJ")
    date_fin = serializers.DateField(required=False, help_text="Format AAAA-MM-JJ")
    agent_id = serializers.IntegerField(required=False, help_text="ID de l'agent de terrain")
    region = serializers.CharField(required=False, help_text="Ex: ABIDJAN, BOUAKE, KORHOGO...")


# ==========================================
# MODULE 05 : TABLEAU DE BORD ADMINISTRATEUR (CORRIGÉ & DOCUMENTÉ)
# ==========================================

class AdminDashboardView(APIView):
    """
    Tableau de bord financier et opérationnel en temps réel.
    - Évite l'overlap comptable des agents.
    - Applique l'analyse temporelle à l'ensemble du workflow.
    """
    permission_classes = [permissions.IsAuthenticated, IsAgentOrAdmin]

    # Le décorateur extend_schema indique à drf-spectacular d'ajouter 
    # des champs de saisie pour chaque attribut de DashboardFilterSerializer
    @extend_schema(parameters=[DashboardFilterSerializer])
    def get(self, request):
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        agent_id = request.query_params.get('agent_id')
        region = request.query_params.get('region')

        # Querysets d'agrégation de base
        credits_qs = Credit.objects.all()
        echeances_qs = Echeancier.objects.all()
        assurances_qs = SouscriptionAssurance.objects.all()
        conversations_qs = Conversation.objects.all()
        paiements_qs = Paiement.objects.all()

        # 1. Filtre temporel complet
        if date_debut and date_fin:
            credits_qs = credits_qs.filter(date_demande__range=[date_debut, date_fin])
            assurances_qs = assurances_qs.filter(date_debut__range=[date_debut, date_fin])
            echeances_qs = echeances_qs.filter(date_echeance__range=[date_debut, date_fin])
            paiements_qs = paiements_qs.filter(date_paiement__range=[date_debut, date_fin])

        # 2. Filtre Agent (Isolation comptable)
        if agent_id:
            paiements_qs = paiements_qs.filter(enregistre_par_id=agent_id)
            echeances_qs = echeances_qs.filter(id__in=paiements_qs.values('echeancier_id')).distinct()

        # 3. Filtre par Région
        if region:
            credits_qs = credits_qs.filter(client__region=region)
            assurances_qs = assurances_qs.filter(client__region=region)
            echeances_qs = echeances_qs.filter(credit__client__region=region)
            paiements_qs = paiements_qs.filter(echeancier__credit__client__region=region)

        # Calculs agrégés
        credits_par_statut = credits_qs.values('statut').annotate(count=models.Count('id'))

        total_du = echeances_qs.aggregate(total=models.Sum('montant_du'))['total'] or Decimal('0.00')
        total_rembourse = paiements_qs.aggregate(total=models.Sum('capital_paye'))['total'] or Decimal('0.00')
        
        taux_recouvrement = Decimal('0.00')
        if total_du > 0:
            taux_recouvrement = (total_rembourse / total_du) * Decimal('100.00')
            taux_recouvrement = taux_recouvrement.quantize(Decimal('0.01'))

        assurances_actives = assurances_qs.filter(statut='ACTIVE').count()
        chats_ouverts = conversations_qs.filter(statut='OUVERTE').count()

        data = {
            "filtres_appliques": {
                "date_debut": date_debut,
                "date_fin": date_fin,
                "agent_id": agent_id,
                "region": region
            },
            "statistiques_credits": {
                "volume_credits_par_statut": list(credits_par_statut),
                "total_capital_planifie": total_du,
                "total_capital_recouvre": total_rembourse,
                "taux_recouvrement_pourcentage": taux_recouvrement,
            },
            "statistiques_assurances": {
                "souscriptions_actives": assurances_actives,
            },
            "statistiques_support": {
                "conversations_support_ouvertes": chats_ouverts
            }
        }

        return Response(data, status=status.HTTP_200_OK)