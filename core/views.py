from django.shortcuts import render

# Create your views here.

from rest_framework import status, generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework import serializers

from .models import CustomUser, Credit, PieceJustificative
from .serializers import (
    UserRegistrationSerializer, 
    UserProfileSerializer, 
    CreditSerializer, 
    PieceJustificativeSerializer
)
from .permissions import IsOwnerOrStaff, IsAgentOrAdmin

# ==========================================
# 1. VUES DE CONTRÔLE DES UTILISATEURS
# ==========================================

class RegisterView(generics.CreateAPIView):
    """
    Vue pour l'inscription en libre-service des nouveaux clients.
    Accessible sans authentification.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(APIView):
    """
    Vue pour consulter et modifier son propre profil utilisateur.
    Requiert une connexion par Token JWT valide.
    """
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


# ==========================================
# 2. VUES DE TRAITEMENT DES CRÉDITS
# ==========================================

class CreditViewSet(viewsets.ModelViewSet):
    """
    ViewSet complet pour gérer les demandes de crédit.
    - Un client ne visualise que ses propres demandes.
    - Un agent ou administrateur a un accès complet à toutes les requêtes.
    """
    queryset = Credit.objects.all()
    serializer_class = CreditSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]

    def get_queryset(self):
        """
        Filtre dynamiquement l'historique en fonction du rôle de l'utilisateur connecté.
        """
        user = self.request.user
        if user.role in ['AGENT', 'ADMIN']:
            return Credit.objects.all()
        return Credit.objects.filter(client=user)

    def perform_create(self, serializer):
        """
        Assigne automatiquement l'utilisateur connecté comme demandeur du crédit.
        """
        serializer.save(client=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAgentOrAdmin])
    def changer_statut(self, request, pk=None):
        """
        Action personnalisée (Endpoint : POST /api/credits/<id>/changer_statut/)
        Permet de modifier le statut d'une demande.
        Format attendu : {"statut": "APPROUVEE"}
        """
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
        
        # Le déclenchement de la génération d'échéancier sera développé dans la prochaine étape
        return Response(CreditSerializer(credit).data, status=status.HTTP_200_OK)


class PieceJustificativeViewSet(viewsets.ModelViewSet):
    """
    ViewSet permettant l'upload et l'association de justificatifs aux crédits.
    Le format d'envoi requis est le 'form-data' pour supporter les fichiers réels.
    """
    queryset = PieceJustificative.objects.all()
    serializer_class = PieceJustificativeSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Requis pour lire les fichiers envoyés

    def perform_create(self, serializer):
        credit_id = self.request.data.get('credit')
        try:
            credit = Credit.objects.get(id=credit_id)
            # Sécurité : Seul le propriétaire ou un personnel peut charger un fichier sur ce crédit
            if credit.client != self.request.user and self.request.user.role not in ['AGENT', 'ADMIN']:
                raise serializers.ValidationError("Vous n'avez pas l'autorisation d'ajouter des fichiers à ce crédit.")
            serializer.save(credit=credit)
        except Credit.DoesNotExist:
            raise serializers.ValidationError("Le crédit spécifié n'existe pas.")