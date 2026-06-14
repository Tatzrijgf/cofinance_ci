from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import CustomUser
from .serializers import UserRegistrationSerializer, UserProfileSerializer, UserListSerializer
from .permissions import IsAdmin


# ─── API VIEWS ────────────────────────────────────────────────────────────────

@extend_schema(tags=['Authentification'])
class RegisterView(generics.CreateAPIView):
    """Inscription d'un nouveau client (role=CLIENT assigné automatiquement)."""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=['Authentification'])
class UserProfileView(APIView):
    """Consulter et mettre à jour son profil personnel."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Authentification'])
class UserListView(generics.ListAPIView):
    """Liste de tous les utilisateurs (Admin uniquement)."""
    queryset = CustomUser.objects.all().order_by('-date_joined')
    serializer_class = UserListSerializer
    permission_classes = [IsAdmin]


# ─── WEB VIEWS ────────────────────────────────────────────────────────────────

def login_web(request):
    """Page de connexion web."""
    if request.user.is_authenticated:
        return redirect('home_web')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Bienvenue, {user.get_full_name() or user.username} !")
            return redirect('home_web')
        messages.error(request, "Identifiant ou mot de passe incorrect.")
    return render(request, 'login.html')


def register_web(request):
    """Page d'inscription web."""
    if request.user.is_authenticated:
        return redirect('home_web')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        password = request.POST.get('password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        region = request.POST.get('region', '')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Cet identifiant est déjà utilisé.")
        elif CustomUser.objects.filter(telephone=telephone).exists():
            messages.error(request, "Ce numéro de téléphone est déjà enregistré.")
        elif len(password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
        else:
            CustomUser.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name,
                telephone=telephone, region=region,
                role=CustomUser.Role.CLIENT,
            )
            messages.success(request, "Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
            return redirect('login_web')
    return render(request, 'register.html')


def logout_web(request):
    """Déconnexion."""
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('login_web')


@login_required(login_url='login_web')
def home_web(request):
    """Tableau de bord principal selon le rôle."""
    from credits.models import Credit, Echeancier
    from insurance.models import ProduitAssurance, SouscriptionAssurance
    from notifications.models import Notification
    from chat.models import Conversation

    user = request.user
    context = {'user': user}

    if user.is_client:
        context['my_credits'] = Credit.objects.filter(client=user).order_by('-date_demande')[:5]
        context['my_echeances'] = Echeancier.objects.filter(
            credit__client=user, statut='A_PAYER'
        ).order_by('date_echeance')[:5]
        context['my_insurances'] = SouscriptionAssurance.objects.filter(
            client=user, statut='ACTIVE'
        )
        context['produits'] = ProduitAssurance.objects.all()
        context['my_conversations'] = Conversation.objects.filter(client=user).order_by('-cree_le')[:3]

    elif user.role in ('AGENT', 'ADMIN'):
        context['pending_credits'] = Credit.objects.filter(statut='SOUMISE').order_by('-date_demande')[:10]
        context['analysis_credits'] = Credit.objects.filter(statut='EN_ANALYSE').order_by('-date_demande')[:5]
        context['approved_credits'] = Credit.objects.filter(statut='APPROUVEE').order_by('-date_demande')[:5]
        context['echeances_dues'] = Echeancier.objects.filter(
            statut='A_PAYER'
        ).order_by('date_echeance')[:10]
        context['open_conversations'] = Conversation.objects.filter(
            statut='OUVERTE'
        ).order_by('-cree_le')[:10]
        context['total_credits'] = Credit.objects.count()
        context['total_clients'] = CustomUser.objects.filter(role='CLIENT').count()

    context['notifs_unread'] = Notification.objects.filter(
        destinataire=user, lu=False
    ).count()
    context['recent_notifs'] = Notification.objects.filter(
        destinataire=user
    ).order_by('-cree_le')[:5]

    return render(request, 'home.html', context)
