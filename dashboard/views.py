from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter

from credits.models import Credit, Echeancier
from repayments.models import Paiement
from insurance.models import SouscriptionAssurance
from chat.models import Conversation
from users.models import CustomUser
from users.permissions import IsAdmin, IsAdminOrAgent


@extend_schema(tags=['Dashboard'])
class AdminDashboardView(APIView):
    """
    Tableau de bord administrateur — agrégations en temps réel.

    Retourne les KPIs clés : volumes, taux de recouvrement, clients, etc.
    """
    permission_classes = [IsAdminOrAgent]

    def get(self, request):
        today = timezone.now().date()

        # ── Crédits par statut ─────────────────────────────────────────────
        credits_par_statut = dict(
            Credit.objects.values('statut').annotate(nb=Count('id')).values_list('statut', 'nb')
        )

        # ── Recouvrement ───────────────────────────────────────────────────
        total_du_agg = Echeancier.objects.aggregate(total=Sum('montant_du'))
        total_du = total_du_agg['total'] or 0

        total_paye_agg = Paiement.objects.aggregate(total=Sum('capital_paye'))
        total_paye = total_paye_agg['total'] or 0

        taux_recouvrement = round(float(total_paye) / float(total_du) * 100, 2) if total_du > 0 else 0.0

        # ── Échéances en retard ────────────────────────────────────────────
        echeances_en_retard = Echeancier.objects.filter(
            date_echeance__lt=today,
            statut__in=['A_PAYER', 'PARTIELLEMENT_PAYE'],
        ).count()

        # ── Assurances ────────────────────────────────────────────────────
        assurances_actives = SouscriptionAssurance.objects.filter(statut='ACTIVE').count()

        # ── Chat ──────────────────────────────────────────────────────────
        conversations_ouvertes = Conversation.objects.filter(statut='OUVERTE').count()

        # ── Utilisateurs ──────────────────────────────────────────────────
        total_clients = CustomUser.objects.filter(role='CLIENT').count()
        total_agents = CustomUser.objects.filter(role='AGENT').count()

        # ── Volumes financiers ────────────────────────────────────────────
        montant_total_engage = Credit.objects.filter(
            statut__in=['APPROUVEE', 'DECAISSEE']
        ).aggregate(total=Sum('montant'))['total'] or 0

        return Response({
            'credits': {
                'soumises': credits_par_statut.get('SOUMISE', 0),
                'en_analyse': credits_par_statut.get('EN_ANALYSE', 0),
                'approuvees': credits_par_statut.get('APPROUVEE', 0),
                'decaissees': credits_par_statut.get('DECAISSEE', 0),
                'rejetees': credits_par_statut.get('REJETEE', 0),
                'cloturees': credits_par_statut.get('CLOTUREE', 0),
                'total': sum(credits_par_statut.values()),
            },
            'recouvrement': {
                'total_planifie_fcfa': float(total_du),
                'total_recouvre_fcfa': float(total_paye),
                'taux_recouvrement_pct': taux_recouvrement,
                'echeances_en_retard': echeances_en_retard,
            },
            'assurances': {
                'souscriptions_actives': assurances_actives,
            },
            'support': {
                'conversations_ouvertes': conversations_ouvertes,
            },
            'utilisateurs': {
                'total_clients': total_clients,
                'total_agents': total_agents,
            },
            'finances': {
                'montant_total_engage_fcfa': float(montant_total_engage),
            },
            'genere_le': timezone.now().isoformat(),
        })


@extend_schema(tags=['Dashboard'])
class AlertesView(APIView):
    """
    Alertes actives : échéances en retard J+1 et à venir J-3.
    Utilisé pour déclencher manuellement ou vérifier les alertes.
    """
    permission_classes = [IsAdminOrAgent]

    def get(self, request):
        from datetime import timedelta
        today = timezone.now().date()
        j_moins_3 = today + timedelta(days=3)
        j_plus_1 = today - timedelta(days=1)

        # Échéances à J-3 (dans 3 jours)
        echeances_j3 = Echeancier.objects.filter(
            date_echeance=j_moins_3,
            statut__in=['A_PAYER', 'PARTIELLEMENT_PAYE'],
        ).select_related('credit__client')

        # Échéances dépassées depuis hier (J+1)
        echeances_retard = Echeancier.objects.filter(
            date_echeance=j_plus_1,
            statut__in=['A_PAYER', 'PARTIELLEMENT_PAYE'],
        ).select_related('credit__client')

        return Response({
            'echeances_j_moins_3': [
                {
                    'id': e.id,
                    'client': e.credit.client.get_full_name() or e.credit.client.username,
                    'telephone': e.credit.client.telephone,
                    'montant_du': float(e.montant_du),
                    'date_echeance': e.date_echeance.isoformat(),
                }
                for e in echeances_j3
            ],
            'echeances_en_retard_j_plus_1': [
                {
                    'id': e.id,
                    'client': e.credit.client.get_full_name() or e.credit.client.username,
                    'telephone': e.credit.client.telephone,
                    'montant_du': float(e.montant_du),
                    'date_echeance': e.date_echeance.isoformat(),
                    'penalite': float(e.penalite_courante),
                }
                for e in echeances_retard
            ],
        })
