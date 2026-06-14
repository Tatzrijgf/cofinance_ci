from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from credits.models import Echeancier
from insurance.models import SouscriptionAssurance
from notifications.models import Notification

class Command(BaseCommand):
    help = "Vérifie les échéances (J-3 / J+1) et assurances (J-15) pour générer des notifications."

    def handle(self, *args, **options):
        self.stdout.write("Analyse des rappels en cours...")
        today = timezone.now().date()

        # 1. Rappel d'échéance à venir (J-3)
        j_moins_3 = today + timedelta(days=3)
        echeances_j3 = Echeancier.objects.filter(
            date_echeance=j_moins_3,
            statut__in=['A_PAYER', 'PARTIELLEMENT_PAYE']
        ).select_related('credit__client')

        count_j3 = 0
        for e in echeances_j3:
            Notification.objects.create(
                destinataire=e.credit.client,
                titre="Rappel d'échéance à venir",
                message=(
                    f"Votre échéance de {e.montant_du:,.0f} FCFA pour le crédit #{e.credit.id} "
                    f"arrive à terme le {e.date_echeance.strftime('%d/%m/%Y')}. "
                    f"Veuillez recharger votre compte Mobile Money ({e.credit.client.telephone})."
                )
            )
            count_j3 += 1

        # 2. Alerte de retard de paiement (J+1)
        j_plus_1 = today - timedelta(days=1)
        echeances_j1 = Echeancier.objects.filter(
            date_echeance=j_plus_1,
            statut__in=['A_PAYER', 'PARTIELLEMENT_PAYE']
        ).select_related('credit__client')

        count_j1 = 0
        for e in echeances_j1:
            Notification.objects.create(
                destinataire=e.credit.client,
                titre="Alerte de retard de paiement",
                message=(
                    f"Votre échéance de {e.montant_du:,.0f} FCFA pour le crédit #{e.credit.id} "
                    f"est en retard depuis le {e.date_echeance.strftime('%d/%m/%Y')}. "
                    f"Des pénalités de retard sont appliquées. Veuillez régulariser au plus vite."
                )
            )
            # Actualise le statut pour qu'il soit explicitement marqué comme EN_RETARD
            e.actualiser_statut()
            count_j1 += 1

        # 3. Expiration d'assurance (J-15)
        j_moins_15 = today + timedelta(days=15)
        assurances_j15 = SouscriptionAssurance.objects.filter(
            date_fin=j_moins_15,
            statut='ACTIVE',
            alerte_expiration_envoyee=False
        ).select_related('client', 'produit')

        count_assurances = 0
        for ass in assurances_j15:
            Notification.objects.create(
                destinataire=ass.client,
                titre="Votre assurance expire bientôt",
                message=(
                    f"Votre souscription à l'offre '{ass.produit.nom}' expire le "
                    f"{ass.date_fin.strftime('%d/%m/%Y')} (dans 15 jours). "
                    f"Pensez à renouveler votre adhésion depuis votre espace client."
                )
            )
            ass.alerte_expiration_envoyee = True
            ass.save()
            count_assurances += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé. Rappels envoyés : {count_j3} (J-3), {count_j1} (J+1), {count_assurances} (Assurances J-15)."
            )
        )
