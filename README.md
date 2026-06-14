# COFINANCE CI - Plateforme Digitale de Microfinance & Assurance Mobile

Ce projet implémente l'intégralité du cahier des charges de COFINANCE CI sous une architecture Django multi-applications hautement modulaire, sécurisée, et dotée d'une interface graphique moderne et fluide.

---

## 📱 Modules Fonctionnels Implémentés

1. **users** : Authentification JWT, rôles (Client, Agent, Admin) et profils de régions.
2. **credits** : Demandes de crédit, calcul automatique d'éligibilité (scoring sur 100 points) et workflow de traitement.
3. **repayments** : Suivi des échéances et enregistrement des paiements (séparation Capital / Pénalités) avec choix des opérateurs de Mobile Money ivoiriens (*Orange Money*, *Wave*, *MTN MoMo*).
4. **insurance** : Catalogue et souscription d'assurance mobile avec calcul de validité.
5. **notifications** : Alertes in-app et notifications de paiement/credits.
6. **dashboard** : Rapport d'agrégation de caisse et de recouvrement en temps réel pour l'admin et l'agent.
7. **chat** : Support client bidirectionnel instantané via WebSockets (Django Channels & Daphne).

---

## 🛠️ Instructions d'Installation & Exécution

### 1. Activer l'Environnement Virtuel (Déjà existant dans le workspace)
Sous Windows :
```powershell
.\env\Scripts\activate
```

### 2. Lancer les Migrations de la Base de Données
```powershell
python manage.py makemigrations users credits repayments insurance notifications chat
python manage.py migrate
```

### 3. Injecter le Jeu de Données de Démonstration (Seeding)
Cette commande crée les comptes utilisateurs pré-configurés, les produits d'assurance, des crédits fictifs à différentes étapes de vie, des échéanciers et des conversations de support :
```powershell
python manage.py seed_db
```

### 4. Lancer le Serveur Daphne (ASGI)
```powershell
python manage.py runserver
```

---

## 👥 Comptes Utilisateurs de Démo (Seeding)

Après l'exécution de `seed_db`, vous pouvez vous connecter sur le portail web à l'adresse **`http://127.0.0.1:8000/login/`** avec les comptes suivants :

| Rôle | Identifiant | Mot de passe | Rôle Métier |
| :--- | :--- | :--- | :--- |
| **Client** | `mory_diop` | `MotDePasseSecurise123` | Client final (Région : Abidjan, Revenu : 350 000 FCFA) |
| **Agent** | `agent_terrain` | `AgentSecurise123` | Agent de recouvrement de terrain (Région : Bouaké) |
| **Admin** | `admin` | `AdminSecurise123` | Administrateur global de la plateforme |

---

## 📡 Documentation API Swagger & Redoc

La plateforme embarque un générateur de schéma OpenAPI (`drf-spectacular`) et expose des documentations interactives :
- **Swagger UI** : `http://127.0.0.1:8000/api/docs/`
- **Redoc** : `http://127.0.0.1:8000/api/redoc/`

---

## 🔔 Commande de Rappel Automatique (Cron/Reminders)

Une commande de gestion personnalisée permet d'envoyer des notifications automatiques (J-3 pour les échéances à venir, J+1 pour les retards avec calcul de pénalités, et J-15 pour l'expiration des contrats d'assurance) :
```powershell
python manage.py check_reminders
```
*Cette commande peut être planifiée via une tâche Cron sous Linux ou le Planificateur de Tâches sous Windows.*

---

## 💬 Test du Chat en Temps Réel (WebSockets)

Pour tester le chat en temps réel :
1. Ouvrez une session de navigation privée (ou un autre navigateur) et connectez-vous avec le compte **Client** (`mory_diop`).
2. Sur votre navigateur principal, connectez-vous avec le compte **Agent** (`agent_terrain`).
3. En tant que **Client**, ouvrez le salon de discussion depuis le tableau de bord.
4. En tant qu'**Agent**, accédez à la liste des discussions actives depuis la barre de navigation et cliquez sur **Rejoindre chat**.
5. Discutez instantanément (vous verrez les indicateurs de frappe et les messages s'afficher sans recharger la page).
