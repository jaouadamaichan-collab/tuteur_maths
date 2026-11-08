# 🎓 Tuteur de Maths IA

Tuteur intelligent de mathématiques pour lycéens avec parcours personnalisé :  
**Diagnostic → Entraînement ciblé → Bilan**

## Fonctionnalités

- 🔍 **Diagnostic** — 3 exercices pour identifier les acquis
- 🎯 **Entraînement adaptatif** — difficulté ajustée en temps réel
- 📊 **Bilan de séance** — acquis, points à consolider, prochaine étape
- 🗄️ **Historique persistant** — l'élève retrouve ses séances précédentes
- 👩‍🏫 **Tableau de bord prof** — suivi de tous les élèves

## Installation rapide (local)

```bash
pip install -r requirements.txt
export GROQ_API_KEY="gsk_..."
streamlit run app.py
```

## Déploiement Streamlit Cloud + Supabase

### 1. Créer la base Supabase (gratuit)

1. Crée un compte sur [supabase.com](https://supabase.com)
2. Crée un nouveau projet
3. Va dans **SQL Editor** → colle le contenu de `supabase_setup.sql` → **Run**
4. Récupère tes clés dans **Settings → API** :
   - `Project URL` → c'est ton `SUPABASE_URL`
   - `anon public` key → c'est ton `SUPABASE_KEY`

### 2. Déployer sur Streamlit Cloud

1. Pousse le repo sur GitHub
2. Va sur [share.streamlit.io](https://share.streamlit.io)
3. Connecte le repo, branche `main`, fichier `app.py`
4. Dans **Advanced settings → Secrets**, ajoute :

```toml
GROQ_API_KEY = "gsk_ta_clé_groq"
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "eyJ..."
MOT_DE_PASSE_PROF = "ton_mot_de_passe_prof"
```

5. Clique **Deploy**

### 3. Partager

- **URL élève** : partage l'URL Streamlit, l'élève choisit la page "Séance élève"
- **URL prof** : même URL, le prof clique sur "Tableau de bord prof" et entre le mot de passe

## Structure

```
tuteur-maths/
├── app.py                 # Application principale
├── requirements.txt       # Dépendances Python
├── supabase_setup.sql     # Script de création de la table
├── .gitignore
├── .streamlit/
│   └── config.toml        # Thème Streamlit
└── README.md
```

## Technologies

- **LLM** : Groq (qwen/qwen3-32b) — gratuit et rapide
- **Base de données** : Supabase (PostgreSQL) — gratuit jusqu'à 500 Mo
- **Interface** : Streamlit — gratuit sur Streamlit Cloud
