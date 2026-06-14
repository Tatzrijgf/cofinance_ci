from django.db import models
from django.conf import settings
from django.utils import timezone


class Conversation(models.Model):
    """Session de support client en temps réel."""

    class Statut(models.TextChoices):
        OUVERTE = 'OUVERTE', 'Ouverte'
        FERMEE = 'FERMEE', 'Fermée'

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chats_client',
        verbose_name='Client',
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='chats_agent',
        verbose_name='Agent support',
    )
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.OUVERTE)
    sujet = models.CharField(max_length=200, blank=True, verbose_name='Sujet')
    cree_le = models.DateTimeField(auto_now_add=True, verbose_name='Créée le')
    ferme_le = models.DateTimeField(null=True, blank=True, verbose_name='Fermée le')

    class Meta:
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-cree_le']

    def __str__(self):
        return f"Conversation #{self.pk} — {self.client} [{self.statut}]"

    def fermer(self):
        self.statut = self.Statut.FERMEE
        self.ferme_le = timezone.now()
        self.save()

    @property
    def dernier_message(self):
        return self.messages.order_by('-envoye_le').first()


class Message(models.Model):
    """Message dans une conversation de support."""

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Conversation',
    )
    expediteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Expéditeur',
    )
    contenu = models.TextField(verbose_name='Contenu')
    envoye_le = models.DateTimeField(auto_now_add=True, verbose_name='Envoyé le')
    lu_par_agent = models.BooleanField(default=False)
    lu_par_client = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['envoye_le']

    def __str__(self):
        return f"[{self.envoye_le.strftime('%H:%M')}] {self.expediteur}: {self.contenu[:50]}"
