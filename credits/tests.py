from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from users.models import CustomUser
from credits.models import Credit, Echeancier
from credits.scoring import CreditScoringService

class CreditsTestCase(TestCase):
    def setUp(self):
        self.client_user = CustomUser.objects.create_user(
            username='client_test',
            email='client_test@example.com',
            password='Password123!',
            telephone='+2250102030400',
            role=CustomUser.Role.CLIENT,
            revenu_mensuel=Decimal('500000.00')
        )
        self.agent_user = CustomUser.objects.create_user(
            username='agent_test',
            email='agent_test@example.com',
            password='Password123!',
            telephone='+2250202030400',
            role=CustomUser.Role.AGENT
        )

    def test_credit_workflow_transitions(self):
        credit = Credit.objects.create(
            client=self.client_user,
            montant=Decimal('1000000.00'),
            duree_mois=12,
            frequence=Credit.Frequence.MENSUEL,
            objet=Credit.Objet.COMMERCE,
            statut=Credit.Statut.SOUMISE
        )
        self.assertEqual(credit.statut, Credit.Statut.SOUMISE)

        # SOUMISE -> EN_ANALYSE
        credit.passer_en_analyse(self.agent_user)
        self.assertEqual(credit.statut, Credit.Statut.EN_ANALYSE)
        self.assertEqual(credit.agent, self.agent_test_agent() if hasattr(self, 'agent_test_agent') else self.agent_user)

        # EN_ANALYSE -> APPROUVEE
        credit.approuver()
        self.assertEqual(credit.statut, Credit.Statut.APPROUVEE)
        self.assertEqual(credit.echeances.count(), 12)

        # APPROUVEE -> DECAISSEE
        credit.decaisser()
        self.assertEqual(credit.statut, Credit.Statut.DECAISSEE)

    def test_credit_scoring(self):
        # Calculate scoring for a request
        score = CreditScoringService.calculate(
            client=self.client_user,
            montant=Decimal('1000000.00'),
            duree_mois=12
        )
        # 500000 monthly income.
        # Monthly repayment: 1M / 12 = ~83k.
        # Ratio mensualite = 83k / 500k = 16.6% <= 20% -> 20 pts
        # Debt ratio = 1M / (500k * 12) = 1M / 6M = 16.6% <= 30% -> 30 pts
        # History: 0 past schedules -> 25 pts
        # Seniority: 0 closed credits -> 2 pts
        # Expected: 20 + 30 + 25 + 2 = 77
        self.assertEqual(score, 77)
