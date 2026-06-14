from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from users.models import CustomUser
from insurance.models import ProduitAssurance, SouscriptionAssurance

class InsuranceTestCase(TestCase):
    def setUp(self):
        self.client_user = CustomUser.objects.create_user(
            username='client_ins',
            email='client_ins@example.com',
            password='Password123!',
            telephone='+2250102030401',
            role=CustomUser.Role.CLIENT
        )
        self.produit = ProduitAssurance.objects.create(
            nom="Assurance Prévoyance",
            categorie=ProduitAssurance.Categorie.VIE,
            description="Couverture prévoyance",
            prime_mensuelle=Decimal('2000.00'),
            duree_validite_mois=12,
            couverture_max=Decimal('500000.00')
        )

    def test_souscription_creation_and_expiration(self):
        # Create subscription
        souscription = SouscriptionAssurance.objects.create(
            client=self.client_user,
            produit=self.produit,
            date_debut=timezone.now().date()
        )
        # Verify automatic end date (date_fin)
        expected_fin = timezone.now().date() + timedelta(days=360)
        self.assertEqual(souscription.date_fin, expected_fin)
        self.assertEqual(souscription.statut, SouscriptionAssurance.Statut.ACTIVE)

        # Test actualiser_statut when active
        souscription.actualiser_statut()
        self.assertEqual(souscription.statut, SouscriptionAssurance.Statut.ACTIVE)

        # Force expire by moving date_fin to past
        souscription.date_fin = timezone.now().date() - timedelta(days=1)
        souscription.save()
        souscription.actualiser_statut()
        self.assertEqual(souscription.statut, SouscriptionAssurance.Statut.EXPIREE)
