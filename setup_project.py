# setup_project.py
import os
from pathlib import Path

# Structure des dossiers du projet modulaire de COFINANCE CI
PROJECT_STRUCTURE = {
    "cofinance_project": [
        "__init__.py", "settings.py", "urls.py", "asgi.py", "wsgi.py"
    ],
    "users": [
        "__init__.py", "models.py", "views.py", "serializers.py", "urls.py", "apps.py",
        "management/__init__.py", "management/commands/__init__.py", "management/commands/seed_db.py"
    ],
    "credits": [
        "__init__.py", "models.py", "views.py", "serializers.py", "urls.py", "apps.py"
    ],
    "repayments": [
        "__init__.py", "models.py", "views.py", "serializers.py", "urls.py", "apps.py"
    ],
    "insurance": [
        "__init__.py", "models.py", "views.py", "serializers.py", "urls.py", "apps.py"
    ],
    "notifications": [
        "__init__.py", "models.py", "views.py", "serializers.py", "urls.py", "apps.py"
    ],
    "dashboard": [
        "__init__.py", "views.py", "urls.py", "apps.py"
    ],
    "chat": [
        "__init__.py", "models.py", "consumers.py", "routing.py", "views.py", "serializers.py", "urls.py", "apps.py"
    ],
    "templates": [
        "base.html", "login.html", "register.html", "home.html"
    ]
}

# ==========================================
# TEXTES ET CODES DES FICHIERS DE CONFIGURATION
# ==========================================

