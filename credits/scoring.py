from decimal import Decimal
from django.utils import timezone


class CreditScoringService:
    """
    Service de calcul du score d'éligibilité (0–100).

    Critères :
    ─────────────────────────────────────────────────────────────
    1. Historique de remboursements (40 pts)
       - Taux de remboursements à temps sur crédits passés
    2. Ratio d'endettement (30 pts)
       - Encours total / revenu mensuel × 12
    3. Montant demandé vs revenu (20 pts)
       - Mensualité estimée / revenu mensuel
    4. Ancienneté client (10 pts)
       - Nombre de crédits clôturés sans incident
    ─────────────────────────────────────────────────────────────
    """

    SEUIL_APPROBATION_AUTO = 60  # En dessous → signalé comme risqué

    @classmethod
    def calculate(cls, client, montant: Decimal, duree_mois: int) -> int:
        score = 0

        # ── 1. Historique (40 pts) ────────────────────────────────────────
        score += cls._score_historique(client)

        # ── 2. Ratio endettement (30 pts) ────────────────────────────────
        score += cls._score_endettement(client, montant)

        # ── 3. Ratio mensualité / revenu (20 pts) ────────────────────────
        score += cls._score_mensualite(client, montant, duree_mois)

        # ── 4. Ancienneté (10 pts) ───────────────────────────────────────
        score += cls._score_anciennete(client)

        return max(0, min(100, score))

    # ── Sous-méthodes privées ──────────────────────────────────────────────

    @classmethod
    def _score_historique(cls, client) -> int:
        """40 pts basés sur le taux de ponctualité des paiements passés."""
        from repayments.models import Paiement
        from credits.models import Echeancier

        echeances_passees = Echeancier.objects.filter(
            credit__client=client,
            date_echeance__lt=timezone.now().date(),
        )
        total = echeances_passees.count()
        if total == 0:
            return 25  # Neutre pour un nouveau client

        payees_a_temps = echeances_passees.filter(statut='PAYE').count()
        taux = payees_a_temps / total
        return int(40 * taux)

    @classmethod
    def _score_endettement(cls, client, nouveau_montant: Decimal) -> int:
        """30 pts : ratio encours actuel vs revenu annuel."""
        from credits.models import Credit
        revenu_annuel = client.revenu_mensuel * 12
        if revenu_annuel <= 0:
            return 10  # Revenu non renseigné → score partiel

        encours_actuel = sum(
            c.solde_restant
            for c in Credit.objects.filter(client=client, statut__in=['APPROUVEE', 'DECAISSEE'])
        )
        encours_total = encours_actuel + nouveau_montant
        ratio = encours_total / revenu_annuel

        if ratio <= 0.3:
            return 30
        elif ratio <= 0.5:
            return 20
        elif ratio <= 0.7:
            return 10
        return 0

    @classmethod
    def _score_mensualite(cls, client, montant: Decimal, duree_mois: int) -> int:
        """20 pts : mensualité estimée vs revenu mensuel."""
        if client.revenu_mensuel <= 0 or duree_mois == 0:
            return 10

        mensualite = montant / duree_mois
        ratio = mensualite / client.revenu_mensuel

        if ratio <= 0.2:
            return 20
        elif ratio <= 0.35:
            return 14
        elif ratio <= 0.5:
            return 7
        return 0

    @classmethod
    def _score_anciennete(cls, client) -> int:
        """10 pts : nombre de crédits soldés sans incident."""
        from credits.models import Credit
        nb_solds = Credit.objects.filter(client=client, statut='CLOTUREE').count()
        if nb_solds >= 3:
            return 10
        elif nb_solds >= 1:
            return 5
        return 2
