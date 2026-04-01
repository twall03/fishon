-- ============================================
-- 009: Water Body Species — what lives here and how to catch it
-- Junction table: each water body × species combo gets its own fishing intel
-- ============================================

CREATE TABLE water_body_species (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    water_body_id   UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    species_id      UUID NOT NULL REFERENCES species(id) ON DELETE CASCADE,

    -- Population info
    is_stocked      BOOLEAN NOT NULL DEFAULT false,
    is_native       BOOLEAN NOT NULL DEFAULT false,
    abundance       TEXT CHECK (abundance IN ('abundant', 'common', 'occasional', 'rare')),

    -- How to catch them HERE
    popular_methods TEXT[],     -- {"fly fishing", "bait", "trolling", "spin casting", "ice fishing"}
    popular_baits   TEXT[],     -- {"PowerBait", "woolly bugger", "kastmaster", "worm", "minnow"}
    popular_lures   TEXT[],     -- {"Rapala", "kastmaster", "rooster tail", "jake's spin-a-lure"}
    popular_flies   TEXT[],     -- {"woolly bugger", "elk hair caddis", "pheasant tail", "adams"}
    best_season     TEXT,       -- "spring", "fall", "summer", "winter", "year-round"
    best_time       TEXT,       -- "early morning", "evening", "midday in winter"
    size_range      TEXT,       -- "8-14 inches" or "2-8 lbs"
    record_size     TEXT,       -- "12 lbs 4 oz (2019)"
    tips            TEXT,       -- freeform: "Fish the inlet in spring when flows are high"
    regulations     TEXT,       -- species-specific regs for this water: "2 fish limit, 15 inch minimum"

    -- Metadata
    data_source     TEXT,       -- where this info came from: "utah_dwr", "community", "ai_generated"
    confidence      FLOAT DEFAULT 1.0 CHECK (confidence BETWEEN 0 AND 1),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- One entry per species per water body
CREATE UNIQUE INDEX idx_wbs_unique ON water_body_species(water_body_id, species_id);
CREATE INDEX idx_wbs_water_body ON water_body_species(water_body_id);
CREATE INDEX idx_wbs_species ON water_body_species(species_id);

-- Trigger for updated_at
CREATE TRIGGER trg_water_body_species_updated_at
    BEFORE UPDATE ON water_body_species
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS
ALTER TABLE water_body_species ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read access" ON water_body_species FOR SELECT USING (true);
