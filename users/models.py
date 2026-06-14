from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """Utilisateur centralisé avec rôle métier explicite."""

    class Role(models.TextChoices):
        CLIENT = 'CLIENT', 'Client'
        AGENT = 'AGENT', 'Agent de terrain'
        ADMIN = 'ADMIN', 'Administrateur'

    class Region(models.TextChoices):
        ABIDJAN = 'ABIDJAN', 'Abidjan'
        BOUAKE = 'BOUAKE', 'Bouaké'
        KORHOGO = 'KORHOGO', 'Korhogo'
        YAMOUSSOUKRO = 'YAMOUSSOUKRO', 'Yamoussoukro'
        SAN_PEDRO = 'SAN_PEDRO', 'San Pédro'
        DALOA = 'DALOA', 'Daloa'
        MAN = 'MAN', 'Man'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT,
        verbose_name='Rôle',
    )
    telephone = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Téléphone',
    )
    region = models.CharField(
        max_length=20,
        choices=Region.choices,
        blank=True,
        null=True,
        verbose_name='Région',
    )
    revenu_mensuel = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Revenu mensuel (FCFA)',
    )

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name() or self.username} [{self.role}]"

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_agent(self):
        return self.role == self.Role.AGENT

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN
