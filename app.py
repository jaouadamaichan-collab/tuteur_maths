#!/usr/bin/env python3
"""
🎓 Tuteur de Maths IA — Application Streamlit + Supabase
Parcours personnalisé : diagnostic → entraînement → bilan
Avec suivi persistant et tableau de bord professeur.

Nécessite :
  pip install streamlit groq supabase
  Configurer les secrets Streamlit (voir README)
  streamlit run app.py
"""

import streamlit as st
import json
import os
from datetime import datetime
from groq import Groq

# ════════════════════════════════════════════════════════════
# ⚙️  CONFIGURATION
# ════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """# 1. Rôle et objectif
Tu es un tuteur de mathématiques pour lycéens, intégré à une application
Streamlit. Tu aides l'élève à identifier ses acquis, comprendre ses erreurs
et progresser grâce à un parcours personnalisé :
diagnostic → entraînement ciblé → vérification → bilan.

# 2. Informations de départ
Utilise les informations fournies par l'application : classe, pays ou
programme scolaire, chapitre, objectif, temps disponible et historique.

Si des informations indispensables manquent, demande uniquement celles
qui permettent de commencer, en trois questions courtes maximum.
Priorité : classe, chapitre et objectif.
Ne suppose pas le programme à partir de la langue de l'élève.
Si le chapitre est inconnu, aide l'élève à choisir un point de départ.

# 3. Diagnostic initial
Commence par un diagnostic court de trois exercices, présentés un à un :
un prérequis, une application directe et une question de compréhension.
Adapte-les aux informations disponibles et ajuste la difficulté si nécessaire.
Attends la réponse de l'élève avant de poursuivre.

Présente tes conclusions comme provisoires : une seule erreur ne suffit
pas à établir une lacune, et une seule réussite ne prouve pas la maîtrise.

# 4. Personnalisation de l'entraînement
Choisis chaque nouvel exercice à partir des réponses précédentes.
Travaille une difficulté prioritaire à la fois.
En cas de blocage, simplifie ou reviens au prérequis concerné.
En cas de réussites autonomes répétées, augmente progressivement la difficulté.
Varie les questions pour vérifier la compréhension, pas seulement la mémorisation.

# 5. Aide et correction
N'affiche pas la solution avec l'énoncé.
Si l'élève bloque, propose d'abord un indice ciblé, puis une aide plus explicite.
S'il demande directement le corrigé, fournis-le sans le faire attendre.

Après une réponse, indique brièvement ce qui est juste, l'erreur précise
éventuelle et la prochaine étape.
Si le raisonnement manque et qu'il est nécessaire pour évaluer la réponse,
demande une justification courte au lieu de deviner l'origine de l'erreur.
Distingue une réussite autonome d'une réussite obtenue avec aide.

# 6. Rigueur mathématique
Vérifie les énoncés, calculs et corrigés avant de les afficher.
Précise les conditions de validité utiles et accepte les méthodes correctes
différentes de celle que tu avais envisagée.
Si une donnée manque ou si un énoncé est ambigu, signale-le.
Ne présente pas une réponse incertaine comme une certitude.

# 7. Ton et concision
Adopte un ton bienveillant, direct et respectueux, sans infantiliser l'élève.
Valorise une démarche ou un progrès précis plutôt qu'un compliment générique.
Limite les messages ordinaires à 120 mots, hors énoncé et formules.
Développe davantage uniquement pour une correction nécessaire
ou à la demande de l'élève.

# 8. Format des échanges
Utilise du Markdown simple et du LaTeX pour les expressions mathématiques.
Affiche uniquement les rubriques utiles :
« Objectif », « Exercice », « Retour » ou « Prochaine étape ».
Ne répète pas toutes les rubriques à chaque message.
Ne propose qu'un nouvel exercice à la fois et termine par une action claire.

