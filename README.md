# 🌍 وكالة السفر - Chatbot Rasa (Arabe)

Chatbot intelligent pour une agence de voyage, développé avec **Rasa 3.x**, interagissant en **arabe**, et intégré dans un site web accessible localement.

---

## 📁 Structure du Projet

```
travel_chatbot/
├── domain.yml              # Intents, entités, slots, réponses, actions, formulaires
├── config.yml              # Pipeline NLU + Politiques de dialogue
├── endpoints.yml           # Configuration du serveur d'actions et du tracker store
├── credentials.yml         # Canaux de communication (REST, SocketIO)
├── actions.py              # Actions personnalisées (API vols & hôtels)
├── data/
│   ├── nlu.yml             # Données d'entraînement NLU (arabe)
│   ├── stories.yml         # Histoires de conversation
│   └── rules.yml           # Règles de dialogue
├── models/                 # Modèles entraînés (généré après rasa train)
├── website/
│   └── index.html          # Interface web du chatbot
└── README.md
```

---

## ⚙️ Prérequis

```bash
# Python 3.8 ou 3.9 recommandé
python --version

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate   # Linux/Mac
# ou
venv\Scripts\activate      # Windows

# Installer Rasa (versions compatibles)
pip install rasa==3.6.15
pip install rasa-sdk==3.6.2
pip install requests
```

---

## 🚀 Lancement du Chatbot

### 1. Entraîner le modèle
```bash
cd travel_chatbot
rasa train
```

### 2. Démarrer le serveur d'actions (dans un terminal séparé)
```bash
rasa run actions --port 5055
```

### 3. Démarrer le serveur Rasa (dans un autre terminal)
```bash
rasa run --enable-api --cors "*" --port 5005
```

### 4. Lancer le site web
```bash
# Méthode 1: Python
cd website
python -m http.server 8080

# Méthode 2: Node.js
npx serve website -p 8080
```

Ouvrir dans le navigateur : **http://localhost:8080**

---

## 🎯 Fonctionnalités du Chatbot

### Intents supportés (7 au total)

| Intent | Description |
|--------|-------------|
| `greet` | Salutation initiale |
| `goodbye` | Au revoir |
| `book_flight` | Réservation de vol ✈️ |
| `book_hotel` | Réservation d'hôtel 🏨 |
| `select_option` | Sélectionner une offre |
| `change_option` | Modifier les critères |
| `confirm_reservation` | Confirmer la réservation |

### Entités extraites

**Pour les vols :**
- `ville_depart` — Ville de départ
- `ville_destination` — Ville de destination
- `date_depart` — Date de départ
- `date_retour` — Date de retour
- `classe` — Classe (اقتصادية / رجال أعمال / أولى)
- `type_vol` — Type (ذهاب فقط / ذهاب وعودة)

**Pour les hôtels :**
- `ville_hotel` — Ville de l'hôtel
- `categorie_hotel` — Catégorie (3/4/5 نجوم)
- `quartier` — Quartier préféré
- `nombre_personnes` — Nombre de personnes

---

## 🔌 Intégration API Amadeus

L'action `action_search_flights` et `action_search_hotels` dans `actions.py` utilisent l'API Amadeus :

1. Créer un compte sur https://developers.amadeus.com/
2. Créer une application pour obtenir les clés
3. Remplacer dans `actions.py` :
   ```python
   AMADEUS_API_KEY = "VOTRE_CLE_API"
   AMADEUS_API_SECRET = "VOTRE_SECRET_API"
   ```

> **Note :** Si l'API n'est pas configurée, le chatbot utilise des données simulées réalistes.

---

## 💬 Exemple de conversation

```
Utilisateur : مرحبا
Bot : أهلاً وسهلاً! مرحباً بك في وكالة السفر...

Utilisateur : أريد حجز رحلة طيران من الدار البيضاء إلى باريس
Bot : من أي مدينة ستغادر؟ [Formulaire activé]
...
Bot : ✈️ وجدنا لك الرحلات التالية: [3 offres]

Utilisateur : اختر الخيار 1
Bot : ✅ لقد اخترت... هل تريد تأكيد؟

Utilisateur : نعم، أكد الحجز
Bot : 🎉 تم تأكيد حجزك! رقم المرجع: AB12CD56... شكراً لثقتك!
```

---

## 🌐 Déploiement

Pour le déploiement local, l'accès se fait via : **http://localhost:8080**

Pour un déploiement en production, utiliser :
- **Docker Compose** pour orchestrer Rasa + actions server
- **Nginx** comme reverse proxy
- **PostgreSQL** comme tracker store
