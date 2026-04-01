-- ============================================
-- 011: Waypoints, Notes, Photos (auth-gated user content)
-- ============================================

-- Waypoints: user-saved spots on the map (like onX waypoints)
CREATE TABLE waypoints (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    description     TEXT,
    coordinates     GEOGRAPHY(POINT, 4326) NOT NULL,
    icon            TEXT DEFAULT 'pin',          -- pin, fish, boat, camp, parking, custom
    color           TEXT DEFAULT '#0ea5e9',      -- hex color
    water_body_id   UUID REFERENCES water_bodies(id) ON DELETE SET NULL,  -- optional link to a water body
    is_public       BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_waypoints_user ON waypoints(user_id);
CREATE INDEX idx_waypoints_water_body ON waypoints(water_body_id);
CREATE INDEX idx_waypoints_coords ON waypoints USING GIST(coordinates);

CREATE TRIGGER trg_waypoints_updated_at
    BEFORE UPDATE ON waypoints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Notes: text notes attached to water bodies or waypoints
CREATE TABLE notes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    water_body_id   UUID REFERENCES water_bodies(id) ON DELETE SET NULL,
    waypoint_id     UUID REFERENCES waypoints(id) ON DELETE SET NULL,
    title           TEXT,
    body            TEXT NOT NULL,
    is_public       BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notes_user ON notes(user_id);
CREATE INDEX idx_notes_water_body ON notes(water_body_id);
CREATE INDEX idx_notes_waypoint ON notes(waypoint_id);

CREATE TRIGGER trg_notes_updated_at
    BEFORE UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Photos: geotagged images attached to water bodies, waypoints, or notes
CREATE TABLE photos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    water_body_id   UUID REFERENCES water_bodies(id) ON DELETE SET NULL,
    waypoint_id     UUID REFERENCES waypoints(id) ON DELETE SET NULL,
    note_id         UUID REFERENCES notes(id) ON DELETE SET NULL,
    storage_path    TEXT NOT NULL,               -- Supabase Storage path
    thumbnail_path  TEXT,                        -- smaller version
    caption         TEXT,
    coordinates     GEOGRAPHY(POINT, 4326),      -- where the photo was taken
    taken_at        TIMESTAMPTZ,                 -- EXIF date if available
    is_public       BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_photos_user ON photos(user_id);
CREATE INDEX idx_photos_water_body ON photos(water_body_id);
CREATE INDEX idx_photos_waypoint ON photos(waypoint_id);

-- Catch log: record catches (species, size, method, location)
CREATE TABLE catch_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    water_body_id   UUID REFERENCES water_bodies(id) ON DELETE SET NULL,
    waypoint_id     UUID REFERENCES waypoints(id) ON DELETE SET NULL,
    species_id      UUID REFERENCES species(id),
    species_text    TEXT,                        -- freeform if species not in DB
    length_inches   FLOAT,
    weight_lbs      FLOAT,
    method          TEXT,                        -- "fly fishing", "bait", "trolling"
    lure_or_fly     TEXT,                        -- what worked: "woolly bugger #8"
    photo_id        UUID REFERENCES photos(id) ON DELETE SET NULL,
    notes           TEXT,
    caught_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_public       BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_catch_user ON catch_logs(user_id);
CREATE INDEX idx_catch_water_body ON catch_logs(water_body_id);
CREATE INDEX idx_catch_species ON catch_logs(species_id);
CREATE INDEX idx_catch_date ON catch_logs(caught_at DESC);

-- RLS for all user content tables
ALTER TABLE waypoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE catch_logs ENABLE ROW LEVEL SECURITY;

-- Users see their own + public content
CREATE POLICY "Users read own waypoints" ON waypoints FOR SELECT USING (auth.uid() = user_id OR is_public = true);
CREATE POLICY "Users manage own waypoints" ON waypoints FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users read own notes" ON notes FOR SELECT USING (auth.uid() = user_id OR is_public = true);
CREATE POLICY "Users manage own notes" ON notes FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users read own photos" ON photos FOR SELECT USING (auth.uid() = user_id OR is_public = true);
CREATE POLICY "Users manage own photos" ON photos FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users read own catches" ON catch_logs FOR SELECT USING (auth.uid() = user_id OR is_public = true);
CREATE POLICY "Users manage own catches" ON catch_logs FOR ALL USING (auth.uid() = user_id);

-- Storage bucket for photos (created via Supabase dashboard or CLI)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('photos', 'photos', true);
