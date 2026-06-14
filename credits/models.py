from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class Credit(models.Model):
    """Demande de microcrédit avec workflow complet."""

    class Statut(models.TextChoices):
        SOUMISE = 'SOUMISE', 'Soumise'
        EN_ANALYSE = 'EN_ANALYSE', 'En analyse'
        APPROUVEE = 'APPROUVEE', 'Approuvée'
        DECAISSEE = 'DECAISSEE', 'Décaissée'
        REJETEE = 'REJETEE', 'Rejetée'
        CLOTUREE = 'CLOTUREE', 'Clôturée / Soldée'

    class Frequence(models.TextChoices):
        HEBDO = 'HEBDO', 'Hebdomadaire'
        MENSUEL = 'MENSUEL', 'Mensuelle'

    class Objet(models.TextChoices):
        COMMERCE = 'COMMERCE', 'Commerce / Négoce'
        AGRICULTURE = 'AGRICULTURE', 'Agriculture'
        ARTISANAT = 'ARTISANAT', 'Artisanat'
        SANTE = 'SANTE', 'Frais de santé'
        EDUCATION = 'EDUCATION', 'Scolarité / Formation'
        AUTRE = 'AUTRE', 'Autre'

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='credits',
        verbose_name='Client',
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='credits_assignes',
        verbose_name='Agent assigné',
    )
    montant = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Montant demandé (FCFA)')
    taux_interet = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'), verbose_name="Taux d'intérêt (%)")
    duree_mois = models.PositiveIntegerField(verbose_name='Durée (mois)')
    frequence = models.CharField(max_length=10, choices=Frequence.choices, default=Frequence.MENSUEL, verbose_name='Fréquence')
    objet = models.CharField(max_length=20, choices=Objet.choices, default=Objet.AUTRE, verbose_name='Objet du crédit')
    taux_penalite = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.00'), verbose_name='Taux pénalité/jour (%)')
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.SOUMISE, verbose_name='Statut')
    score_eligibilite = models.PositiveIntegerField(null=True, blank=True, verbose_name='Score éligibilité (0-100)')
    date_demande = models.DateTimeField(auto_now_add=True, verbose_name='Date de soumission')
    date_decision = models.DateField(null=True, blank=True, verbose_name='Date décision')
    date_decaissement = models.DateField(null=True, blank=True, verbose_name='Date de décaissement')
    motif_rejet = models.TextField(blank=True, verbose_name='Motif de rejet')

    class Meta:
        verbose_name = 'Crédit'
        verbose_name_plural = 'Crédits'
        ordering = ['-date_demande']

    def __str__(self):
        return f"Crédit #{self.pk} — {self.client} — {self.montant} FCFA [{self.statut}]"

    # ── Workflow transitions ──────────────────────────────────────────────────

    def passer_en_analyse(self, agent):
        """Transition : SOUMISE → EN_ANALYSE."""
        if self.statut != self.Statut.SOUMISE:
            raise ValueError("Seule une demande 'Soumise' peut passer en analyse.")
        self.statut = self.Statut.EN_ANALYSE
        self.agent = agent
        self.save()
        self._notify_client("Votre dossier est en cours d'analyse par nos équipes.")

    def approuver(self):
        """Transition : EN_ANALYSE → APPROUVEE. Génère l'échéancier."""
        if self.statut != self.Statut.EN_ANALYSE:
            raise ValueError("Seule une demande 'En analyse' peut être approuvée.")
        self.statut = self.Statut.APPROUVEE
        self.date_decision = timezone.now().date()
        self.save()
        self.generer_echeancier()
        self._notify_client(f"Félicitations ! Votre crédit de {self.montant:,.0f} FCFA a été approuvé.")

    def rejeter(self, motif=''):
        """Transition : EN_ANALYSE → REJETEE."""
        if self.statut != self.Statut.EN_ANALYSE:
            raise ValueError("Seule une demande 'En analyse' peut être rejetée.")
        self.statut = self.Statut.REJETEE
        self.motif_rejet = motif
        self.date_decision = timezone.now().date()
        self.save()
        self._notify_client(f"Votre demande de crédit a été rejetée. {motif}")

    def decaisser(self):
        """Transition : APPROUVEE → DECAISSEE."""
        if self.statut != self.Statut.APPROUVEE:
            raise ValueError("Seule une demande 'Approuvée' peut être décaissée.")
        self.statut = self.Statut.DECAISSEE
        self.date_decaissement = timezone.now().date()
        self.save()
        self._notify_client("Votre crédit a été décaissé. Les fonds sont disponibles.")

    # ── Génération de l'échéancier ───────────────────────────────────────────

    def generer_echeancier(self):
        """Calcule et sauvegarde les échéances de remboursement."""
        self.echeances.all().delete()

        montant_total = self.montant * (1 + self.taux_interet / 100)

        if self.frequence == self.Frequence.HEBDO:
            nb_echeances = self.duree_mois * 4
            delta = timedelta(weeks=1)
        else:
            nb_echeances = self.duree_mois
            delta = timedelta(days=30)

        montant_echeance = round(montant_total / nb_echeances, 2)
        # Correction d'arrondi sur la dernière échéance
        total_provisoire = montant_echeance * (nb_echeances - 1)
        derniere_echeance = round(montant_total - total_provisoire, 2)

        date_courante = timezone.now().date() + delta
        for i in range(nb_echeances):
            montant_i = derniere_echeance if i == nb_echeances - 1 else montant_echeance
            Echeancier.objects.create(
                credit=self,
                numero=i + 1,
                date_echeance=date_courante,
                montant_du=montant_i,
            )
            date_courante += delta

    def _notify_client(self, message):
        """Crée une notification in-app pour le client."""
        try:
            from notifications.models import Notification
            Notification.objects.create(
                destinataire=self.client,
                titre=f"Crédit #{self.pk} — Mise à jour",
                message=message,
            )
        except Exception:
            pass

    @property
    def montant_total_du(self):
        return self.montant * (1 + self.taux_interet / 100)

    @property
    def solde_restant(self):
        from repayments.models import Paiement
        total_paye = sum(
            p.capital_paye for p in Paiement.objects.filter(echeancier__credit=self)
        )
        return max(Decimal('0'), self.montant_total_du - total_paye)


