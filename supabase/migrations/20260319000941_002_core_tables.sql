-- ============================================
-- 002: Core Tables (The Bible)
-- ============================================

-- Water Bodies: the canonical registry of fishable locations
CREATE TABLE water_bodies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    state           CHAR(2) NOT NULL,
    county          TEXT,
    type            TEXT NOT NULL CHECK (type IN (
                        'lake', 'reservoir', 'river', 'creek',
                        'pond', 'stream', 'marina', 'access_point'
                    )),
    coordinates     GEOGRAPHY(POINT, 4326) NOT NULL,
    geometry        GEOGRAPHY(GEOMETRY, 4326),
    parent_id       UUID REFERENCES water_bodies(id) ON DELETE SET NULL,
    attributes      JSONB NOT NULL DEFAULT '{}',
    popularity_rank INT,
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN (
                        'active', 'seasonal', 'closed', 'unverified'
                    )),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_water_bodies_state ON water_bodies(state);
CREATE INDEX idx_water_bodies_type ON water_bodies(type);
CREATE INDEX idx_water_bodies_status ON water_bodies(status);
CREATE INDEX idx_water_bodies_coordinates ON water_bodies USING GIST(coordinates);
CREATE INDEX idx_water_bodies_geometry ON water_bodies USING GIST(geometry);
CREATE INDEX idx_water_bodies_parent ON water_bodies(parent_id);
CREATE INDEX idx_water_bodies_attributes ON water_bodies USING GIN(attributes);

-- Water Body Aliases: the rosetta stone for name matching
CREATE TABLE water_body_aliases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    water_body_id   UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    alias           TEXT NOT NULL,
    alias_lower     TEXT GENERATED ALWAYS AS (LOWER(alias)) STORED,
    source          TEXT NOT NULL CHECK (source IN (
                        'state_dwr', 'usgs', 'nhdplus', 'manual', 'scraped'
                    )),
    is_primary      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_aliases_lower ON water_body_aliases(alias_lower);
CREATE INDEX idx_aliases_water_body ON water_body_aliases(water_body_id);
CREATE INDEX idx_aliases_trgm ON water_body_aliases USING GIN(alias_lower gin_trgm_ops);
CREATE UNIQUE INDEX idx_aliases_primary ON water_body_aliases(water_body_id) WHERE is_primary = true;

-- Data Source Links: per-source health tracking per water body
CREATE TABLE data_source_links (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    water_body_id           UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    source_type             TEXT NOT NULL CHECK (source_type IN (
                                'usgs_gauge', 'noaa_station', 'state_dwr',
                                'nhdplus_feature', 'ice_report', 'fishing_report',
                                'army_corps', 'epa_wqx', 'moon', 'regulations'
                            )),
    external_id             TEXT,
    source_url              TEXT,
    refresh_frequency_hours INT NOT NULL DEFAULT 6,
    last_refreshed_at       TIMESTAMPTZ,
    last_value_summary      TEXT,
    health_status           TEXT NOT NULL DEFAULT 'unknown' CHECK (health_status IN (
                                'healthy', 'stale', 'broken', 'unknown', 'no_source'
                            )),
    config                  JSONB NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dsl_water_body ON data_source_links(water_body_id);
CREATE INDEX idx_dsl_source_type ON data_source_links(source_type);
CREATE INDEX idx_dsl_health ON data_source_links(health_status);
CREATE INDEX idx_dsl_refresh ON data_source_links(last_refreshed_at);

-- Species: canonical list
CREATE TABLE species (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    common_name     TEXT NOT NULL UNIQUE,
    scientific_name TEXT,
    species_group   TEXT NOT NULL CHECK (species_group IN (
                        'trout', 'bass', 'panfish', 'catfish',
                        'walleye', 'pike', 'salmon', 'carp', 'other'
                    )),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Species Aliases: normalization layer
CREATE TABLE species_aliases (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    species_id  UUID NOT NULL REFERENCES species(id) ON DELETE CASCADE,
    alias       TEXT NOT NULL,
    alias_lower TEXT GENERATED ALWAYS AS (LOWER(alias)) STORED,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_species_aliases_lower ON species_aliases(alias_lower);
CREATE INDEX idx_species_aliases_species ON species_aliases(species_id);
