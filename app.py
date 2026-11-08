#!/usr/bin/env python3
"""
🎓 Tuteur de Maths IA — Application Streamlit
Parcours personnalisé : diagnostic → entraînement → bilan

Nécessite :
  pip install streamlit groq
  export GROQ_API_KEY="gsk_..."
  streamlit run app.py
"""

import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
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

HISTORIQUE_DIR = Path("historique")
HISTORIQUE_DIR.mkdir(exist_ok=True)

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


# ════════════════════════════════════════════════════════════
# 🗄️  HISTORIQUE (sauvegarde locale JSON)
# ════════════════════════════════════════════════════════════

def sauvegarder_session(profil, messages, bilan=""):
    """Sauvegarde la session dans un fichier JSON horodaté."""
    nom = profil.get("nom", "eleve")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fichier = HISTORIQUE_DIR / f"{nom}_{ts}.json"

    data = {
        "date": datetime.now().isoformat(),
        "profil": profil,
        "messages": [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["role"] != "system"
        ],
        "bilan": bilan,
    }
    fichier.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return fichier


def charger_sessions(nom):
    """Charge les sessions précédentes d'un élève."""
    sessions = []
    for f in sorted(HISTORIQUE_DIR.glob(f"{nom}_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append(data)
        except Exception:
            continue
    return sessions


def resume_historique(sessions):
    """Résume l'historique pour l'injecter dans le contexte."""
    if not sessions:
        return ""
    lignes = ["\n--- HISTORIQUE DES SÉANCES PRÉCÉDENTES ---"]
    for s in sessions[:3]:  # 3 dernières sessions max
        date = s.get("date", "?")[:10]
        bilan = s.get("bilan", "")
        profil = s.get("profil", {})
        chapitre = profil.get("chapitre", "?")
        lignes.append(f"\n[{date}] Chapitre : {chapitre}")
        if bilan:
            lignes.append(f"Bilan : {bilan}")
    lignes.append("--- FIN HISTORIQUE ---\n")
    return "\n".join(lignes)


# ════════════════════════════════════════════════════════════
# 🤖  APPEL LLM (Groq)
# ════════════════════════════════════════════════════════════

def appel_tuteur(messages):
    """Appel à Groq avec le contexte complet."""
    api_key = os.environ.get("GROQ_API_KEY", st.session_state.get("api_key", ""))
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
# 🎨  INTERFACE STREAMLIT
# ════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="🎓 Tuteur Maths IA",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # CSS personnalisé
    st.markdown("""
    <style>
    .main-title {
        text-align: center;
        padding: 0.5rem 0 0.2rem 0;
    }
    .main-title h1 {
        font-size: 2rem;
        margin-bottom: 0;
    }
    .main-title p {
        color: #888;
        font-size: 0.95rem;
    }
    .phase-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .phase-diagnostic { background: #fef3c7; color: #92400e; }
    .phase-entrainement { background: #dbeafe; color: #1e40af; }
    .phase-bilan { background: #d1fae5; color: #065f46; }
    .stat-card {
        background: #f8f9fa;
        border-radius: 0.6rem;
        padding: 0.8rem;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .stat-card .number {
        font-size: 1.6rem;
        font-weight: 700;
        color: #2563eb;
    }
    .stat-card .label {
        font-size: 0.8rem;
        color: #6b7280;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Initialisation session state ──────────────────────────
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_active" not in st.session_state:
        st.session_state.session_active = False
    if "profil" not in st.session_state:
        st.session_state.profil = {}
    if "nb_exercices" not in st.session_state:
        st.session_state.nb_exercices = 0
    if "phase" not in st.session_state:
        st.session_state.phase = "config"
    if "debut_session" not in st.session_state:
        st.session_state.debut_session = None

    # ══════════════════════════════════════════════════════════
    # 📚  BARRE LATÉRALE — Configuration
    # ══════════════════════════════════════════════════════════

    with st.sidebar:
        st.markdown("## ⚙️ Configuration")

        # Clé API
        if not os.environ.get("GROQ_API_KEY"):
            api_key = st.text_input(
                "🔑 Clé API Groq",
                type="password",
                value=st.session_state.get("api_key", ""),
                help="Obtiens une clé gratuite sur console.groq.com",
            )
            if api_key:
                st.session_state.api_key = api_key
        else:
            st.success("🔑 Clé API configurée (env)")

        st.divider()
        st.markdown("## 👤 Profil élève")

        nom = st.text_input("Nom / Pseudo", value="", placeholder="Ex: Sarah")

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
        st.divider()
        sessions_passees = charger_sessions(nom) if nom else []
        if sessions_passees:
            st.info(f"📂 {len(sessions_passees)} séance(s) trouvée(s)")

        # ── Boutons d'action ──────────────────────────────────

        col1, col2 = st.columns(2)

        with col1:
            btn_start = st.button(
                "▶️ Démarrer" if not st.session_state.session_active else "🔄 Relancer",
                use_container_width=True,
                type="primary",
            )

        with col2:
            btn_bilan = st.button(
                "📊 Bilan",
                use_container_width=True,
                disabled=not st.session_state.session_active,
            )

        if st.session_state.session_active:
            if st.button("💾 Sauvegarder la séance", use_container_width=True):
                fichier = sauvegarder_session(
                    st.session_state.profil,
                    st.session_state.messages,
                )
                st.success(f"Sauvegardé : {fichier.name}")

            if st.button("🗑️ Nouvelle séance", use_container_width=True):
                st.session_state.messages = []
                st.session_state.session_active = False
                st.session_state.nb_exercices = 0
                st.session_state.phase = "config"
                st.session_state.debut_session = None
                st.rerun()

    # ══════════════════════════════════════════════════════════
    # 🏠  ZONE PRINCIPALE
    # ══════════════════════════════════════════════════════════

    # Titre
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

        # Contexte avec historique
        historique_txt = resume_historique(sessions_passees)
        contexte = construire_contexte_initial(profil, historique_txt)

        # Initialiser la conversation
        st.session_state.messages = [
            {"role": "system", "content": contexte},
        ]

        # Premier message du tuteur
        with st.spinner("Le tuteur prépare le diagnostic..."):
            premier_msg = (
                f"Bonjour ! Je suis prêt pour une séance de {temps} "
                f"sur le chapitre « {chapitre} » en {classe}. "
                f"Mon objectif : {objectif or 'réviser et progresser'}. "
                "Commence le diagnostic."
            )
            st.session_state.messages.append(
                {"role": "user", "content": premier_msg}
            )
            reponse = appel_tuteur(st.session_state.messages)
            st.session_state.messages.append(
                {"role": "assistant", "content": reponse}
            )
        st.rerun()

    # ── Demande de bilan ──────────────────────────────────────

    if btn_bilan and st.session_state.session_active:
        st.session_state.messages.append(
            {"role": "user", "content": "Peux-tu me faire un bilan de cette séance ?"}
        )
        with st.spinner("Génération du bilan..."):
            reponse = appel_tuteur(st.session_state.messages)
            st.session_state.messages.append(
                {"role": "assistant", "content": reponse}
            )
        st.session_state.phase = "bilan"
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

        st.markdown("---")
        st.info("👈 Configure ton profil dans la barre latérale puis clique sur **Démarrer**.")
        return

    # ══════════════════════════════════════════════════════════
    # 💬  ZONE DE CHAT
    # ══════════════════════════════════════════════════════════

    # Indicateurs de session
    phase = st.session_state.phase
    phase_labels = {
        "diagnostic": ("🔍 Diagnostic", "phase-diagnostic"),
        "entrainement": ("🎯 Entraînement", "phase-entrainement"),
        "bilan": ("📊 Bilan", "phase-bilan"),
    }
    label, css_class = phase_labels.get(phase, ("📝 En cours", "phase-entrainement"))

    col_phase, col_stats1, col_stats2, col_stats3 = st.columns([2, 1, 1, 1])

    with col_phase:
        st.markdown(
            f'<span class="phase-badge {css_class}">{label}</span>',
            unsafe_allow_html=True,
        )

    with col_stats1:
        st.markdown(
            f'<div class="stat-card"><div class="number">{st.session_state.nb_exercices}</div>'
            f'<div class="label">Exercices</div></div>',
            unsafe_allow_html=True,
        )

    with col_stats2:
        nb_msgs = len([m for m in st.session_state.messages if m["role"] == "user"]) - 1
        st.markdown(
            f'<div class="stat-card"><div class="number">{max(0, nb_msgs)}</div>'
            f'<div class="label">Échanges</div></div>',
            unsafe_allow_html=True,
        )

    with col_stats3:
        if st.session_state.debut_session:
            duree = (datetime.now() - st.session_state.debut_session).seconds // 60
            st.markdown(
                f'<div class="stat-card"><div class="number">{duree} min</div>'
                f'<div class="label">Durée</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Afficher les messages (sauf le system prompt et le premier user auto)
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "system":
            continue
        # Masquer le premier message auto de lancement
        if i == 1 and msg["role"] == "user" and "Commence le diagnostic" in msg.get("content", ""):
            continue

        with st.chat_message(msg["role"], avatar="🎓" if msg["role"] == "assistant" else "🧑‍🎓"):
            st.markdown(msg["content"])

    # ── Input élève ───────────────────────────────────────────

    if user_input := st.chat_input("Ta réponse ou ta question..."):
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(user_input)

        # Détecter les exercices pour mettre à jour le compteur et la phase
        mots_exercice = ["exercice", "question", "calcule", "résous", "détermine",
                         "montre que", "prouve", "simplifie", "développe", "factorise"]
        mots_bilan = ["bilan", "résumé", "synthèse", "récapitulatif"]

        with st.chat_message("assistant", avatar="🎓"):
            with st.spinner("Réflexion..."):
                reponse = appel_tuteur(st.session_state.messages)

            st.markdown(reponse)
            st.session_state.messages.append({"role": "assistant", "content": reponse})

            # Mise à jour des compteurs
            reponse_lower = reponse.lower()
            if any(mot in reponse_lower for mot in mots_exercice):
                st.session_state.nb_exercices += 1
                if st.session_state.nb_exercices > 3 and st.session_state.phase == "diagnostic":
                    st.session_state.phase = "entrainement"
            if any(mot in reponse_lower for mot in mots_bilan):
                st.session_state.phase = "bilan"


# ════════════════════════════════════════════════════════════
# 🚀  LANCEMENT
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
