from rest_framework import status, generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework import serializers

from decimal import Decimal
from datetime import date, timedelta

from .models import CustomUser, Credit, PieceJustificative, Echeancier, Paiement, ProduitAssurance, SouscriptionAssurance
from .serializers import (
    UserRegistrationSerializer, 
    UserProfileSerializer, 
    CreditSerializer, 
    PieceJustificativeSerializer,
    EcheancierSerializer,
    PaiementSerializer,
    ProduitAssuranceSerializer,
    SouscriptionAssuranceSerializer
)
from .permissions import IsOwnerOrStaff, IsAgentOrAdmin

# ==========================================
# AUTOMATIONS CRÉDITS
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
# PERMISSIONS SUPPLÉMENTAIRES ASSURANCES
# ==========================================

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permet à n'importe quel utilisateur connecté de lire les données (GET),
    mais restreint les modifications (POST, PUT, DELETE) uniquement aux Administrateurs.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and (request.user.is_superuser or request.user.role == 'ADMIN')

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
        serializer.save(client=self.request.user)

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
        paiement = serializer.save(enregistre_par=self.request.user)
        echeance = paiement.echeancier
        
        if echeance.total_paye_capital >= echeance.montant_du:
            echeance.statut = 'PAYE'
            echeance.save()

        credit = echeance.credit
        if not credit.echeances.exclude(statut='PAYE').exists():
            credit.statut = 'CLOTUREE'
            credit.save()


# ==========================================
# VUES ASSURANCE MOBILE (NOUVEAU)
# ==========================================

class ProduitAssuranceViewSet(viewsets.ModelViewSet):
    """
    Gère le catalogue des produits d'assurance de COFINANCE CI.
    - Lecture : Tous les utilisateurs authentifiés (IsAdminOrReadOnly).
    - Écriture (Création/Modification) : Réservé uniquement aux administrateurs.
    """
    queryset = ProduitAssurance.objects.all()
    serializer_class = ProduitAssuranceSerializer
    permission_classes = [IsAdminOrReadOnly]


class SouscriptionAssuranceViewSet(viewsets.ModelViewSet):
    """
    Gère les souscriptions d'assurance par les clients.
    - Un client ne voit que ses propres souscriptions d'assurance.
    - Un agent ou admin a un accès total.
    """
    queryset = SouscriptionAssurance.objects.all()
    serializer_class = SouscriptionAssuranceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN'] or user.is_superuser:
            return SouscriptionAssurance.objects.all()
        return SouscriptionAssurance.objects.filter(client=user)

    def perform_create(self, serializer):
        """
        Assigne automatiquement l'utilisateur connecté comme souscripteur.
        """
        serializer.save(client=self.request.user)