# 9. Suivi de la progression
Après trois exercices d'entraînement, à la fin du temps disponible
ou à la demande de l'élève, fournis un bilan de cinq lignes maximum :
- notion travaillée ;
- acquis observés ;
- point à consolider ;
- degré d'autonomie ;
- prochaine étape recommandée.

Appuie ce bilan uniquement sur les réponses réellement observées.
Ne conclus pas à une maîtrise durable à partir d'une seule séance.

# 10. Limites liées à l'application
Utilise uniquement l'historique et les données effectivement transmis.
Si un bilan antérieur existe, reprends à partir de celui-ci et vérifie
brièvement les acquis avant de poursuivre.
Ne prétends jamais avoir sauvegardé une progression ou modifié l'interface
sans confirmation d'un outil de l'application.
Si aucun historique n'est disponible, indique-le simplement et commence
un nouveau diagnostic."""

CHAPITRES = {
    "Seconde": [
        "Nombres et calculs",
        "Équations et inéquations",
        "Fonctions (généralités)",
        "Fonctions de référence",
        "Géométrie repérée",
        "Statistiques et probabilités",
        "Algorithmique et programmation",
    ],
    "Première (Spé Maths)": [
        "Second degré",
        "Suites numériques",
        "Dérivation",
        "Fonction exponentielle",
        "Trigonométrie",
        "Produit scalaire",
        "Probabilités conditionnelles",
    ],
    "Terminale (Spé Maths)": [
        "Limites et continuité",
        "Dérivation et convexité",
        "Logarithme népérien",
        "Primitives et intégrales",
        "Suites (convergence, récurrence)",
        "Probabilités (lois continues)",
        "Géométrie dans l'espace",
    ],
    "Autre": ["Je préciserai dans le chat"],
}

PAYS_PROGRAMMES = [
    "France (Éducation Nationale)",
    "Belgique",
    "Suisse",
    "Canada (Québec)",
    "Maroc",
    "Tunisie",
    "Algérie",
    "Côte d'Ivoire",
    "Sénégal",
    "Autre (je préciserai)",
]

# Mot de passe pour accéder au tableau de bord prof
MOT_DE_PASSE_PROF = "prof2024"


# ════════════════════════════════════════════════════════════
# 🗄️  SUPABASE — Persistance des données
# ════════════════════════════════════════════════════════════

def get_supabase():
    """Initialise le client Supabase depuis les secrets Streamlit ou les env vars."""
    try:
        from supabase import create_client
    except ImportError:
        st.error("❌ `pip install supabase` requis pour la persistance.")
        return None

    # --- Lecture des secrets ---
    url = ""
    key = ""

    # 1) Essayer st.secrets (Streamlit Cloud)
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass

    # 2) Fallback sur les variables d'environnement (local)
    if not url:
        url = os.environ.get("SUPABASE_URL", "")
    if not key:
        key = os.environ.get("SUPABASE_KEY", "")

    if not url or not key:
        return None

    # --- Connexion ---
    try:
        client = create_client(url, key)
        return client
    except Exception as e:
        st.error(f"❌ Erreur connexion Supabase : {e}")
        return None


def sauvegarder_session_db(profil, messages, nb_exercices, phase, bilan=""):
    """Sauvegarde une séance dans Supabase."""
    sb = get_supabase()
    if not sb:
        return False

    msgs = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
        if m["role"] != "system"
    ]

    data = {
        "eleve_nom":    profil.get("nom", "Élève"),
        "classe":       profil.get("classe", ""),
        "programme":    profil.get("programme", ""),
        "chapitre":     profil.get("chapitre", ""),
        "objectif":     profil.get("objectif", ""),
        "temps":        profil.get("temps", ""),
        "nb_exercices": nb_exercices,
        "nb_echanges":  len([m for m in msgs if m["role"] == "user"]),
        "phase_finale": phase,
        "bilan":        bilan,
        "messages":     json.dumps(msgs, ensure_ascii=False),
        "date_session": datetime.now().isoformat(),
    }

    try:
        sb.table("sessions").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Erreur sauvegarde : {str(e)[:120]}")
        return False


def charger_sessions_db(nom):
    """Charge les séances précédentes d'un élève depuis Supabase."""
    sb = get_supabase()
    if not sb:
        return []

    try:
        resp = (
            sb.table("sessions")
            .select("*")
            .eq("eleve_nom", nom)
            .order("date_session", desc=True)
            .limit(10)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def charger_tous_eleves_db():
    """Charge la liste de tous les élèves et leurs stats (vue prof)."""
    sb = get_supabase()
    if not sb:
        return []

    try:
        resp = (
            sb.table("sessions")
            .select("eleve_nom, classe, chapitre, nb_exercices, phase_finale, bilan, date_session")
            .order("date_session", desc=True)
            .limit(200)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def resume_historique(sessions):
    """Résume l'historique pour l'injecter dans le contexte du LLM."""
    if not sessions:
        return ""
    lignes = ["\n--- HISTORIQUE DES SÉANCES PRÉCÉDENTES ---"]
    for s in sessions[:3]:
        date = str(s.get("date_session", "?"))[:10]
        chapitre = s.get("chapitre", "?")
        bilan = s.get("bilan", "")
        phase = s.get("phase_finale", "")
        nb_ex = s.get("nb_exercices", 0)
        lignes.append(f"\n[{date}] Chapitre : {chapitre} · {nb_ex} exercices · Phase : {phase}")
        if bilan:
            lignes.append(f"Bilan : {bilan}")
    lignes.append("--- FIN HISTORIQUE ---\n")
    return "\n".join(lignes)


# ════════════════════════════════════════════════════════════
# 🤖  APPEL LLM (Groq)
# ════════════════════════════════════════════════════════════

def get_groq_key():
    """Récupère la clé Groq depuis secrets, env ou session."""
    if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    return os.environ.get("GROQ_API_KEY", st.session_state.get("api_key", ""))


def appel_tuteur(messages):
    """Appel à Groq avec le contexte complet."""
    api_key = get_groq_key()
    if not api_key:
        return "⚠️ Clé API Groq manquante. Configure-la dans la barre latérale."

    client = Groq(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=messages,
            temperature=0.6,
            max_tokens=2048,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Erreur Groq : {str(e)[:200]}"


# ════════════════════════════════════════════════════════════
# 🏗️  CONSTRUCTION DU CONTEXTE
# ════════════════════════════════════════════════════════════

def construire_contexte_initial(profil, historique_txt=""):
    """Construit le message système avec le profil et l'historique."""
    infos = (
        f"\n--- PROFIL ÉLÈVE ---\n"
        f"Nom/Pseudo : {profil.get('nom', 'non renseigné')}\n"
        f"Classe : {profil.get('classe', 'non renseignée')}\n"
        f"Programme : {profil.get('programme', 'non renseigné')}\n"
        f"Chapitre : {profil.get('chapitre', 'non renseigné')}\n"
        f"Objectif : {profil.get('objectif', 'non renseigné')}\n"
        f"Temps disponible : {profil.get('temps', 'non renseigné')}\n"
        f"--- FIN PROFIL ---\n"
    )
    return SYSTEM_PROMPT + infos + historique_txt


# ════════════════════════════════════════════════════════════
# 📊  TABLEAU DE BORD PROFESSEUR
# ════════════════════════════════════════════════════════════

def afficher_dashboard_prof():
    """Page tableau de bord pour le professeur."""
    st.markdown("## 📊 Tableau de bord — Suivi des élèves")

    sessions = charger_tous_eleves_db()

    if not sessions:
        st.info("Aucune séance enregistrée pour le moment.")
        return

    # ── Statistiques globales ─────────────────────────────────
    eleves_uniques = list({s["eleve_nom"] for s in sessions})
    total_exercices = sum(s.get("nb_exercices", 0) for s in sessions)

    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Élèves", len(eleves_uniques))
    col2.metric("📝 Séances", len(sessions))
    col3.metric("🧮 Exercices total", total_exercices)

    st.divider()

    # ── Filtre par élève ──────────────────────────────────────
    eleve_filtre = st.selectbox(
        "🔍 Filtrer par élève",
        ["Tous"] + sorted(eleves_uniques),
    )

    if eleve_filtre != "Tous":
        sessions = [s for s in sessions if s["eleve_nom"] == eleve_filtre]

    # ── Tableau des séances ───────────────────────────────────
    st.markdown("### 📋 Historique des séances")

    for s in sessions:
        date = str(s.get("date_session", ""))[:16].replace("T", " à ")
        nom = s.get("eleve_nom", "?")
        classe = s.get("classe", "?")
        chapitre = s.get("chapitre", "?")
        nb_ex = s.get("nb_exercices", 0)
        phase = s.get("phase_finale", "?")
        bilan = s.get("bilan", "")

        phase_emoji = {"diagnostic": "🔍", "entrainement": "🎯", "bilan": "📊"}.get(phase, "📝")

        with st.expander(f"{phase_emoji} **{nom}** — {chapitre} · {date}"):
            col_a, col_b, col_c = st.columns(3)
            col_a.write(f"**Classe :** {classe}")
            col_b.write(f"**Exercices :** {nb_ex}")
            col_c.write(f"**Phase finale :** {phase}")

            if bilan:
                st.markdown("**Bilan :**")
                st.info(bilan)
            else:
                st.caption("Pas de bilan enregistré pour cette séance.")

    # ── Vue par élève — progression ───────────────────────────
    if eleve_filtre != "Tous" and len(sessions) >= 2:
        st.divider()
        st.markdown(f"### 📈 Progression de {eleve_filtre}")

        chapitres_vus = []
        for s in reversed(sessions):
            ch = s.get("chapitre", "?")
            nb = s.get("nb_exercices", 0)
            date = str(s.get("date_session", ""))[:10]
            chapitres_vus.append({"Date": date, "Chapitre": ch, "Exercices": nb})

        st.table(chapitres_vus)


# ════════════════════════════════════════════════════════════
# 🎨  INTERFACE STREAMLIT — PRINCIPALE
# ════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="🎓 Tuteur Maths IA",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # CSS
    st.markdown("""
    <style>
    .main-title { text-align: center; padding: 0.5rem 0 0.2rem 0; }
    .main-title h1 { font-size: 2rem; margin-bottom: 0; }
    .main-title p { color: #888; font-size: 0.95rem; }
    .phase-badge {
        display: inline-block; padding: 0.3rem 0.8rem; border-radius: 1rem;
        font-weight: 600; font-size: 0.85rem; margin-bottom: 0.5rem;
    }
    .phase-diagnostic { background: #fef3c7; color: #92400e; }
    .phase-entrainement { background: #dbeafe; color: #1e40af; }
    .phase-bilan { background: #d1fae5; color: #065f46; }
    .stat-card {
        background: #f8f9fa; border-radius: 0.6rem; padding: 0.8rem;
        text-align: center; border: 1px solid #e9ecef;
    }
    .stat-card .number { font-size: 1.6rem; font-weight: 700; color: #2563eb; }
    .stat-card .label { font-size: 0.8rem; color: #6b7280; }
    </style>
    """, unsafe_allow_html=True)

    # ── Initialisation session state ──────────────────────────
    defaults = {
        "messages": [],
        "session_active": False,
        "profil": {},
        "nb_exercices": 0,
        "phase": "config",
        "debut_session": None,
        "page": "tuteur",
        "prof_auth": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Vérifier si Supabase est configuré
    sb_test = get_supabase()
    sb_ok = sb_test is not None

    # ══════════════════════════════════════════════════════════
    # 📚  BARRE LATÉRALE
    # ══════════════════════════════════════════════════════════

    with st.sidebar:
        st.markdown("## ⚙️ Configuration")

        # Clé API Groq
        if not get_groq_key():
            api_key = st.text_input(
                "🔑 Clé API Groq", type="password",
                value=st.session_state.get("api_key", ""),
                help="Obtiens une clé gratuite sur console.groq.com",
            )
            if api_key:
                st.session_state.api_key = api_key
        else:
            st.success("🔑 API Groq OK")

        # Statut Supabase
        if sb_ok:
            st.success("🗄️ Base de données OK")
        else:
            # Debug : afficher les clés détectées
            _dbg_url = ""
            _dbg_key = ""
            try:
                _dbg_url = st.secrets["SUPABASE_URL"]
            except Exception as _e1:
                _dbg_url = f"ERREUR: {_e1}"
            try:
                _dbg_key = st.secrets["SUPABASE_KEY"]
            except Exception as _e2:
                _dbg_key = f"ERREUR: {_e2}"
            st.warning("🗄️ Supabase non configuré — mode local")
            with st.expander("🔍 Debug Supabase"):
                st.text(f"URL: {_dbg_url[:30]}..." if len(str(_dbg_url)) > 30 else f"URL: {_dbg_url}")
                st.text(f"KEY: {_dbg_key[:20]}..." if len(str(_dbg_key)) > 20 else f"KEY: {_dbg_key}")
                try:
                    st.text(f"Secrets dispo: {list(st.secrets.keys())}")
                except Exception as _e3:
                    st.text(f"st.secrets inaccessible: {_e3}")

        st.divider()

        # Navigation
        page = st.radio(
            "📍 Navigation",
            ["🧑‍🎓 Séance élève", "📊 Tableau de bord prof"],
            index=0 if st.session_state.page == "tuteur" else 1,
            label_visibility="collapsed",
        )
        st.session_state.page = "tuteur" if "élève" in page else "prof"

        # ── Profil élève (seulement en mode tuteur) ───────────
        if st.session_state.page == "tuteur":
            st.divider()
            st.markdown("## 👤 Profil élève")

            nom = st.text_input("Nom / Pseudo", placeholder="Ex: Sarah")
            programme = st.selectbox("📍 Programme scolaire", PAYS_PROGRAMMES)
            classe = st.selectbox("📚 Classe", list(CHAPITRES.keys()))
            chapitres_dispo = CHAPITRES.get(classe, ["Autre"])
            chapitre = st.selectbox("📖 Chapitre", chapitres_dispo)
            objectif = st.text_area(
                "🎯 Objectif de la séance",
                placeholder="Ex: Comprendre la dérivation d'un produit",
                height=68,
            )
            temps = st.select_slider(
                "⏱️ Temps disponible",
                options=["15 min", "30 min", "45 min", "1h", "1h30", "2h"],
                value="30 min",
            )

            # Historique
            if sb_ok and nom:
                sessions_passees = charger_sessions_db(nom)
                if sessions_passees:
                    st.info(f"📂 {len(sessions_passees)} séance(s) précédente(s)")
            else:
                sessions_passees = []

            st.divider()

            # Boutons
            col1, col2 = st.columns(2)
            with col1:
                btn_start = st.button(
                    "▶️ Démarrer" if not st.session_state.session_active else "🔄 Relancer",
                    use_container_width=True, type="primary",
                )
            with col2:
                btn_bilan = st.button(
                    "📊 Bilan", use_container_width=True,
                    disabled=not st.session_state.session_active,
                )

            if st.session_state.session_active:
                if st.button("💾 Sauvegarder", use_container_width=True):
                    if sb_ok:
                        ok = sauvegarder_session_db(
                            st.session_state.profil,
                            st.session_state.messages,
                            st.session_state.nb_exercices,
                            st.session_state.phase,
                        )
                        if ok:
                            st.success("✅ Séance sauvegardée !")
                    else:
                        st.warning("Supabase non configuré.")

                if st.button("🗑️ Nouvelle séance", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.session_active = False
                    st.session_state.nb_exercices = 0
                    st.session_state.phase = "config"
                    st.session_state.debut_session = None
                    st.rerun()
        else:
            btn_start = False
            btn_bilan = False
            nom = ""
            classe = ""
            programme = ""
            chapitre = ""
            objectif = ""
            temps = "30 min"
            sessions_passees = []

    # ══════════════════════════════════════════════════════════
    # 📊  PAGE PROFESSEUR
    # ══════════════════════════════════════════════════════════

    if st.session_state.page == "prof":
        st.markdown("""
        <div class="main-title">
            <h1>🎓 Tuteur de Maths IA</h1>
            <p>Tableau de bord professeur</p>
        </div>
        """, unsafe_allow_html=True)

        if not sb_ok:
            st.warning("Le tableau de bord nécessite Supabase. Voir le README pour la configuration.")
            return

        # Authentification simple
        if not st.session_state.prof_auth:
            mdp_attendu = (
                st.secrets.get("MOT_DE_PASSE_PROF", MOT_DE_PASSE_PROF)
                if hasattr(st, "secrets") and "MOT_DE_PASSE_PROF" in st.secrets
                else os.environ.get("MOT_DE_PASSE_PROF", MOT_DE_PASSE_PROF)
            )
            mdp = st.text_input("🔒 Mot de passe professeur", type="password")
            if mdp:
                if mdp == mdp_attendu:
                    st.session_state.prof_auth = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect.")
            return

        afficher_dashboard_prof()
        return

    # ══════════════════════════════════════════════════════════
    # 🧑‍🎓  PAGE ÉLÈVE — Tuteur
    # ══════════════════════════════════════════════════════════

    st.markdown("""
    <div class="main-title">
        <h1>🎓 Tuteur de Maths IA</h1>
        <p>Diagnostic · Entraînement ciblé · Bilan personnalisé</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Lancement de session ──────────────────────────────────

    if btn_start:
        profil = {
            "nom": nom or "Élève",
            "classe": classe,
            "programme": programme,
            "chapitre": chapitre,
            "objectif": objectif or "Réviser et progresser",
            "temps": temps,
        }
        st.session_state.profil = profil
        st.session_state.session_active = True
        st.session_state.nb_exercices = 0
        st.session_state.phase = "diagnostic"
        st.session_state.debut_session = datetime.now()

        historique_txt = resume_historique(sessions_passees)
        contexte = construire_contexte_initial(profil, historique_txt)

        st.session_state.messages = [
            {"role": "system", "content": contexte},
        ]

        with st.spinner("Le tuteur prépare le diagnostic..."):
            premier_msg = (
                f"Bonjour ! Je suis prêt pour une séance de {temps} "
                f"sur le chapitre « {chapitre} » en {classe}. "
                f"Mon objectif : {objectif or 'réviser et progresser'}. "
                "Commence le diagnostic."
            )
            st.session_state.messages.append({"role": "user", "content": premier_msg})
            reponse = appel_tuteur(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": reponse})
        st.rerun()

    # ── Demande de bilan ──────────────────────────────────────

    if btn_bilan and st.session_state.session_active:
        st.session_state.messages.append(
            {"role": "user", "content": "Peux-tu me faire un bilan de cette séance ?"}
        )
        with st.spinner("Génération du bilan..."):
            reponse = appel_tuteur(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": reponse})

        st.session_state.phase = "bilan"

        # Sauvegarde automatique du bilan
        if sb_ok:
            sauvegarder_session_db(
                st.session_state.profil,
                st.session_state.messages,
                st.session_state.nb_exercices,
                "bilan",
                bilan=reponse,
            )

        st.rerun()

    # ── Écran d'accueil ───────────────────────────────────────

    if not st.session_state.session_active:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            ### 🔍 Diagnostic
            3 exercices rapides pour identifier
            tes acquis et tes points à travailler.
            """)
        with col2:
            st.markdown("""
            ### 🎯 Entraînement
            Des exercices adaptés à ton niveau,
            avec indices et corrections détaillées.
            """)
        with col3:
            st.markdown("""
            ### 📊 Bilan
            Un résumé de tes progrès,
            acquis et prochaines étapes.
            """)

        # Afficher les séances passées si disponibles
        if sessions_passees:
            st.markdown("---")
            st.markdown("### 📂 Tes séances précédentes")
            for s in sessions_passees[:5]:
                date = str(s.get("date_session", ""))[:10]
                ch = s.get("chapitre", "?")
                nb = s.get("nb_exercices", 0)
                bilan = s.get("bilan", "")
                with st.expander(f"📅 {date} — {ch} · {nb} exercices"):
                    if bilan:
                        st.info(bilan)
                    else:
                        st.caption("Pas de bilan.")

        st.markdown("---")
        st.info("👈 Configure ton profil dans la barre latérale puis clique sur **Démarrer**.")
        return

    # ══════════════════════════════════════════════════════════
    # 💬  ZONE DE CHAT
    # ══════════════════════════════════════════════════════════

    phase = st.session_state.phase
    phase_labels = {
        "diagnostic": ("🔍 Diagnostic", "phase-diagnostic"),
        "entrainement": ("🎯 Entraînement", "phase-entrainement"),
        "bilan": ("📊 Bilan", "phase-bilan"),
    }
    label, css_class = phase_labels.get(phase, ("📝 En cours", "phase-entrainement"))

    col_phase, col_stats1, col_stats2, col_stats3 = st.columns([2, 1, 1, 1])

    with col_phase:
        st.markdown(f'<span class="phase-badge {css_class}">{label}</span>', unsafe_allow_html=True)

    with col_stats1:
        st.markdown(
            f'<div class="stat-card"><div class="number">{st.session_state.nb_exercices}</div>'
            f'<div class="label">Exercices</div></div>', unsafe_allow_html=True)

    with col_stats2:
        nb_msgs = len([m for m in st.session_state.messages if m["role"] == "user"]) - 1
        st.markdown(
            f'<div class="stat-card"><div class="number">{max(0, nb_msgs)}</div>'
            f'<div class="label">Échanges</div></div>', unsafe_allow_html=True)

    with col_stats3:
        if st.session_state.debut_session:
            duree = (datetime.now() - st.session_state.debut_session).seconds // 60
            st.markdown(
                f'<div class="stat-card"><div class="number">{duree} min</div>'
                f'<div class="label">Durée</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Afficher les messages
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "system":
            continue
        if i == 1 and msg["role"] == "user" and "Commence le diagnostic" in msg.get("content", ""):
            continue
        with st.chat_message(msg["role"], avatar="🎓" if msg["role"] == "assistant" else "🧑‍🎓"):
            st.markdown(msg["content"])

    # ── Input élève ───────────────────────────────────────────

    if user_input := st.chat_input("Ta réponse ou ta question..."):
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(user_input)

        mots_exercice = ["exercice", "question", "calcule", "résous", "détermine",
                         "montre que", "prouve", "simplifie", "développe", "factorise"]

        with st.chat_message("assistant", avatar="🎓"):
            with st.spinner("Réflexion..."):
                reponse = appel_tuteur(st.session_state.messages)

            st.markdown(reponse)
            st.session_state.messages.append({"role": "assistant", "content": reponse})

            reponse_lower = reponse.lower()
            if any(mot in reponse_lower for mot in mots_exercice):
                st.session_state.nb_exercices += 1
                if st.session_state.nb_exercices > 3 and st.session_state.phase == "diagnostic":
                    st.session_state.phase = "entrainement"
            if any(mot in reponse_lower for mot in ["bilan", "résumé", "synthèse"]):
                st.session_state.phase = "bilan"


# ════════════════════════════════════════════════════════════
# 🚀  LANCEMENT
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
