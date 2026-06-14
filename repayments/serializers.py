from rest_framework import serializers
from .models import Paiement
from credits.models import Echeancier


class PaiementSerializer(serializers.ModelSerializer):
    enregistre_par_nom = serializers.SerializerMethodField()
    mode_display = serializers.CharField(source='get_mode_paiement_display', read_only=True)
    echeance_info = serializers.SerializerMethodField()

    class Meta:
        model = Paiement
        fields = [
            'id', 'echeancier', 'echeance_info',
            'enregistre_par', 'enregistre_par_nom',
            'capital_paye', 'penalites_payees',
            'mode_paiement', 'mode_display',
            'reference_transaction', 'date_paiement', 'notes',
        ]
        read_only_fields = ['id', 'enregistre_par', 'date_paiement']

    def get_enregistre_par_nom(self, obj):
        return obj.enregistre_par.get_full_name() or obj.enregistre_par.username

    def get_echeance_info(self, obj):
        e = obj.echeancier
        return {
            'id': e.id,
            'numero': e.numero,
            'date_echeance': e.date_echeance,
            'montant_du': e.montant_du,
            'credit_id': e.credit_id,
        }


class EcheancierDetailSerializer(serializers.ModelSerializer):
    paiements = PaiementSerializer(many=True, read_only=True)
    total_paye = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    reste_a_payer = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    penalite_courante = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    client_nom = serializers.SerializerMethodField()

    class Meta:
        model = Echeancier
        fields = [
            'id', 'credit', 'numero', 'date_echeance',
            'montant_du', 'statut', 'statut_display',
            'total_paye', 'reste_a_payer', 'penalite_courante',
            'client_nom', 'paiements',
        ]

    def get_client_nom(self, obj):
        return obj.credit.client.get_full_name() or obj.credit.client.username
