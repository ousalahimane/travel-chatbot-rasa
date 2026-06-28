#  وكالة السفر - Chatbot Rasa (Arabe)

Chatbot intelligent pour une agence de voyage, développé avec **Rasa 3.x**, interagissant en **arabe**, et intégré dans un site web accessible localement.

---

## Structure du Projet


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
