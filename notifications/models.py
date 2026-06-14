from django.db import models
from django.conf import settings


class Notification(models.Model):
    """Notification in-app pour un utilisateur."""

    class Type(models.TextChoices):
        CREDIT = 'CREDIT', 'Crédit'
        REMBOURSEMENT = 'REMBOURSEMENT', 'Remboursement'
        ASSURANCE = 'ASSURANCE', 'Assurance'
        ALERTE = 'ALERTE', 'Alerte'
        SYSTEME = 'SYSTEME', 'Système'

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Destinataire',
    )
    titre = models.CharField(max_length=150, verbose_name='Titre')
    message = models.TextField(verbose_name='Message')
    type_notif = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.SYSTEME,
        verbose_name='Type',
    )
    lu = models.BooleanField(default=False, verbose_name='Lu')
    cree_le = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-cree_le']

    def __str__(self):
        return f"[{self.type_notif}] {self.titre} → {self.destinataire}"
