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

-- Politique : accès total via la clé service (anon key dans notre cas)
-- En production, restreindre selon l'authentification
CREATE POLICY "allow_all" ON sessions
    FOR ALL
    USING (true)
    WITH CHECK (true);
