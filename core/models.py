from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser

# ==========================================
# 1. UTILISATEURS & RÔLES
# ==========================================

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('CLIENT', 'Client'),
        ('AGENT', 'Agent de terrain'),
        ('ADMIN', 'Administrateur'),
    ]

    REGION_CHOICES = [
        ('ABIDJAN', 'Abidjan'),
        ('BOUAKE', 'Bouaké'),
        ('KORHOGO', 'Korhogo'),
        ('YAMOUSSOUKRO', 'Yamoussoukro'),
        ('SAN_PEDRO', 'San Pédro'),
    ]

    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='CLIENT')
    telephone = models.CharField(max_length=20, unique=True, help_text="Numéro utilisé pour le Mobile Money")
    region = models.CharField(max_length=30, choices=REGION_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


# ==========================================
# 2. GESTION DES MICROCRÉDITS & JUSTIFICATIFS
# ==========================================

class Credit(models.Model):
    STATUS_CHOICES = [
        ('SOUMISE', 'Soumise'),
        ('EN_ANALYSE', 'En analyse'),
        ('APPROUVEE', 'Approuvée'),
        ('DECAISSEE', 'Décaissée'),
        ('REJETEE', 'Rejetée'),
        ('CLOTUREE', 'Clôturée / Soldée'),
    ]

    client = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='credits_demandes')
    montant = models.DecimalField(max_digits=12, decimal_places=2, help_text="Montant du crédit en FCFA")
    taux_interet = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'), help_text="Taux d'intérêt annuel ou mensuel en %")
    duree_mois = models.PositiveIntegerField(help_text="Durée du remboursement en mois")
    taux_penalite = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.00'), help_text="Taux de pénalité de retard par jour en %")
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SOUMISE')
    score_eligibilite = models.PositiveIntegerField(blank=True, null=True, help_text="Score d'éligibilité calculé automatiquement de 0 à 100")
    date_demande = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Crédit {self.id} de {self.client.username} - {self.montant} FCFA ({self.statut})"


class PieceJustificative(models.Model):
    credit = models.ForeignKey(Credit, on_delete=models.CASCADE, related_name='pieces_jointes')
    fichier = models.FileField(upload_to='justificatifs/')
    nom_piece = models.CharField(max_length=100, help_text="Ex: Pièce d'identité, Justificatif de domicile")
    charge_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom_piece} pour Crédit {self.credit.id}"


# ==========================================
# 3. ÉCHÉANCIER & PAIEMENTS
# ==========================================

class Echeancier(models.Model):
    STATUS_ECHEANCE_CHOICES = [
        ('A_PAYER', 'À payer'),
        ('PAYE', 'Payé'),
        ('EN_RETARD', 'En retard'),
    ]

    credit = models.ForeignKey(Credit, on_delete=models.CASCADE, related_name='echeances')
    date_echeance = models.DateField()
    montant_du = models.DecimalField(max_digits=12, decimal_places=2)
    statut = models.CharField(max_length=15, choices=STATUS_ECHEANCE_CHOICES, default='A_PAYER')

    @property
    def total_paye_capital(self):
        """
        Somme uniquement le capital effectivement remboursé pour cette échéance.
        """
        agg = self.paiements.aggregate(total=models.Sum('capital_paye'))
        return agg['total'] or Decimal('0.00')

    def __str__(self):
        return f"Échéance du {self.date_echeance} pour Crédit {self.credit.id} ({self.montant_du} FCFA)"


class Paiement(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ('ORANGE_MONEY', 'Orange Money'),
        ('WAVE', 'Wave'),
        ('MTN_MOMO', 'MTN MoMo'),
        ('ESPECES', 'Espèces'),
    ]

    echeancier = models.ForeignKey(Echeancier, on_delete=models.PROTECT, related_name='paiements')
    enregistre_par = models.ForeignKey(CustomUser, on_delete=models.PROTECT, limit_choices_to={'role': 'AGENT'})
    capital_paye = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        help_text="Partie du paiement allouée au capital de l'échéance"
    )
    penalites_payees = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'), 
        help_text="Pénalités de retard payées en plus"
    )
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, default='ESPECES')
    date_paiement = models.DateTimeField(auto_now_add=True)

    @property
    def montant_total(self):
        """
        Calcule de manière dynamique la somme de la transaction (Capital + Pénalités).
        """
        return self.capital_paye + self.penalites_payees

    def __str__(self):
        return f"Paiement {self.id} de {self.montant_total} FCFA"


# ==========================================
# 4. ASSURANCES MOBILE
# ==========================================

class ProduitAssurance(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    tarif_mensuel = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nom


class SouscriptionAssurance(models.Model):
    STATUS_ASSURANCE_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIREE', 'Expirée'),
        ('RESILIEE', 'Résiliée'),
    ]

    client = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='assurances_souscrites')
    produit = models.ForeignKey(ProduitAssurance, on_delete=models.PROTECT)
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=15, choices=STATUS_ASSURANCE_CHOICES, default='ACTIVE')

    def __str__(self):
        return f"Assurance {self.produit.nom} - {self.client.username} ({self.statut})"


# ==========================================
# 5. COMMUNICATIONS (CHAT & NOTIFICATIONS)
# ==========================================

class Conversation(models.Model):
    STATUS_CHAT_CHOICES = [
        ('OUVERTE', 'Ouverte'),
        ('FERMEE', 'Fermée'),
    ]

    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conversations_client')
    agent = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations_agent', limit_choices_to={'role': 'ADMIN'})
    statut = models.CharField(max_length=15, choices=STATUS_CHAT_CHOICES, default='OUVERTE')
    cree_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat {self.id} - Client : {self.client.username}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    expediteur = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    contenu = models.TextField()
    envoye_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message de {self.expediteur.username} à {self.envoye_le}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('CHANGEMENT_STATUT_CREDIT', 'Changement statut crédit'),
        ('RAPPEL_ECHEANCE_REMBOUSEMENT', 'Rappel échéance remboursement'),
        ('EXPIRATION_ASSURANCE', 'Expiration assurance imminent'),
    ]

    destinataire = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(max_length=150)
    message = models.TextField()
    type_notification = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    lu = models.BooleanField(default=False)
    cree_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification pour {self.destinataire.username} - Lu : {self.lu}"