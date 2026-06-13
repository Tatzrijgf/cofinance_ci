from decimal import Decimal
from datetime import date, timedelta # Importations nécessaires pour les calculs de dates
from rest_framework import serializers
from .models import CustomUser, Credit, PieceJustificative, Echeancier, Paiement, ProduitAssurance, SouscriptionAssurance

# ==========================================
# 1. UTILISATEURS
# ==========================================

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'telephone', 'region', 'role']
        read_only_fields = ['id', 'username', 'role']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'telephone', 'region']

    def validate_telephone(self, value):
        if not value:
            raise serializers.ValidationError("Le numéro de téléphone est obligatoire.")
        return value

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            telephone=validated_data['telephone'],
            region=validated_data.get('region', None),
            role='CLIENT'
        )
        return user


# ==========================================
# 2. CRÉDITS & DOCUMENTS
# ==========================================

class PieceJustificativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PieceJustificative
        fields = ['id', 'nom_piece', 'fichier', 'charge_le']


class CreditSerializer(serializers.ModelSerializer):
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
        montant = validated_data['montant']
        duree = validated_data['duree_mois']
        
        score = 100
        if montant > Decimal('1000000'):
            score -= 30
        elif montant > Decimal('500000'):
            score -= 15

        if duree > 12:
            score -= 20
        elif duree < 3:
            score -= 10
            
        validated_data['score_eligibilite'] = max(score, 0)
        validated_data['statut'] = 'SOUMISE'

        return super().create(validated_data)


# ==========================================
# 3. ÉCHÉANCIER & PAIEMENTS
# ==========================================

class PaiementSerializer(serializers.ModelSerializer):
    enregistre_par_name = serializers.CharField(source='enregistre_par.username', read_only=True)
    montant_total = serializers.ReadOnlyField()

    class Meta:
        model = Paiement
        fields = [
            'id', 'echeancier', 'enregistre_par', 'enregistre_par_name', 
            'capital_paye', 'penalites_payees', 'montant_total', 'mode_paiement', 'date_paiement'
        ]
        read_only_fields = ['id', 'enregistre_par']


class EcheancierSerializer(serializers.ModelSerializer):
    paiements = PaiementSerializer(many=True, read_only=True)
    total_paye_capital = serializers.ReadOnlyField()

    class Meta:
        model = Echeancier
        fields = ['id', 'credit', 'date_echeance', 'montant_du', 'statut', 'total_paye_capital', 'paiements']
        read_only_fields = ['id', 'credit', 'date_echeance', 'montant_du', 'statut']


# ==========================================
# 4. SÉRIALISATEURS D'ASSURANCE MOBILE (NOUVEAU)
# ==========================================

class ProduitAssuranceSerializer(serializers.ModelSerializer):
    """
    Sérialisateur pour visualiser ou modifier le catalogue des offres d'assurance.
    """
    class Meta:
        model = ProduitAssurance
        fields = ['id', 'nom', 'description', 'tarif_mensuel']


class SouscriptionAssuranceSerializer(serializers.ModelSerializer):
    """
    Sérialisateur pour gérer la souscription active d'un client à une assurance.
    La date de fin et le statut d'origine sont automatisés à la création.
    """
    produit_detail = ProduitAssuranceSerializer(source='produit', read_only=True)
    client_name = serializers.CharField(source='client.username', read_only=True)

    class Meta:
        model = SouscriptionAssurance
        fields = [
            'id', 'client', 'client_name', 'produit', 'produit_detail', 
            'date_debut', 'date_fin', 'statut'
        ]
        read_only_fields = ['id', 'client', 'date_fin', 'statut']

    def create(self, validated_data):
        """
        Calcule automatiquement une validité par défaut de 1 an (365 jours) 
        à partir de la date de début fournie (ou aujourd'hui par défaut).
        """
        date_debut = validated_data.get('date_debut', date.today())
        validated_data['date_debut'] = date_debut
        validated_data['date_fin'] = date_debut + timedelta(days=365)
        validated_data['statut'] = 'ACTIVE'
        return super().create(validated_data)