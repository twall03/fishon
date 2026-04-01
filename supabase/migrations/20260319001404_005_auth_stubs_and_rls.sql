-- ============================================
-- 005: Auth Stubs and Row Level Security
-- ============================================

-- Profiles: extends Supabase auth.users (stub for future auth)
CREATE TABLE profiles (
    id                  UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name        TEXT,
    subscription_tier   TEXT NOT NULL DEFAULT 'free' CHECK (subscription_tier IN (
                            'free', 'pro', 'guide'
                        )),
    home_state          CHAR(2),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- User Favorites: which water bodies a user tracks
CREATE TABLE user_favorites (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    water_body_id        UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    notify_on_stocking   BOOLEAN NOT NULL DEFAULT true,
    notify_on_conditions BOOLEAN NOT NULL DEFAULT false,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_favorites_unique ON user_favorites(user_id, water_body_id);
CREATE INDEX idx_favorites_water_body ON user_favorites(water_body_id);
CREATE INDEX idx_favorites_user ON user_favorites(user_id);

-- ============================================
-- Enable RLS on ALL tables
-- ============================================

ALTER TABLE water_bodies ENABLE ROW LEVEL SECURITY;
ALTER TABLE water_body_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_source_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE species ENABLE ROW LEVEL SECURITY;
ALTER TABLE species_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE stocking_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE conditions ENABLE ROW LEVEL SECURITY;
ALTER TABLE weather_forecasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ice_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;

-- ============================================
-- Permissive policies (tightened when auth is added)
-- Service role bypasses RLS automatically.
-- These policies allow anon/authenticated read access to public data.
-- ============================================

-- Public data: anyone can read water bodies, species, stocking, conditions, weather, ice
CREATE POLICY "Public read access" ON water_bodies FOR SELECT USING (true);
CREATE POLICY "Public read access" ON water_body_aliases FOR SELECT USING (true);
CREATE POLICY "Public read access" ON data_source_links FOR SELECT USING (true);
CREATE POLICY "Public read access" ON species FOR SELECT USING (true);
CREATE POLICY "Public read access" ON species_aliases FOR SELECT USING (true);
CREATE POLICY "Public read access" ON stocking_events FOR SELECT USING (true);
CREATE POLICY "Public read access" ON conditions FOR SELECT USING (true);
CREATE POLICY "Public read access" ON weather_forecasts FOR SELECT USING (true);
CREATE POLICY "Public read access" ON ice_reports FOR SELECT USING (true);

-- Scraping infra: no public access (service role only, which bypasses RLS)
-- No policies needed — RLS enabled with no policies = denied for non-service roles

-- User data: users can only see their own data (when auth is active)
CREATE POLICY "Users read own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users read own favorites" ON user_favorites FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users manage own favorites" ON user_favorites FOR ALL USING (auth.uid() = user_id);
