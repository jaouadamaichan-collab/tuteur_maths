-- ════════════════════════════════════════════════════════════
-- 🗄️  Tuteur Maths IA — Table Supabase
-- ════════════════════════════════════════════════════════════
-- À exécuter dans Supabase → SQL Editor → New Query → Run

CREATE TABLE IF NOT EXISTS sessions (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    eleve_nom     TEXT NOT NULL,
    classe        TEXT DEFAULT '',
    programme     TEXT DEFAULT '',
    chapitre      TEXT DEFAULT '',
    objectif      TEXT DEFAULT '',
    temps         TEXT DEFAULT '',
    nb_exercices  INTEGER DEFAULT 0,
    nb_echanges   INTEGER DEFAULT 0,
    phase_finale  TEXT DEFAULT '',
    bilan         TEXT DEFAULT '',
    messages      JSONB DEFAULT '[]'::jsonb,
    date_session  TIMESTAMPTZ DEFAULT now()
);

-- Index pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_sessions_eleve ON sessions (eleve_nom);
CREATE INDEX IF NOT EXISTS idx_sessions_date  ON sessions (date_session DESC);

-- Activer Row Level Security (recommandé par Supabase)
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Aucune politique d'accès public : seule la clé SECRÈTE (sb_secret_… ou service_role),
-- stockée dans les secrets Streamlit, peut lire et écrire. Les élèves sont en majorité mineurs.
-- Supprime l'ancienne politique ouverte créée par une version précédente de ce script.
DROP POLICY IF EXISTS "allow_all" ON sessions;
