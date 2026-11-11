# 🎓 Tuteur de Maths IA

Tuteur de mathématiques pour lycéens (Seconde → Terminale, spécialité maths).
L'élève s'entraîne par **exercices courts et variés, au niveau des attendus du bac** : **Diagnostic → Entraînement → Bilan**.

## Fonctionnalités

- 🧭 **Trois façons de choisir le thème** : un chapitre du programme, **📸 la photo d'un exercice fait en classe**, ou un thème libre
- 🃏 **Six formats d'exercice** qui alternent (QCM, réponse numérique, vrai ou faux, texte à trous, étapes dans l'ordre, réponse rédigée), **corrigés instantanément par l'app** (ADR 0001)
- 📈 **Figures dessinées par l'app** : solides, triangles, droites et **courbes de fonctions**, avec mesures vérifiées
- 💡 **Indices gradués** puis correction ; question libre au tuteur, qui ne donne pas la réponse
- 🎯 **Orienté DS et bac** : l'élève indique ce qu'il prépare ; énoncés et bilan suivent les attendus du lycée, ton sobre
- 🧭 **Contextes réalistes** tirés des domaines de l'élève (spécialités, projet d'orientation : physique-chimie, économie, informatique…)
- 📈 **Score et jalons** cumulés d'une séance à l'autre (Autonomie, Régularité, Polyvalence, Rebond), sans effets de jeu
- 📸 **Exercice modèle** : le tuteur lit la photo, l'élève vérifie le texte, puis s'entraîne sur des variantes. La photo n'est jamais enregistrée et l'exercice de classe n'est jamais résolu (ADR 0002)
- 👩‍🏫 **Espace prof** : vue par élève (score, jalons, part de réussite sans aide, formats où il bloque) et détail des séances

Vocabulaire du projet : `GLOSSARY.md`. Décisions : `docs/adr/`.

## Installation rapide (local)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."   # en local, les secrets Supabase vont dans .streamlit/secrets.toml
streamlit run app.py
```

## Déploiement Streamlit Cloud + Supabase

### 1. Créer la base Supabase (gratuit)

1. Crée un compte sur [supabase.com](https://supabase.com)
2. Crée un nouveau projet
3. Va dans **SQL Editor** → colle le contenu de `supabase_setup.sql` → **Run**
4. Récupère tes clés dans **Project Settings → API Keys** :
   - `Project URL` → c'est ton `SUPABASE_URL`
   - la clé **secrète** (`sb_secret_…`, ou `service_role` dans *Legacy API Keys*) → c'est ton `SUPABASE_KEY`.
     **Jamais la clé publique** (`anon` / `sb_publishable_…`) : la table n'a aucune politique d'accès public,
     et aucune clé ne doit être écrite dans le code (dépôt public, élèves mineurs).

### 2. Déployer sur Streamlit Cloud

1. Pousse le repo sur GitHub
2. Va sur [share.streamlit.io](https://share.streamlit.io)
3. Connecte le repo, branche `main`, fichier `app.py`
4. Dans **Advanced settings → Secrets**, ajoute :

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "sb_secret_..."
MOT_DE_PASSE_PROF = "ton_mot_de_passe_prof"
```

5. Clique **Deploy**

### 3. Partager

- **URL élève** : partage l'URL Streamlit, l'élève reste sur « Ma séance »
- **URL prof** : même URL, le prof clique sur « Espace prof » et entre le mot de passe

## Structure

```
app.py              # Interface Streamlit : accueil, panneau, espace prof, sauvegarde Supabase
seance.py           # Déroulé d'une séance (diagnostic, entraînement, score, jalons, bilan)
exercices.py        # Contrat d'exercice, correction par le code, calcul vérifié, barème
figures.py          # Figures dessinées par l'app (solides, triangles, droites, courbes)
tuteur.py           # Prompts et appels à l'API Claude
progression.py      # Badges et cumul par élève
modele.py           # Photo d'un exercice de classe : préparation et anti-copie
ecran.py            # Carte d'exercice et bilan
tests/              # pytest (IA et Supabase simulés) : python -m pytest
supabase_setup.sql  # Table sessions (RLS, sans accès public)
```

## Technologies

- **LLM** : API Claude (`claude-haiku-4-5`)
- **Base de données** : Supabase (PostgreSQL) — gratuit jusqu'à 500 Mo
- **Interface** : Streamlit — gratuit sur Streamlit Cloud