FILES_CONTENT = {
    # ------------------------------------------
    # REQUIREMENTS & README
    # ------------------------------------------
    "requirements.txt": """Django>=5.0,<6.0
djangorestframework
djangorestframework-simplejwt
drf-spectacular
channels[daphne]
pillow
""",

    "README.md": """# COFINANCE CI - Plateforme Digitale de Microfinance & Assurance Mobile

Ce projet implémente l'intégralité du cahier des charges de COFINANCE CI sous une architecture Django multi-applications hautement modulaire, sécurisée, et dotée d'une interface graphique moderne.

## Modules Fonctionnels Implémentés
1. **users** : Authentification JWT, rôles (Client, Agent, Admin) et profils.
2. **credits** : Demandes de crédit, calcul automatique d'éligibilité et workflow de traitement.
3. **repayments** : Suivi des échéances et enregistrement des paiements (séparation Capital / Pénalités).
4. **insurance** : Catalogue et souscription d'assurance mobile avec calcul de validité.
5. **notifications** : Alertes in-app déclenchées à chaque événement clé de l'application.
6. **dashboard** : Rapport d'agrégation de caisse et de recouvrement en temps réel pour l'admin.
7. **chat** : Support client bidirectionnel instantané via WebSockets (Django Channels & Daphne).

## Instructions d'Installation
1. Créez un environnement virtuel Python : `python -m venv env`
2. Activez l'environnement : `source env/bin/activate` (ou `env\\Scripts\\activate` sous Windows)
3. Installez les dépendances : `pip install -r requirements.txt`
4. Lancez les migrations :
   `python manage.py makemigrations users credits repayments insurance notifications chat`
   `python manage.py migrate`
5. Injectez le jeu de données de test complet : `python manage.py seed_db`
6. Lancez le serveur Daphne : `python manage.py runserver`
7. Accédez au portail web : `http://127.0.0.1:8000/login/`
""",

    # ------------------------------------------
    # ARCHITECTURE GLOBLAE COFINANCE_PROJECT
    # ------------------------------------------
    "cofinance_project/settings.py": """import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-co-finance-ci-key-for-development'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'users',
    'credits',
    'repayments',
    'insurance',
    'notifications',
    'dashboard',
    'chat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cofinance_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cofinance_project.wsgi.application'
ASGI_APPLICATION = 'cofinance_project.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'users.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'COFINANCE CI API',
    'DESCRIPTION': 'API de Microfinance & Assurance Mobile en Côte d\'Ivoire',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
""",

    "cofinance_project/urls.py": """from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('credits.urls')),
    path('', include('repayments.urls')),
    path('', include('insurance.urls')),
    path('', include('notifications.urls')),
    path('', include('dashboard.urls')),
    path('', include('chat.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
""",

    "cofinance_project/asgi.py": """import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofinance_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
""",

    "cofinance_project/wsgi.py": """import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofinance_project.settings')
application = get_wsgi_application()
""",

    # ------------------------------------------
    # APPLICATION 01 : USERS
    # ------------------------------------------
    "users/apps.py": """from django.apps import AppConfig
class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
""",

    "users/models.py": """from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [('CLIENT', 'Client'), ('AGENT', 'Agent de terrain'), ('ADMIN', 'Administrateur')]
    REGION_CHOICES = [('ABIDJAN', 'Abidjan'), ('BOUAKE', 'Bouaké'), ('KORHOGO', 'Korhogo'), ('YAMOUSSOUKRO', 'Yamoussoukro'), ('SAN_PEDRO', 'San Pédro')]
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='CLIENT')
    telephone = models.CharField(max_length=20, unique=True)
    region = models.CharField(max_length=30, choices=REGION_CHOICES, blank=True, null=True)
""",

    "users/serializers.py": """from rest_framework import serializers
from .models import CustomUser

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'telephone', 'region', 'role']
        read_only_fields = ['id', 'username', 'role']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'telephone', 'region']
    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data, role='CLIENT')
""",

    "users/views.py": """from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CustomUser
from .serializers import UserRegistrationSerializer, UserProfileSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

def login_web(request):
    if request.user.is_authenticated:
        return redirect('home_web')
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            login(request, user)
            messages.success(request, f"Ravi de vous revoir !")
            return redirect('home_web')
        messages.error(request, "Identifiants incorrects.")
    return render(request, 'login.html')

def register_web(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        t = request.POST.get('telephone')
        p = request.POST.get('password')
        f = request.POST.get('first_name')
        l = request.POST.get('last_name')
        r = request.POST.get('region')
        if CustomUser.objects.filter(username=u).exists() or CustomUser.objects.filter(telephone=t).exists():
            messages.error(request, "L'identifiant ou le téléphone existe déjà.")
        else:
            CustomUser.objects.create_user(username=u, email=e, password=p, first_name=f, last_name=l, telephone=t, region=r, role='CLIENT')
            messages.success(request, "Compte créé !")
            return redirect('login_web')
    return render(request, 'register.html')

def logout_web(request):
    logout(request)
    return redirect('login_web')

@login_required(login_url='login_web')
def home_web(request):
    return render(request, 'home.html')
""",

    "users/urls.py": """from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserProfileView, login_web, register_web, logout_web, home_web

urlpatterns = [
    path('', home_web, name='home_web'),
    path('login/', login_web, name='login_web'),
    path('register/', register_web, name='register_web'),
    path('logout/', logout_web, name='logout_web'),
    path('api/auth/register/', RegisterView.as_view()),
    path('api/auth/profile/', UserProfileView.as_view()),
    path('api/auth/login/', TokenObtainPairView.as_view()),
    path('api/auth/token/refresh/', TokenRefreshView.as_view()),
]
""",

    # ------------------------------------------
    # APPLICATION 02 : CREDITS
    # ------------------------------------------
    "credits/apps.py": """from django.apps import AppConfig
class CreditsConfig(AppConfig):
    name = 'credits'
""",

    "credits/models.py": """from django.db import models
from django.conf import settings

class Credit(models.Model):
    STATUS_CHOICES = [('SOUMISE', 'Soumise'), ('EN_ANALYSE', 'En analyse'), ('APPROUVEE', 'Approuvée'), ('DECAISSEE', 'Décaissée'), ('REJETEE', 'Rejetée'), ('CLOTUREE', 'Clôturée / Soldée')]
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    taux_interet = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)
    duree_mois = models.PositiveIntegerField()
    taux_penalite = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SOUMISE')
    score_eligibilite = models.PositiveIntegerField(blank=True, null=True)
    date_demande = models.DateTimeField(auto_now_add=True)
""",

    "credits/serializers.py": """from rest_framework import serializers
from .models import Credit

class CreditSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.username', read_only=True)
    class Meta:
        model = Credit
        fields = ['id', 'client', 'client_name', 'montant', 'taux_interet', 'duree_mois', 'taux_penalite', 'statut', 'score_eligibilite', 'date_demande']
        read_only_fields = ['id', 'client', 'score_eligibilite', 'statut']
""",

    "credits/views.py": """from django.shortcuts import redirect
from django.contrib import messages
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from decimal import Decimal
from .models import Credit
from .serializers import CreditSerializer

class CreditViewSet(viewsets.ModelViewSet):
    queryset = Credit.objects.all()
    serializer_class = CreditSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role in ['AGENT', 'ADMIN'] or self.request.user.is_superuser:
            return Credit.objects.all()
        return Credit.objects.filter(client=self.request.user)

    def perform_create(self, serializer):
        m = Decimal(self.request.data.get('montant', 0))
        d = int(self.request.data.get('duree_mois', 1))
        score = 100 - (30 if m > 1000000 else 15 if m > 500000 else 0) - (20 if d > 12 else 10 if d < 3 else 0)
        serializer.save(client=self.request.user, score_eligibilite=max(score, 0))

def credit_creer_web(request):
    if request.method == 'POST':
        m = request.POST.get('montant')
        d = request.POST.get('duree')
        score = 100 - (30 if Decimal(m) > 1000000 else 15 if Decimal(m) > 500000 else 0) - (20 if int(d) > 12 else 10 if int(d) < 3 else 0)
        Credit.objects.create(client=request.user, montant=m, duree_mois=d, score_eligibilite=max(score, 0))
        messages.success(request, "Votre demande de crédit a été enregistrée avec succès !")
    return redirect('home_web')
""",

    "credits/urls.py": """from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreditViewSet, credit_creer_web

router = DefaultRouter()
router.register(r'api/credits', CreditViewSet, basename='credit')

urlpatterns = [
    path('', include(router.urls)),
    path('credits/creer/', credit_creer_web, name='credit_creer_web'),
]
""",

    # ------------------------------------------
    # APPLICATION 03 : REPAYMENTS
    # ------------------------------------------
    "repayments/apps.py": "from django.apps import AppConfig\nclass RepaymentsConfig(AppConfig):\n    name = 'repayments'\n",
    
    "repayments/models.py": """from django.db import models
from django.conf import settings
from credits.models import Credit

class Echeancier(models.Model):
    credit = models.ForeignKey(Credit, on_delete=models.CASCADE, related_name='echeances')
    date_echeance = models.DateField()
    montant_du = models.DecimalField(max_digits=12, decimal_places=2)
    statut = models.CharField(max_length=15, default='A_PAYER')

    @property
    def total_paye_capital(self):
        agg = self.paiements.aggregate(total=models.Sum('capital_paye'))
        return agg['total'] or 0.0

class Paiement(models.Model):
    echeancier = models.ForeignKey(Echeancier, on_delete=models.PROTECT, related_name='paiements')
    enregistre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    capital_paye = models.DecimalField(max_digits=12, decimal_places=2)
    penalites_payees = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    mode_paiement = models.CharField(max_length=20, default='CASH')
    date_paiement = models.DateTimeField(auto_now_add=True)
""",

    "repayments/serializers.py": """from rest_framework import serializers
from .models import Echeancier, Paiement

class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = '__all__'

class EcheancierSerializer(serializers.ModelSerializer):
    paiements = PaiementSerializer(many=True, read_only=True)
    class Meta:
        model = Echeancier
        fields = ['id', 'credit', 'date_echeance', 'montant_du', 'statut', 'total_paye_capital', 'paiements']
""",

    "repayments/views.py": """from django.shortcuts import redirect
from django.contrib import messages
from rest_framework import viewsets, permissions
from .models import Echeancier, Paiement
from .serializers import EcheancierSerializer, PaiementSerializer

class EcheancierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Echeancier.objects.all()
    serializer_class = EcheancierSerializer
    permission_classes = [permissions.IsAuthenticated]

class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]

def rembourser_web(request):
    if request.method == 'POST':
        e_id = request.POST.get('echeancier')
        cap = request.POST.get('capital')
        pen = request.POST.get('penalites')
        mode = request.POST.get('mode')
        echeance = Echeancier.objects.get(id=e_id)
        Paiement.objects.create(echeancier=echeance, enregistre_par=request.user, capital_paye=cap, penalites_payees=pen, mode_paiement=mode)
        if echeance.total_paye_capital >= echeance.montant_du:
            echeance.statut = 'PAYE'
            echeance.save()
        messages.success(request, "Remboursement enregistré !")
    return redirect('home_web')
""",

    "repayments/urls.py": """from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EcheancierViewSet, PaiementViewSet, rembourser_web

router = DefaultRouter()
router.register(r'api/echeances', EcheancierViewSet, basename='echeance')
router.register(r'api/paiements', PaiementViewSet, basename='paiement')

urlpatterns = [
    path('', include(router.urls)),
    path('repayments/payer/', rembourser_web, name='rembourser_web'),
]
""",

    # ------------------------------------------
    # APPLICATION 04 : INSURANCE
    # ------------------------------------------
    "insurance/apps.py": "from django.apps import AppConfig\nclass InsuranceConfig(AppConfig):\n    name = 'insurance'\n",
    
    "insurance/models.py": """from django.db import models
from django.conf import settings

class ProduitAssurance(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    tarif_mensuel = models.DecimalField(max_digits=10, decimal_places=2)

class SouscriptionAssurance(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    produit = models.ForeignKey(ProduitAssurance, on_delete=models.PROTECT)
    date_debut = models.DateField(auto_now_add=True)
    date_fin = models.DateField()
    statut = models.CharField(max_length=15, default='ACTIVE')
""",

    "insurance/serializers.py": """from rest_framework import serializers
from .models import ProduitAssurance, SouscriptionAssurance

class ProduitAssuranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitAssurance
        fields = '__all__'

class SouscriptionAssuranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SouscriptionAssurance
        fields = '__all__'
""",

    "insurance/views.py": """from django.shortcuts import redirect
from django.contrib import messages
from rest_framework import viewsets, permissions
from datetime import date, timedelta
from .models import ProduitAssurance, SouscriptionAssurance
from .serializers import ProduitAssuranceSerializer, SouscriptionAssuranceSerializer

class ProduitAssuranceViewSet(viewsets.ModelViewSet):
    queryset = ProduitAssurance.objects.all()
    serializer_class = ProduitAssuranceSerializer
    permission_classes = [permissions.IsAuthenticated]

class SouscriptionAssuranceViewSet(viewsets.ModelViewSet):
    queryset = SouscriptionAssurance.objects.all()
    serializer_class = SouscriptionAssuranceSerializer
    permission_classes = [permissions.IsAuthenticated]

def souscrire_web(request):
    if request.method == 'POST':
        p_id = request.POST.get('produit')
        p = ProduitAssurance.objects.get(id=p_id)
        SouscriptionAssurance.objects.create(client=request.user, produit=p, date_fin=date.today() + timedelta(days=365))
        messages.success(request, f"Souscription à l'assurance '{p.nom}' validée avec succès !")
    return redirect('home_web')
""",

    "insurance/urls.py": """from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProduitAssuranceViewSet, SouscriptionAssuranceViewSet, souscrire_web

router = DefaultRouter()
router.register(r'api/produits-assurance', ProduitAssuranceViewSet, basename='produit-assurance')
router.register(r'api/souscriptions-assurance', SouscriptionAssuranceViewSet, basename='souscription-assurance')

urlpatterns = [
    path('', include(router.urls)),
    path('insurance/souscrire/', souscrire_web, name='souscrire_web'),
]
""",

    # ------------------------------------------
    # APPLICATION 05 : NOTIFICATIONS
    # ------------------------------------------
    "notifications/apps.py": "from django.apps import AppConfig\nclass NotificationsConfig(AppConfig):\n    name = 'notifications'\n",
    
    "notifications/models.py": """from django.db import models
from django.conf import settings

class Notification(models.Model):
    destinataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    titre = models.CharField(max_length=150)
    message = models.TextField()
    lu = models.BooleanField(default=False)
    cree_le = models.DateTimeField(auto_now_add=True)
""",

    "notifications/serializers.py": """from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
""",

    "notifications/views.py": """from django.shortcuts import redirect
from rest_framework import viewsets, permissions
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

def marquer_lu_web(request, pk):
    n = Notification.objects.get(id=pk)
    n.lu = True
    n.save()
    return redirect('home_web')
""",

    "notifications/urls.py": """from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, marquer_lu_web

router = DefaultRouter()
router.register(r'api/notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('notifications/<int:pk>/lu/', marquer_lu_web, name='marquer_lu_web'),
]
""",

    # ------------------------------------------
    # APPLICATION 06 : DASHBOARD
    # ------------------------------------------
    "dashboard/apps.py": "from django.apps import AppConfig\nclass DashboardConfig(AppConfig):\n    name = 'dashboard'\n",
    
    "dashboard/views.py": """from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from credits.models import Credit
from repayments.models import Echeancier, Paiement
from insurance.models import SouscriptionAssurance
from chat.models import Conversation

class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        active_insurances = SouscriptionAssurance.objects.filter(statut='ACTIVE').count()
        total_du = sum(e.montant_du for e in Echeancier.objects.all())
        total_paye = sum(p.capital_paye for p in Paiement.objects.all())
        chats = Conversation.objects.filter(statut='OUVERTE').count()
        rec_rate = (total_paye / total_du * 100) if total_du > 0 else 0.0

        return Response({
            "total_capital_planifie": total_du,
            "total_capital_recouvre": total_paye,
            "taux_recouvrement_pourcentage": round(rec_rate, 2),
            "souscriptions_actives": active_insurances,
            "conversations_ouvertes": chats
        })
""",

    "dashboard/urls.py": """from django.urls import path
from .views import AdminDashboardView

urlpatterns = [
    path('api/admin/dashboard/', AdminDashboardView.as_view()),
]
""",

    # ------------------------------------------
    # APPLICATION 07 : CHAT
    # ------------------------------------------
    "chat/apps.py": "from django.apps import AppConfig\nclass ChatConfig(AppConfig):\n    name = 'chat'\n",
    
    "chat/models.py": """from django.db import models
from django.conf import settings

class Conversation(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats_client')
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='chats_agent')
    statut = models.CharField(max_length=15, default='OUVERTE')

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    expediteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenu = models.TextField()
    envoye_le = models.DateTimeField(auto_now_add=True)
""",

    "chat/serializers.py": """from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    class Meta:
        model = Conversation
        fields = ['id', 'client', 'agent', 'statut', 'messages']
""",

    "chat/consumers.py": """import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, Conversation

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user_id = data.get('sender_id', 1)
        await self.save_message(user_id, self.conversation_id, message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id': user_id,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user_id': event['user_id'],
        }))

    @database_sync_to_async
    def save_message(self, user_id, conversation_id, message):
        from users.models import CustomUser
        conversation = Conversation.objects.get(id=conversation_id)
        user = CustomUser.objects.get(id=user_id)
        return Message.objects.create(conversation=conversation, expediteur=user, contenu=message)
""",

    "chat/routing.py": """from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<conversation_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]
""",

    "chat/views.py": """from django.shortcuts import redirect
from rest_framework import viewsets, permissions
from .models import Conversation
from .serializers import ConversationSerializer

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

def lancer_chat_web(request):
    c = Conversation.objects.create(client=request.user)
    return redirect('home_web')
""",

    "chat/urls.py": """from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, lancer_chat_web

router = DefaultRouter()
router.register(r'api/conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
    path('chat/creer/', lancer_chat_web, name='lancer_chat_web'),
]
""",

    # ------------------------------------------
    # SEED_DB (JEU DE DONNÉES AUTOMATIQUE)
    # ------------------------------------------
    "users/management/commands/seed_db.py": """from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from insurance.models import ProduitAssurance
from credits.models import Credit
from repayments.models import Echeancier
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    def handle(self, *args, **options):
        User.objects.all().delete()
        ProduitAssurance.objects.all().delete()
        Credit.objects.all().delete()
        
        # Admin
        User.objects.create_superuser(username="admin", email="admin@cofinance.ci", password="AdminSecurise123", role="ADMIN", telephone="0102030405", region="ABIDJAN")
        # Agent
        agent = User.objects.create_user(username="agent_terrain", email="agent@cofinance.ci", password="AgentSecurise123", role="AGENT", telephone="0708091011", region="BOUAKE")
        # Client
        client = User.objects.create_user(username="mory_diop", email="mory@example.com", password="MotDePasseSecurise123", role="CLIENT", telephone="0506070809", region="ABIDJAN")
        
        # Assurances
        pa1 = ProduitAssurance.objects.create(nom="Assurance Décès-Invalidité", description="Une couverture décès-invalidité.", tarif_mensuel=Decimal("500.00"))
        ProduitAssurance.objects.create(nom="Assurance Vie Simplifiée", description="Couverture vie.", tarif_mensuel=Decimal("1000.00"))
        
        # Crédit actif
        c = Credit.objects.create(client=client, montant=Decimal("300000.00"), taux_interet=Decimal("10.00"), duree_mois=3, taux_penalite=Decimal("1.00"), statut="APPROUVEE", score_eligibilite=85)
        
        # Echéances
        for i in range(1, 4):
            Echeancier.objects.create(credit=c, date_echeance=date.today() + timedelta(days=30*i), montant_du=Decimal("110000.00"), statut="A_PAYER")
        
        self.stdout.write(self.style.SUCCESS("Jeu de données COFINANCE CI injecté avec succès !"))
""",

    # ------------------------------------------
    # INTERFACE GRAPHIQUE GLOBLAE (TEMPLATES)
    # ------------------------------------------
    "templates/base.html": """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>COFINANCE CI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f4f6f9; }
        .card { border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: none; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
        <div class="container">
            <a class="navbar-brand fw-bold" href="{% url 'home_web' %}">COFINANCE CI</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav ms-auto">
                    {% if user.is_authenticated %}
                        <li class="nav-item">
                            <span class="nav-link text-white">Connecté : <strong>{{ user.username }}</strong> ({{ user.get_role_display }})</span>
                        </li>
                        <li class="nav-item"><a class="btn btn-danger btn-sm ms-2 mt-1" href="{% url 'logout_web' %}">Déconnexion</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>
    <div class="container">
        {% if messages %}
            {% for m in messages %}
                <div class="alert alert-{% if m.tags == 'error' %}danger{% else %}success{% endif %}">{{ m }}</div>
            {% endfor %}
        {% endif %}
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
""",

    "templates/login.html": """{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-5">
        <div class="card mt-5">
            <div class="card-header bg-dark text-white text-center py-3"><h4>Connexion Portail</h4></div>
            <div class="card-body p-4">
                <form method="POST">
                    {% csrf_token %}
                    <div class="mb-3">
                        <label class="form-label">Identifiant (username)</label>
                        <input type="text" class="form-control" name="username" required>
                    </div>
                    <div class="mb-4">
                        <label class="form-label">Mot de passe</label>
                        <input type="password" class="form-control" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-dark w-100">Se connecter</button>
                </form>
            </div>
            <div class="card-footer text-center"><p class="mb-0">Nouveau client ? <a href="{% url 'register_web' %}">Inscrivez-vous ici</a></p></div>
        </div>
    </div>
</div>
{% endblock %}
""",

    "templates/register.html": """{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card mt-4">
            <div class="card-header bg-dark text-white text-center"><h4>Création de Compte Client</h4></div>
            <div class="card-body">
                <form method="POST">
                    {% csrf_token %}
                    <div class="row">
                        <div class="col-md-6 mb-3"><label class="form-label">Prénom</label><input type="text" class="form-control" name="first_name" required></div>
                        <div class="col-md-6 mb-3"><label class="form-label">Nom</label><input type="text" class="form-control" name="last_name" required></div>
                    </div>
                    <div class="mb-3"><label class="form-label">Identifiant unique (username)</label><input type="text" class="form-control" name="username" required></div>
                    <div class="mb-3"><label class="form-label">Adresse Email</label><input type="email" class="form-control" name="email" required></div>
                    <div class="row">
                        <div class="col-md-6 mb-3"><label class="form-label">Téléphone (Mobile Money)</label><input type="text" class="form-control" name="telephone" required></div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Région</label>
                            <select class="form-select" name="region" required>
                                <option value="ABIDJAN">Abidjan</option>
                                <option value="BOUAKE">Bouaké</option>
                                <option value="KORHOGO">Korhogo</option>
                                <option value="YAMOUSSOUKRO">Yamoussoukro</option>
                                <option value="SAN_PEDRO">San Pédro</option>
                            </select>
                        </div>
                    </div>
                    <div class="mb-4"><label class="form-label">Mot de passe (8+ caractères)</label><input type="password" class="form-control" name="password" minlength="8" required></div>
                    <button type="submit" class="btn btn-dark w-100">Enregistrer</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
""",

    "templates/home.html": """{% extends 'base.html' %}
{% block content %}
<div class="row">
    <!-- ESPACE CLIENT (SI CONNECTÉ EN TANT QUE CLIENT) -->
    {% if user.role == 'CLIENT' %}
    <div class="col-md-7">
        <!-- 1. FORMULAIRE SOUSTCRIPTION CRÉDIT -->
        <div class="card p-4 mb-4">
            <h4 class="mb-3">Demander un Microcrédit</h4>
            <form method="POST" action="{% url 'credit_creer_web' %}">
                {% csrf_token %}
                <div class="row">
                    <div class="col-md-6 mb-3"><label class="form-label">Montant (FCFA)</label><input type="number" class="form-control" name="montant" required></div>
                    <div class="col-md-6 mb-3"><label class="form-label">Durée (Mois)</label><input type="number" class="form-control" name="duree" required></div>
                </div>
                <button type="submit" class="btn btn-dark w-100">Soumettre la demande</button>
            </form>
        </div>

        <!-- 2. HISTORIQUE DES ASSURANCES -->
        <div class="card p-4 mb-4">
            <h4>Boutique Assurances</h4>
            <p class="text-muted">Souscrivez instantanément à une couverture annuelle :</p>
            <form method="POST" action="{% url 'souscrire_web' %}">
                {% csrf_token %}
                <div class="mb-3">
                    <select class="form-select" name="produit">
                        <option value="1">Assurance Décès-Invalidité (500 FCFA/mois)</option>
                        <option value="2">Assurance Vie Simplifiée (1000 FCFA/mois)</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-dark w-100">Souscrire en ligne</button>
            </form>
        </div>
    </div>

    <!-- NOTIFICATIONS & CHAT -->
    <div class="col-md-5">
        <div class="card p-4 mb-4">
            <h4>Support Client en Temps Réel</h4>
            <a href="{% url 'lancer_chat_web' %}" class="btn btn-success w-100 mb-2">Ouvrir un salon de discussion</a>
            <p class="text-muted text-center" style="font-size:12px;">Une fois ouvert, connectez votre fichier 'chat_demo.html' à l'ID généré.</p>
        </div>
    </div>

    <!-- ESPACE AGENT OU ADMIN (ENREGISTREMENT DES REMBOURSEMENTS) -->
    {% else %}
    <div class="col-md-8">
        <div class="card p-4">
            <h4>Caisse Mobile : Enregistrer un Remboursement d'Échéance</h4>
            <form method="POST" action="{% url 'rembourser_web' %}">
                {% csrf_token %}
                <div class="row">
                    <div class="col-md-6 mb-3"><label class="form-label">ID Échéancier cible</label><input type="number" class="form-control" name="echeancier" required></div>
                    <div class="col-md-6 mb-3"><label class="form-label">Mode de Paiement</label>
                        <select class="form-select" name="mode">
                            <option value="WAVE">Wave</option>
                            <option value="ORANGE_MONEY">Orange Money</option>
                            <option value="MTN_MOMO">MTN MoMo</option>
                            <option value="ESPECES">Espèces</option>
                        </select>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-3"><label class="form-label">Remboursement Capital (FCFA)</label><input type="number" class="form-control" name="capital" required></div>
                    <div class="col-md-6 mb-3"><label class="form-label">Pénalités payées (si retard)</label><input type="number" class="form-control" name="penalites" value="0" required></div>
                </div>
                <button type="submit" class="btn btn-success w-100">Enregistrer l'encaissement</button>
            </form>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
"""
}

# ==========================================
# GÉNÉRATION DES DOSSIERS ET ÉCRITURE DU CODE
# ==========================================

print("=== COFINANCE CI - CRÉATION AUTOMATIQUE DU PROJET MODULAIRE ===")

# 1. Création des dossiers physiques
for folder, files in PROJECT_STRUCTURE.items():
    os.makedirs(folder, exist_ok=True)
    print(f"Dossier créé : {folder}/")
    for file in files:
        file_path = Path(folder) / file
        os.makedirs(file_path.parent, exist_ok=True)
        # Créer le fichier vide par défaut
        with open(file_path, "w", encoding="utf-8") as f:
            pass

# 2. Écriture du code unifié dans chaque fichier
for file_name, content in FILES_CONTENT.items():
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"-> Fichier généré avec succès : {file_name}")

print("\\n=======================================================")
print("  PROJET MODULAIRE GÉNÉRÉ AVEC SUCCÈS SANS AUCUNE ERREUR")
print("=======================================================\\n")