from rest_framework import serializers
from .models import ProduitAssurance, SouscriptionAssurance


class ProduitAssuranceSerializer(serializers.ModelSerializer):
    categorie_display = serializers.CharField(source='get_categorie_display', read_only=True)

    class Meta:
        model = ProduitAssurance
        fields = [
            'id', 'nom', 'categorie', 'categorie_display',
            'description', 'prime_mensuelle', 'duree_validite_mois',
            'couverture_max', 'actif',
        ]


class SouscriptionAssuranceSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    produit_prime = serializers.DecimalField(source='produit.prime_mensuelle', max_digits=10, decimal_places=2, read_only=True)
    client_nom = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    jours_avant_expiration = serializers.IntegerField(read_only=True)

    class Meta:
        model = SouscriptionAssurance
        fields = [
            'id', 'client', 'client_nom', 'produit', 'produit_nom', 'produit_prime',
            'date_debut', 'date_fin', 'statut', 'statut_display',
            'jours_avant_expiration',
        ]
        read_only_fields = ['id', 'client', 'date_fin', 'statut']

    def get_client_nom(self, obj):
        return obj.client.get_full_name() or obj.client.username
