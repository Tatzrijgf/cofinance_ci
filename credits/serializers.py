from rest_framework import serializers
from .models import Credit, Echeancier, DocumentCredit


class DocumentCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCredit
        fields = ['id', 'type_doc', 'fichier', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class EcheancierSerializer(serializers.ModelSerializer):
    total_paye = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    reste_a_payer = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    penalite_courante = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Echeancier
        fields = [
            'id', 'credit', 'numero', 'date_echeance',
            'montant_du', 'statut', 'statut_display',
            'total_paye', 'reste_a_payer', 'penalite_courante',
        ]
        read_only_fields = ['id', 'credit', 'numero']


class CreditSerializer(serializers.ModelSerializer):
    client_nom = serializers.SerializerMethodField()
    agent_nom = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    frequence_display = serializers.CharField(source='get_frequence_display', read_only=True)
    objet_display = serializers.CharField(source='get_objet_display', read_only=True)
    echeances = EcheancierSerializer(many=True, read_only=True)
    documents = DocumentCreditSerializer(many=True, read_only=True)
    montant_total_du = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    solde_restant = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Credit
        fields = [
            'id', 'client', 'client_nom', 'agent', 'agent_nom',
            'montant', 'taux_interet', 'duree_mois', 'frequence', 'frequence_display',
            'objet', 'objet_display', 'taux_penalite',
            'statut', 'statut_display', 'score_eligibilite',
            'date_demande', 'date_decision', 'date_decaissement',
            'motif_rejet', 'montant_total_du', 'solde_restant',
            'echeances', 'documents',
        ]
        read_only_fields = [
            'id', 'client', 'statut', 'score_eligibilite',
            'date_demande', 'date_decision', 'date_decaissement',
        ]

    def get_client_nom(self, obj):
        return obj.client.get_full_name() or obj.client.username

    def get_agent_nom(self, obj):
        if obj.agent:
            return obj.agent.get_full_name() or obj.agent.username
        return None


class CreditCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur allégé pour la création par un client."""
    class Meta:
        model = Credit
        fields = ['montant', 'duree_mois', 'frequence', 'objet', 'taux_interet']


class WorkflowActionSerializer(serializers.Serializer):
    """Payload pour les actions de workflow (approbation, rejet, etc.)."""
    motif = serializers.CharField(required=False, allow_blank=True, help_text='Motif de rejet (si applicable)')
