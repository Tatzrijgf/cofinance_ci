from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command
from datetime import timedelta
from decimal import Decimal
from io import StringIO
from users.models import CustomUser
from credits.models import Credit, Echeancier
from repayments.models import Paiement
from insurance.models import ProduitAssurance, SouscriptionAssurance
from notifications.models import Notification

class RepaymentsTestCase(TestCase):
    def setUp(self):
        self.client_user = CustomUser.objects.create_user(
            username='client_rep',
            email='client_rep@example.com',
            password='Password123!',
            telephone='+2250102030402',
            role=CustomUser.Role.CLIENT
        )
        self.agent_user = CustomUser.objects.create_user(
            username='agent_rep',
            email='agent_rep@example.com',
            password='Password123!',
            telephone='+2250202030402',
            role=CustomUser.Role.AGENT
        )
        self.credit = Credit.objects.create(
            client=self.client_user,
            montant=Decimal('100000.00'),
            duree_mois=2,
            frequence=Credit.Frequence.MENSUEL,
            objet=Credit.Objet.COMMERCE,
            statut=Credit.Statut.DECAISSEE
        )
        # Manually create two echeances
        self.echeance1 = Echeancier.objects.create(
            credit=self.credit,
            numero=1,
            date_echeance=timezone.now().date() + timedelta(days=30),
            montant_du=Decimal('55000.00'),
            statut=Echeancier.Statut.A_PAYER
        )
        self.echeance2 = Echeancier.objects.create(
            credit=self.credit,
            numero=2,
            date_echeance=timezone.now().date() + timedelta(days=60),
            montant_du=Decimal('55000.00'),
            statut=Echeancier.Statut.A_PAYER
        )

    def test_partial_and_full_payment(self):
        # 1. Partial payment
        paiement1 = Paiement.objects.create(
            echeancier=self.echeance1,
            enregistre_par=self.agent_user,
            capital_paye=Decimal('20000.00'),
            mode_paiement=Paiement.ModePaiement.WAVE
        )
        self.echeance1.refresh_from_db()
        self.assertEqual(self.echeance1.statut, Echeancier.Statut.PARTIELLEMENT_PAYE)
        self.assertEqual(self.echeance1.total_paye, Decimal('20000.00'))

        # Check notification creation
        self.assertTrue(Notification.objects.filter(destinataire=self.client_user, titre="Remboursement enregistré").exists())

        # 2. Full payment remaining
        paiement2 = Paiement.objects.create(
            echeancier=self.echeance1,
            enregistre_par=self.agent_user,
            capital_paye=Decimal('35000.00'),
            mode_paiement=Paiement.ModePaiement.ESPECES
        )
        self.echeance1.refresh_from_db()
        self.assertEqual(self.echeance1.statut, Echeancier.Statut.PAYE)
        self.assertEqual(self.echeance1.total_paye, Decimal('55000.00'))

    def test_check_reminders_command(self):
        # Setup specific conditions for check_reminders command
        today = timezone.now().date()

        # Echeance 1: J-3 reminder
        self.echeance1.date_echeance = today + timedelta(days=3)
        self.echeance1.save()

        # Echeance 2: J+1 overdue
        self.echeance2.date_echeance = today - timedelta(days=1)
        self.echeance2.save()

        # Souscription: J-15 reminder
        produit = ProduitAssurance.objects.create(
            nom="Assurance Décès",
            categorie=ProduitAssurance.Categorie.DECES_INVALIDITE,
            description="Assurance décès",
            prime_mensuelle=Decimal('1000.00'),
            duree_validite_mois=12,
            couverture_max=Decimal('100000.00')
        )
        souscription = SouscriptionAssurance.objects.create(
            client=self.client_user,
            produit=produit,
            date_debut=today - timedelta(days=345),
            date_fin=today + timedelta(days=15),
            statut=SouscriptionAssurance.Statut.ACTIVE
        )

        # Run command
        out = StringIO()
        call_command('check_reminders', stdout=out)
        output = out.getvalue()

        self.assertIn("Terminé. Rappels envoyés : 1 (J-3), 1 (J+1), 1 (Assurances J-15)", output)

        # Verify notifications are created
        self.assertTrue(Notification.objects.filter(titre="Rappel d'échéance à venir").exists())
        self.assertTrue(Notification.objects.filter(titre="Alerte de retard de paiement").exists())
        self.assertTrue(Notification.objects.filter(titre="Votre assurance expire bientôt").exists())

        # Verify echeance 2 status is updated to EN_RETARD
        self.echeance2.refresh_from_db()
        self.assertEqual(self.echeance2.statut, Echeancier.Statut.EN_RETARD)

        # Verify souscription alert flag is set
        souscription.refresh_from_db()
        self.assertTrue(souscription.alerte_expiration_envoyee)
