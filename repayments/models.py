from django.db import models
from django.conf import settings
from credits.models import Echeancier


class Paiement(models.Model):
    """Enregistrement d'un paiement sur une échéance de crédit."""

    class ModePaiement(models.TextChoices):
        WAVE = 'WAVE', 'Wave'
        ORANGE_MONEY = 'ORANGE_MONEY', 'Orange Money'
        MTN_MOMO = 'MTN_MOMO', 'MTN MoMo'
        ESPECES = 'ESPECES', 'Espèces'

    echeancier = models.ForeignKey(
        Echeancier,
        on_delete=models.PROTECT,
        related_name='paiements',
        verbose_name='Échéance',
    )
    enregistre_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='Enregistré par',
    )
    capital_paye = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Capital payé (FCFA)',
    )
    penalites_payees = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0,
        verbose_name='Pénalités payées (FCFA)',
    )
    mode_paiement = models.CharField(
        max_length=20,
        choices=ModePaiement.choices,
        default=ModePaiement.ESPECES,
        verbose_name='Mode de paiement',
    )
    reference_transaction = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Référence transaction Mobile Money',
    )
    date_paiement = models.DateTimeField(auto_now_add=True, verbose_name='Date de paiement')
    notes = models.TextField(blank=True, verbose_name='Notes')

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-date_paiement']

    def __str__(self):
        return f"Paiement {self.capital_paye} FCFA — Échéance #{self.echeancier_id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour le statut de l'échéance après chaque paiement
        self.echeancier.actualiser_statut()
        # Notification au client
        try:
            from notifications.models import Notification
            credit = self.echeancier.credit
            Notification.objects.create(
                destinataire=credit.client,
                titre="Remboursement enregistré",
                message=(
                    f"Paiement de {self.capital_paye:,.0f} FCFA enregistré "
                    f"(échéance #{self.echeancier.numero}, mode : {self.get_mode_paiement_display()})."
                ),
            )
        except Exception:
            pass
