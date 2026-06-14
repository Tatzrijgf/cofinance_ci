from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class ProduitAssurance(models.Model):
    """Produit d'assurance mobile proposé par COFINANCE CI."""

    class Categorie(models.TextChoices):
        VIE = 'VIE', 'Assurance Vie'
        DECES_INVALIDITE = 'DECES_INVALIDITE', 'Décès-Invalidité'
        SANTE = 'SANTE', 'Santé / Hospitalisation'
        ACCIDENT = 'ACCIDENT', 'Accident'
        MULTIRISQUE = 'MULTIRISQUE', 'Multirisque'

    nom = models.CharField(max_length=120, verbose_name='Nom du produit')
    categorie = models.CharField(max_length=20, choices=Categorie.choices, default=Categorie.VIE)
    description = models.TextField(verbose_name='Description')
    prime_mensuelle = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Prime mensuelle (FCFA)')
    duree_validite_mois = models.PositiveIntegerField(default=12, verbose_name='Durée de validité (mois)')
    couverture_max = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='Couverture maximale (FCFA)')
    actif = models.BooleanField(default=True, verbose_name='Produit actif')

    class Meta:
        verbose_name = "Produit d'assurance"
        verbose_name_plural = "Produits d'assurance"
        ordering = ['categorie', 'nom']

    def __str__(self):
        return f"{self.nom} — {self.prime_mensuelle} FCFA/mois"


class SouscriptionAssurance(models.Model):
    """Souscription d'un client à un produit d'assurance."""

    class Statut(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        EXPIREE = 'EXPIREE', 'Expirée'
        RESILIEE = 'RESILIEE', 'Résiliée'

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='souscriptions_assurance',
        verbose_name='Client',
    )
    produit = models.ForeignKey(
        ProduitAssurance,
        on_delete=models.PROTECT,
        related_name='souscriptions',
        verbose_name='Produit',
    )
    date_debut = models.DateField(default=timezone.now, verbose_name='Date de début')
    date_fin = models.DateField(verbose_name='Date de fin')
    statut = models.CharField(max_length=15, choices=Statut.choices, default=Statut.ACTIVE)
    alerte_expiration_envoyee = models.BooleanField(default=False, verbose_name='Alerte J-15 envoyée')

    class Meta:
        verbose_name = 'Souscription assurance'
        verbose_name_plural = 'Souscriptions assurance'
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.client} → {self.produit.nom} [{self.statut}]"

    def save(self, *args, **kwargs):
        # Calcul automatique de la date de fin si non définie
        if not self.date_fin:
            debut = self.date_debut if self.date_debut else timezone.now().date()
            self.date_fin = debut + timedelta(days=30 * self.produit.duree_validite_mois)
        super().save(*args, **kwargs)

    def actualiser_statut(self):
        """Met à jour le statut selon la date de fin."""
        today = timezone.now().date()
        if self.statut == self.Statut.ACTIVE and today > self.date_fin:
            self.statut = self.Statut.EXPIREE
            self.save()

    @property
    def jours_avant_expiration(self):
        today = timezone.now().date()
        return (self.date_fin - today).days