class Echeancier(models.Model):
    """Ligne d'échéancier liée à un crédit approuvé."""

    class Statut(models.TextChoices):
        A_PAYER = 'A_PAYER', 'À payer'
        PARTIELLEMENT_PAYE = 'PARTIELLEMENT_PAYE', 'Partiellement payé'
        PAYE = 'PAYE', 'Payé'
        EN_RETARD = 'EN_RETARD', 'En retard'

    credit = models.ForeignKey(Credit, on_delete=models.CASCADE, related_name='echeances', verbose_name='Crédit')
    numero = models.PositiveIntegerField(verbose_name='N° échéance')
    date_echeance = models.DateField(verbose_name="Date d'échéance")
    montant_du = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Montant dû (FCFA)')
    statut = models.CharField(max_length=25, choices=Statut.choices, default=Statut.A_PAYER, verbose_name='Statut')

    class Meta:
        verbose_name = 'Échéancier'
        verbose_name_plural = 'Échéanciers'
        ordering = ['credit', 'numero']

    def __str__(self):
        return f"Échéance #{self.numero} du crédit #{self.credit_id} — {self.date_echeance}"

    @property
    def total_paye(self):
        result = self.paiements.aggregate(total=models.Sum('capital_paye'))
        return result['total'] or Decimal('0')

    @property
    def reste_a_payer(self):
        return max(Decimal('0'), self.montant_du - self.total_paye)

    @property
    def penalite_courante(self):
        """Calcule la pénalité de retard si la date est dépassée."""
        today = timezone.now().date()
        if today > self.date_echeance and self.statut not in (self.Statut.PAYE,):
            jours_retard = (today - self.date_echeance).days
            return round(self.reste_a_payer * self.credit.taux_penalite / 100 * jours_retard, 2)
        return Decimal('0')

    def actualiser_statut(self):
        """Met à jour le statut selon les paiements reçus."""
        today = timezone.now().date()
        total = self.total_paye
        if total == 0:
            self.statut = self.Statut.EN_RETARD if today > self.date_echeance else self.Statut.A_PAYER
        elif total >= self.montant_du:
            self.statut = self.Statut.PAYE
        else:
            self.statut = self.Statut.PARTIELLEMENT_PAYE
        self.save()


class DocumentCredit(models.Model):
    """Pièce justificative attachée à une demande de crédit."""

    class TypeDoc(models.TextChoices):
        CNI = 'CNI', "Carte Nationale d'Identité"
        JUSTIF_REVENU = 'JUSTIF_REVENU', 'Justificatif de revenu'
        ATTESTATION = 'ATTESTATION', 'Attestation de résidence'
        PHOTO = 'PHOTO', "Photo d'identité"
        AUTRE = 'AUTRE', 'Autre document'

    credit = models.ForeignKey(Credit, on_delete=models.CASCADE, related_name='documents')
    type_doc = models.CharField(max_length=20, choices=TypeDoc.choices, default=TypeDoc.AUTRE)
    fichier = models.FileField(upload_to='documents/credits/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'

    def __str__(self):
        return f"{self.get_type_doc_display()} — Crédit #{self.credit_id}"
