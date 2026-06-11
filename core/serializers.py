from decimal import Decimal
from rest_framework import serializers
from .models import CustomUser, Credit, PieceJustificative

# ==========================================
# 1. SÉRIALISATEURS DE GESTION DES UTILISATEURS
# ==========================================

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Sérialisateur pour afficher et mettre à jour le profil de l'utilisateur connecté.
    Le rôle et l'identifiant (username) sont en lecture seule pour des raisons de sécurité.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'telephone', 'region', 'role']
        read_only_fields = ['id', 'username', 'role']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Sérialisateur dédié à l'inscription en libre-service d'un nouveau Client.
    """
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'telephone', 'region']

    def validate_telephone(self, value):
        """
        S'assure que le numéro de téléphone est bien renseigné.
        """
        if not value:
            raise serializers.ValidationError("Le numéro de téléphone est obligatoire.")
        return value

    def create(self, validated_data):
        """
        Enregistre l'utilisateur en base de données et chiffre le mot de passe.
        """
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            telephone=validated_data['telephone'],
            region=validated_data.get('region', None),
            role='CLIENT'  # Tout utilisateur s'inscrivant de lui-même est un client
        )
        return user


# ==========================================
# 2. SÉRIALISATEURS DE GESTION DES CRÉDITS
# ==========================================

class PieceJustificativeSerializer(serializers.ModelSerializer):
    """
    Sérialisateur pour la gestion des pièces justificatives.
    """
    class Meta:
        model = PieceJustificative
        fields = ['id', 'nom_piece', 'fichier', 'charge_le']


class CreditSerializer(serializers.ModelSerializer):
    """
    Sérialisateur principal pour la gestion des demandes de microcrédit.
    Gère le calcul automatique du score lors de la soumission.
    """
    pieces_jointes = PieceJustificativeSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source='client.username', read_only=True)

    class Meta:
        model = Credit
        fields = [
            'id', 'client', 'client_name', 'montant', 'taux_interet', 
            'duree_mois', 'taux_penalite', 'statut', 'score_eligibilite', 
            'date_demande', 'date_mise_a_jour', 'pieces_jointes'
        ]
        read_only_fields = ['id', 'client', 'score_eligibilite', 'statut']

    def create(self, validated_data):
        """
        Calcule automatiquement le score d'éligibilité simplifié au moment de la création.
        """
        montant = validated_data['montant']
        duree = validated_data['duree_mois']
        
        # Algorithme simplifié d'aide à la décision :
        score = 100
        if montant > Decimal('1000000'):  # Plus de 1 000 000 FCFA
            score -= 30
        elif montant > Decimal('500000'):  # Plus de 500 000 FCFA
            score -= 15

        if duree > 12:  # Durée de remboursement supérieure à un an
            score -= 20
        elif duree < 3:  # Moins de 3 mois de remboursement
            score -= 10
            
        validated_data['score_eligibilite'] = max(score, 0)
        validated_data['statut'] = 'SOUMISE'  # On force le statut d'origine

        return super().create(validated_data)