import os
import shutil
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from insurance.models import ProduitAssurance, SouscriptionAssurance
from credits.models import Credit, Echeancier
from chat.models import Conversation, Message
from repayments.models import Paiement
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

User = get_user_model()

# Simple valid 1-pixel white PNG

SIMPLE_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
    b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
    b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
    b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
)


class Command(BaseCommand):
    help = "Injecte les données de test initiales de COFINANCE CI dans la base de données."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Nettoyage de la base de données..."))
        Message.objects.all().delete()
        Conversation.objects.all().delete()
        Paiement.objects.all().delete()
        Echeancier.objects.all().delete()
        Credit.objects.all().delete()
        SouscriptionAssurance.objects.all().delete()
        ProduitAssurance.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write("Création des utilisateurs...")
        # Admin
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@cofinance.ci",
            password="AdminSecurise123",
            role="ADMIN",
            first_name="Diallo",
            last_name="Administrateur",
            telephone="0102030405",
            region="ABIDJAN",
        )
        # Agent
        agent = User.objects.create_user(
            username="agent_terrain",
            email="agent@cofinance.ci",
            password="AgentSecurise123",
            role="AGENT",
            first_name="Koné",
            last_name="Ibrahim",
            telephone="0708091011",
            region="BOUAKE",
        )
        # Client
        client = User.objects.create_user(
            username="mory_diop",
            email="mory@example.com",
            password="MotDePasseSecurise123",
            role="CLIENT",
            first_name="Mory",
            last_name="Diop",
            telephone="0506070809",
            region="ABIDJAN",
            revenu_mensuel=Decimal("350000.00"),
            date_naissance=date(1990, 3, 15),
            id_type="CNI",
            id_number="CNI-CI-2990315-009",
        )

        # Attach placeholder KYC documents for demo client
        client.photo.save("demo_photo_mory_diop.png", ContentFile(SIMPLE_PNG), save=False)
        client.id_document_recto.save("demo_cni_recto_mory_diop.png", ContentFile(SIMPLE_PNG), save=False)
        client.id_document_verso.save("demo_cni_verso_mory_diop.png", ContentFile(SIMPLE_PNG), save=False)
        client.save()

        self.stdout.write("Création des produits d'assurance...")
        pa1 = ProduitAssurance.objects.create(
            nom="Assurance Décès-Invalidité",
            description="Couverture complète en cas de décès accidentel ou d'invalidité de l'emprunteur.",
            prime_mensuelle=Decimal("500.00"),
            couverture_max=Decimal("1000000.00"),
            categorie="DECES_INVALIDITE",
            actif=True
        )
        pa2 = ProduitAssurance.objects.create(
            nom="Assurance Vie Simplifiée",
            description="Garantie prévoyance pour protéger votre famille avec une prime mensuelle accessible.",
            prime_mensuelle=Decimal("1000.00"),
            couverture_max=Decimal("2500000.00"),
            categorie="VIE",
            actif=True
        )

        # Souscription active
        SouscriptionAssurance.objects.create(
            client=client,
            produit=pa1,
            date_debut=timezone.now().date(),
            statut="ACTIVE"
        )

        self.stdout.write("Création des crédits et échéances...")
        # Crédit actif (décaissé)
        c1 = Credit.objects.create(
            client=client,
            montant=Decimal("300000.00"),
            taux_interet=Decimal("10.00"),
            duree_mois=3,
            taux_penalite=Decimal("2.00"),
            statut="DECAISSEE",
            score_eligibilite=85,
            date_decaissement=timezone.now().date() - timedelta(days=20)
        )

        today = timezone.now().date()
        Echeancier.objects.create(
            credit=c1, numero=1,
            date_echeance=today - timedelta(days=5),  # En retard de 5 jours
            montant_du=Decimal("110000.00"), statut="A_PAYER"
        )
        Echeancier.objects.create(
            credit=c1, numero=2,
            date_echeance=today + timedelta(days=25),
            montant_du=Decimal("110000.00"), statut="A_PAYER"
        )
        Echeancier.objects.create(
            credit=c1, numero=3,
            date_echeance=today + timedelta(days=55),
            montant_du=Decimal("110000.00"), statut="A_PAYER"
        )

        # Crédit en cours de demande (soumis)
        c2 = Credit.objects.create(
            client=client,
            montant=Decimal("500000.00"),
            taux_interet=Decimal("12.00"),
            duree_mois=6,
            taux_penalite=Decimal("2.00"),
            statut="SOUMISE",
            score_eligibilite=72
        )

        # Crédit en analyse (pour montrer l'agent)
        c3 = Credit.objects.create(
            client=client,
            agent=agent,
            montant=Decimal("150000.00"),
            taux_interet=Decimal("10.00"),
            duree_mois=2,
            taux_penalite=Decimal("2.00"),
            statut="EN_ANALYSE",
            score_eligibilite=78
        )

        self.stdout.write("Création des salons de chat et messages...")
        conv1 = Conversation.objects.create(
            client=client,
            agent=agent,
            sujet="Renseignements sur le taux d'intérêt",
            statut="OUVERTE"
        )
        Message.objects.create(
            conversation=conv1, expediteur=client,
            contenu="Bonjour, je souhaiterais savoir si le taux de 10% s'applique sur toute la durée du crédit.",
        )
        Message.objects.create(
            conversation=conv1, expediteur=agent,
            contenu="Bonjour Mory. Oui, le taux est fixe sur toute la durée de remboursement de votre microcrédit.",
        )

        self.stdout.write(self.style.SUCCESS("\n[OK] Jeu de donnees COFINANCE CI injecte avec succes !"))
        self.stdout.write(self.style.SUCCESS("----------------------------------------------------"))
        self.stdout.write(self.style.SUCCESS("  Compte Admin  : admin / AdminSecurise123"))
        self.stdout.write(self.style.SUCCESS("  Compte Agent  : agent_terrain / AgentSecurise123"))
        self.stdout.write(self.style.SUCCESS("  Compte Client : mory_diop / MotDePasseSecurise123"))
        self.stdout.write(self.style.SUCCESS("----------------------------------------------------"))
