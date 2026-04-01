# Design Document

## Overview

The FishOn data structure on Supabase (PostgreSQL + PostGIS). This is the foundation every feature builds on. The design centers on the water body as the primary entity — a registry of fishable locations (not just physical water bodies), each with N data sources linked directly to it, each source independently tracked for health and freshness.

Managed via Supabase CLI with versioned SQL migrations. PostGIS for geospatial. RLS enabled on all tables for future Supabase Auth.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SUPABASE PROJECT                            │
│                                                                     │
│  ┌─────────────┐    ┌──────────────────┐    ┌───────────────────┐  │
│  │ water_bodies │◄──┤water_body_aliases │    │    species        │  │
│  │  (THE BIBLE) │    └──────────────────┘    │  (canonical list) │  │
│  └──────┬───────┘                            └────────┬──────────┘  │
│         │                                             │             │
│         │ water_body_id                    species_id  │             │
│         │                                             │             │
│  ┌──────▼───────────┐                     ┌───────────▼──────────┐ │
│  │data_source_links  │                     │  species_aliases     │ │
│  │(per-source health)│                     └──────────────────────┘ │
│  └──────┬───────────┘                                               │
│         │                                                           │
│         │ water_body_id                                             │
│         ├──────────────────┬──────────────────┬──────────────────┐  │
│  ┌──────▼──────┐   ┌──────▼──────┐   ┌───────▼─────┐  ┌────────▼┐ │
│  │  stocking   │   │ conditions  │   │   weather   │  │  ice    │ │
│  │  _events    │   │ (USGS)      │   │ _forecasts  │  │_reports │ │
│  └─────────────┘   └─────────────┘   └─────────────┘  └─────────┘ │
│                                                                     │
│  ┌───────────────┐  ┌─────────────────┐  ┌────────────────────┐    │
│  │source_catalog  │  │prompt_templates  │  │   scrape_logs     │    │
│  │(scraping infra)│──┤(per-state AI)    │  │  (audit trail)    │    │
│  └───────────────┘  └─────────────────┘  └────────────────────┘    │
│                                                                     │
│  ┌──────────┐  ┌────────────────┐                                  │
│  │ profiles │  │ user_favorites │  ← stubs for Supabase Auth       │
│  └──────────┘  └────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Components and Interfaces

### Extensions Required

```sql
-- Enable in Supabase SQL editor or migration
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- trigram matching for fuzzy alias search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

### Table: `water_bodies` (The Bible)

The canonical registry of fishable locations. NOT just physical water bodies — a large reservoir like Flaming Gorge has multiple entries (one per marina / access point / section), each in its own state.

```sql
CREATE TABLE water_bodies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,                    -- canonical display name
    state           CHAR(2) NOT NULL,                 -- 2-letter state code
    county          TEXT,                             -- for disambiguation
    type            TEXT NOT NULL CHECK (type IN (
                        'lake', 'reservoir', 'river', 'creek',
                        'pond', 'stream', 'marina', 'access_point'
                    )),
    coordinates     GEOGRAPHY(POINT, 4326) NOT NULL,  -- centroid for map pins
    geometry        GEOGRAPHY(GEOMETRY, 4326),         -- polygon/line from NHDPlus (nullable — not all will have this initially)
    parent_id       UUID REFERENCES water_bodies(id),  -- optional grouping (Flaming Gorge → its marinas)
    attributes      JSONB DEFAULT '{}',                -- type-specific fields
    popularity_rank INT,                               -- per state, nullable
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN (
                        'active', 'seasonal', 'closed', 'unverified'
                    )),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_water_bodies_state ON water_bodies(state);
CREATE INDEX idx_water_bodies_type ON water_bodies(type);
CREATE INDEX idx_water_bodies_status ON water_bodies(status);
CREATE INDEX idx_water_bodies_coordinates ON water_bodies USING GIST(coordinates);
CREATE INDEX idx_water_bodies_geometry ON water_bodies USING GIST(geometry);
CREATE INDEX idx_water_bodies_parent ON water_bodies(parent_id);
CREATE INDEX idx_water_bodies_attributes ON water_bodies USING GIN(attributes);
```

**JSONB `attributes` by type:**

```jsonc
// Lake / Reservoir
{
    "surface_acres": 17164,
    "max_depth_ft": 108,
    "boat_ramps": 3,
    "has_stocking": true,
    "has_level_data": true
}

// River / Creek
{
    "avg_flow_cfs": 450,
    "has_flow_data": true,
    "access_type": "wade, float"
}

// Marina / Access Point
{
    "parent_water_name": "Flaming Gorge Reservoir",
    "amenities": ["boat_ramp", "parking", "restrooms"],
    "has_stocking": true
}
```

---

### Table: `water_body_aliases` (The Rosetta Stone)

Every known name variant for fuzzy matching from scraped data. State-scoped via the water body FK to prevent cross-state collisions.

```sql
CREATE TABLE water_body_aliases (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    water_body_id   UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    alias           TEXT NOT NULL,
    alias_lower     TEXT GENERATED ALWAYS AS (LOWER(alias)) STORED, -- for fast case-insensitive lookup
    source          TEXT NOT NULL CHECK (source IN (
                        'state_dwr', 'usgs', 'nhdplus', 'manual', 'scraped'
                    )),
    is_primary      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Fast alias lookup: case-insensitive, state-scoped via join
CREATE INDEX idx_aliases_lower ON water_body_aliases(alias_lower);
CREATE INDEX idx_aliases_water_body ON water_body_aliases(water_body_id);

-- Trigram index for fuzzy/partial matching
CREATE INDEX idx_aliases_trgm ON water_body_aliases USING GIN(alias_lower gin_trgm_ops);

-- Enforce one primary alias per water body
CREATE UNIQUE INDEX idx_aliases_primary ON water_body_aliases(water_body_id)
    WHERE is_primary = true;
```

**Alias lookup function** (state-scoped, used by scraping pipeline):

```sql
CREATE OR REPLACE FUNCTION find_water_body(
    p_alias TEXT,
    p_state CHAR(2)
) RETURNS UUID AS $$
    SELECT wb.id
    FROM water_body_aliases wba
    JOIN water_bodies wb ON wb.id = wba.water_body_id
    WHERE wba.alias_lower = LOWER(p_alias)
      AND wb.state = p_state
    LIMIT 1;
$$ LANGUAGE sql STABLE;
```

---

### Table: `data_source_links` (Per-Source Health Tracking)

Links each water body to ALL its data sources. Tracks health and freshness independently per source per water body. This is how the system knows "stocking data is fresh, USGS is stale, weather is broken" for any given water body.

```sql
CREATE TABLE data_source_links (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    water_body_id           UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    source_type             TEXT NOT NULL CHECK (source_type IN (
                                'usgs_gauge', 'noaa_station', 'state_dwr',
                                'nhdplus_feature', 'ice_report', 'fishing_report',
                                'army_corps', 'epa_wqx', 'moon', 'regulations'
                            )),
    external_id             TEXT,            -- USGS gauge number, NOAA grid point, etc.
    source_url              TEXT,            -- direct link to source page/API
    refresh_frequency_hours INT NOT NULL DEFAULT 6,
    last_refreshed_at       TIMESTAMPTZ,
    last_value_summary      TEXT,            -- human-readable: "12,000 Rainbow Trout" / "450 CFS"
    health_status           TEXT NOT NULL DEFAULT 'unknown' CHECK (health_status IN (
                                'healthy', 'stale', 'broken', 'unknown', 'no_source'
                            )),
    config                  JSONB DEFAULT '{}', -- source-specific config (API params, headers, etc.)
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dsl_water_body ON data_source_links(water_body_id);
CREATE INDEX idx_dsl_source_type ON data_source_links(source_type);
CREATE INDEX idx_dsl_health ON data_source_links(health_status);
CREATE INDEX idx_dsl_refresh ON data_source_links(last_refreshed_at);

-- One source type per water body (with exceptions for multiple gauges)
-- Not enforced as unique — a river section can have multiple USGS gauges
```

---

### Table: `species` (Canonical Species List)

```sql
CREATE TABLE species (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    common_name     TEXT NOT NULL UNIQUE,  -- "Rainbow Trout"
    scientific_name TEXT,                  -- "Oncorhynchus mykiss"
    species_group   TEXT NOT NULL CHECK (species_group IN (
                        'trout', 'bass', 'panfish', 'catfish',
                        'walleye', 'pike', 'salmon', 'carp', 'other'
                    )),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Table: `species_aliases`

```sql
CREATE TABLE species_aliases (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    species_id  UUID NOT NULL REFERENCES species(id) ON DELETE CASCADE,
    alias       TEXT NOT NULL,
    alias_lower TEXT GENERATED ALWAYS AS (LOWER(alias)) STORED,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_species_aliases_lower ON species_aliases(alias_lower);
CREATE INDEX idx_species_aliases_species ON species_aliases(species_id);
```

**Species lookup function:**

```sql
CREATE OR REPLACE FUNCTION find_species(p_alias TEXT) RETURNS UUID AS $$
    SELECT species_id
    FROM species_aliases
    WHERE alias_lower = LOWER(p_alias)
    LIMIT 1;
$$ LANGUAGE sql STABLE;
```

---

### Table: `stocking_events` (Time-Series, Accumulates Forever)

```sql
CREATE TABLE stocking_events (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    water_body_id     UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    species_id        UUID REFERENCES species(id),       -- FK to canonical species
    species_raw       TEXT NOT NULL,                      -- original text from scrape for audit
    quantity          INT,                                -- nullable: some reports don't include qty
    date              DATE NOT NULL,
    source_agency     TEXT NOT NULL,                      -- "Utah DWR", "Colorado CPW"
    source_url        TEXT NOT NULL,                      -- direct link to source page
    raw_text          TEXT,                               -- original scraped text snippet for audit
    confidence_score  FLOAT NOT NULL DEFAULT 1.0 CHECK (confidence_score BETWEEN 0 AND 1),
    needs_review      BOOLEAN NOT NULL DEFAULT false,
    scrape_log_id     UUID,                              -- FK to scrape_logs (which run produced this)
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Deduplication composite key
CREATE UNIQUE INDEX idx_stocking_dedup
    ON stocking_events(water_body_id, species_id, date, quantity)
    WHERE quantity IS NOT NULL;

-- Query indexes
CREATE INDEX idx_stocking_water_body ON stocking_events(water_body_id);
CREATE INDEX idx_stocking_date ON stocking_events(date DESC);
CREATE INDEX idx_stocking_species ON stocking_events(species_id);
CREATE INDEX idx_stocking_state ON stocking_events(water_body_id, date DESC); -- for state-scoped feeds
CREATE INDEX idx_stocking_review ON stocking_events(needs_review) WHERE needs_review = true;
```

---

### Table: `conditions` (USGS Time-Series, Ephemeral)

```sql
CREATE TABLE conditions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    water_body_id   UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    flow_cfs        FLOAT,              -- cubic feet per second (rivers)
    level_ft        FLOAT,              -- water level in feet (lakes/reservoirs)
    temp_f          FLOAT,              -- water temperature
    timestamp       TIMESTAMPTZ NOT NULL,
    source          TEXT NOT NULL DEFAULT 'USGS',
    gauge_id        TEXT,               -- USGS gauge ID for traceability
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Latest conditions per water body
CREATE INDEX idx_conditions_latest ON conditions(water_body_id, timestamp DESC);
CREATE INDEX idx_conditions_gauge ON conditions(gauge_id);

-- Retention: conditions older than 90 days can be aggregated/archived
-- (implement via pg_cron or application-level cleanup)
```

---

### Table: `weather_forecasts` (NOAA, Expires)

```sql
CREATE TABLE weather_forecasts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    water_body_id   UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    forecast_date   DATE NOT NULL,
    temp_high_f     INT,
    temp_low_f      INT,
    wind_mph        INT,
    precip_chance   FLOAT,              -- 0.0 to 1.0
    summary         TEXT,               -- "Partly Cloudy", "Rain likely"
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Latest forecast per water body per date
CREATE UNIQUE INDEX idx_weather_dedup ON weather_forecasts(water_body_id, forecast_date);
CREATE INDEX idx_weather_water_body ON weather_forecasts(water_body_id, forecast_date);
```

---

### Table: `ice_reports` (Seasonal, Community + Scraped)

```sql
CREATE TABLE ice_reports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    water_body_id   UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    thickness_in    FLOAT,
    quality         TEXT CHECK (quality IN ('good', 'fair', 'poor', 'unsafe', 'unknown')),
    reporter        TEXT,               -- "Utah DWR" or future username
    report_source   TEXT NOT NULL CHECK (report_source IN ('agency', 'community', 'scraped')),
    report_date     DATE NOT NULL,
    notes           TEXT,
    confidence_score FLOAT NOT NULL DEFAULT 1.0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ice_water_body ON ice_reports(water_body_id, report_date DESC);
```

---

### Scraping Infrastructure

#### Table: `source_catalog`

Master list of all scraping targets. One entry per source page/URL. State-scoped.

```sql
CREATE TABLE source_catalog (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state                   CHAR(2) NOT NULL,
    name                    TEXT NOT NULL,           -- "Utah DWR Stocking Reports"
    url                     TEXT NOT NULL,
    source_type             TEXT NOT NULL CHECK (source_type IN (
                                'stocking', 'regulations', 'conditions', 'reports', 'ice'
                            )),
    format                  TEXT NOT NULL CHECK (format IN (
                                'html_table', 'html_list', 'pdf', 'csv', 'api', 'json'
                            )),
    scrape_frequency_hours  INT NOT NULL DEFAULT 6,
    prompt_template_id      UUID REFERENCES prompt_templates(id),
    js_rendered             BOOLEAN NOT NULL DEFAULT false,  -- needs Playwright?
    status                  TEXT NOT NULL DEFAULT 'active' CHECK (status IN (
                                'active', 'paused', 'broken', 'needs_review', 'retired'
                            )),
    consecutive_failures    INT NOT NULL DEFAULT 0,
    last_scraped_at         TIMESTAMPTZ,
    last_success_at         TIMESTAMPTZ,
    config                  JSONB DEFAULT '{}',      -- extra config (headers, selectors, etc.)
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_source_state ON source_catalog(state);
CREATE INDEX idx_source_status ON source_catalog(status);
CREATE INDEX idx_source_next_scrape ON source_catalog(last_scraped_at, scrape_frequency_hours);
```

#### Table: `prompt_templates`

Versioned Haiku prompt templates. Per-state, per-source-type. This IS the per-state agent's brain.

```sql
CREATE TABLE prompt_templates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,               -- "utah_stocking_v3"
    state           CHAR(2) NOT NULL,
    source_type     TEXT NOT NULL,               -- matches source_catalog.source_type
    version         INT NOT NULL DEFAULT 1,
    system_prompt   TEXT NOT NULL,               -- the actual Haiku system prompt
    schema_json     JSONB NOT NULL,              -- expected output JSON schema
    examples        JSONB,                       -- few-shot examples for the prompt
    species_map     JSONB,                       -- state-specific species alias overrides
    is_active       BOOLEAN NOT NULL DEFAULT true,
    accuracy_score  FLOAT,                       -- tracked from test runs
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prompt_state ON prompt_templates(state, source_type);
CREATE UNIQUE INDEX idx_prompt_active ON prompt_templates(state, source_type) WHERE is_active = true;
```

#### Table: `scrape_logs`

Audit trail for every scrape run. Links back to source and prompt template.

```sql
CREATE TABLE scrape_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id           UUID NOT NULL REFERENCES source_catalog(id),
    prompt_template_id  UUID REFERENCES prompt_templates(id),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    http_status         INT,
    response_size_bytes INT,
    records_extracted   INT DEFAULT 0,
    records_stored      INT DEFAULT 0,
    records_duplicated  INT DEFAULT 0,
    records_unmatched   INT DEFAULT 0,       -- water bodies not found in bible
    confidence_avg      FLOAT,
    unmatched_names     JSONB,               -- ["Unknown Lake", "Mystery Creek"] for bible expansion
    errors              JSONB,               -- structured error details
    raw_snapshot_url    TEXT,                 -- S3 URL of raw HTML/PDF for replay
    status              TEXT NOT NULL DEFAULT 'running' CHECK (status IN (
                            'running', 'success', 'partial', 'failed'
                        )),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_scrape_source ON scrape_logs(source_id, started_at DESC);
CREATE INDEX idx_scrape_status ON scrape_logs(status);
CREATE INDEX idx_scrape_unmatched ON scrape_logs(records_unmatched) WHERE records_unmatched > 0;
```

---

### Future Auth Stubs

Ready for Supabase Auth — these tables exist but aren't populated until auth is implemented.

```sql
-- Profiles: extends Supabase auth.users
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

-- User favorites: which water bodies a user tracks
CREATE TABLE user_favorites (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    water_body_id       UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    notify_on_stocking  BOOLEAN NOT NULL DEFAULT true,
    notify_on_conditions BOOLEAN NOT NULL DEFAULT false,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_favorites_unique ON user_favorites(user_id, water_body_id);
CREATE INDEX idx_favorites_water_body ON user_favorites(water_body_id);
```

---

### Row Level Security

RLS enabled on all tables. Initially permissive for the scraping pipeline (service role). Will be tightened when auth is added.

```sql
-- Enable RLS on all tables
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

-- Permissive policies for service role (scraping pipeline)
-- These allow full access via the service_role key
-- Public/anon access will be restricted when auth is added
CREATE POLICY "Service role full access" ON water_bodies FOR ALL USING (true);
CREATE POLICY "Service role full access" ON water_body_aliases FOR ALL USING (true);
CREATE POLICY "Service role full access" ON data_source_links FOR ALL USING (true);
CREATE POLICY "Service role full access" ON species FOR ALL USING (true);
CREATE POLICY "Service role full access" ON species_aliases FOR ALL USING (true);
CREATE POLICY "Service role full access" ON stocking_events FOR ALL USING (true);
CREATE POLICY "Service role full access" ON conditions FOR ALL USING (true);
CREATE POLICY "Service role full access" ON weather_forecasts FOR ALL USING (true);
CREATE POLICY "Service role full access" ON ice_reports FOR ALL USING (true);
CREATE POLICY "Service role full access" ON source_catalog FOR ALL USING (true);
CREATE POLICY "Service role full access" ON prompt_templates FOR ALL USING (true);
CREATE POLICY "Service role full access" ON scrape_logs FOR ALL USING (true);
CREATE POLICY "Service role full access" ON profiles FOR ALL USING (true);
CREATE POLICY "Service role full access" ON user_favorites FOR ALL USING (true);
```

---

## Data Models — Relationship Summary

```
water_bodies (1) ──── (N) water_body_aliases
water_bodies (1) ──── (N) data_source_links
water_bodies (1) ──── (N) stocking_events
water_bodies (1) ──── (N) conditions
water_bodies (1) ──── (N) weather_forecasts
water_bodies (1) ──── (N) ice_reports
water_bodies (1) ──── (N) user_favorites
water_bodies (1) ──── (N) water_bodies (parent_id self-ref)

species (1) ──── (N) species_aliases
species (1) ──── (N) stocking_events

source_catalog (1) ──── (N) scrape_logs
source_catalog (1) ──── (1) prompt_templates (active)
prompt_templates (1) ──── (N) scrape_logs

profiles (1) ──── (N) user_favorites
```

---

## Refresh Flow Per Source Type

### Stocking (Scraped — per state page)
```
Cron fires → source_catalog WHERE source_type = 'stocking' AND status = 'active'
  → Fetch HTML from source URL
  → Send to Haiku with state's prompt_template
  → Parse response: array of {water_name, species, quantity, date}
  → For each event:
      → find_water_body(water_name, state) → water_body_id
      → find_species(species_raw) → species_id
      → If water body not found → log in scrape_logs.unmatched_names, skip
      → If duplicate (dedup index) → increment records_duplicated, skip
      → Insert stocking_event
  → Update source_catalog.last_scraped_at
  → Update data_source_links.last_refreshed_at for each affected water body
  → Log everything to scrape_logs
```

### USGS Conditions (API — per gauge)
```
Cron fires → data_source_links WHERE source_type = 'usgs_gauge'
  → Batch query USGS API by gauge IDs (group by state for efficiency)
  → For each gauge response:
      → Insert conditions record with water_body_id
      → Update data_source_links.last_refreshed_at + last_value_summary
  → No Haiku needed — structured API response
```

### NOAA Weather (API — per coordinates)
```
Cron fires → water_bodies with stale weather (forecast fetched_at > 6 hours)
  → For each water body:
      → Query NOAA API with coordinates
      → Upsert weather_forecasts (7-day forecast)
      → Update data_source_links.last_refreshed_at
  → No Haiku needed — structured API response
```

### Health Status Auto-Update
```
-- Run periodically (every 15 min)
UPDATE data_source_links
SET health_status = CASE
    WHEN last_refreshed_at IS NULL THEN 'unknown'
    WHEN last_refreshed_at < NOW() - (refresh_frequency_hours * INTERVAL '2 hours') THEN 'stale'
    ELSE 'healthy'
END
WHERE health_status != 'broken';  -- broken requires manual intervention

-- Auto-break sources with consecutive failures
UPDATE source_catalog
SET status = 'broken'
WHERE consecutive_failures >= 3 AND status = 'active';
```

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| Scrape returns HTTP error | Log to scrape_logs, increment source_catalog.consecutive_failures, serve cached data |
| Haiku returns invalid JSON | Should not happen with structured outputs; if it does, log error, mark source broken |
| Water body name not in bible | Log in scrape_logs.unmatched_names, skip event, surface in health dashboard for bible expansion |
| Species name not recognized | Store with species_id = NULL, species_raw preserved, needs_review = true |
| Duplicate stocking event | Caught by dedup unique index, increment records_duplicated counter, skip |
| USGS API rate limit hit | Backoff and retry, batch requests by state to reduce call count |
| NOAA API down | Weather becomes stale, health_status → 'stale', retry on next cycle |
| Source format changes | consecutive_failures → 3 → status = 'broken' → alert → manual prompt update (self-healing in Phase 2) |

---

## Testing Strategy

1. **Schema validation:** Run migrations against a fresh Supabase project, verify all tables/indexes/functions created without errors.
2. **Constraint testing:** Attempt inserts that violate CHECK constraints, unique indexes, and FK constraints — verify they're rejected.
3. **Geospatial queries:** Insert sample water bodies with coordinates, verify PostGIS spatial queries return correct results (e.g., ST_DWithin for proximity).
4. **Alias lookup:** Insert aliases, verify find_water_body() returns correct matches (case-insensitive, state-scoped).
5. **Species lookup:** Insert species aliases, verify find_species() normalizes correctly.
6. **Deduplication:** Insert duplicate stocking events, verify the unique index prevents double-inserts.
7. **RLS:** Verify service role has full access, anon role is blocked (or permissive per current policy).
8. **Health status:** Simulate stale/broken conditions, verify auto-update query sets correct statuses.

---

## Migration Strategy

All schema changes managed via Supabase CLI:

```bash
supabase init                           # initialize project
supabase migration new create_schema    # create migration file
supabase db push                        # apply to remote
supabase db reset                       # reset local for testing
```

Migrations stored in `supabase/migrations/` in the repository, version controlled with git.

Ordering:
1. Extensions (PostGIS, pg_trgm, uuid-ossp)
2. Core tables (water_bodies, species)
3. Relationship tables (aliases, data_source_links)
4. Time-series tables (stocking_events, conditions, weather_forecasts, ice_reports)
5. Scraping infrastructure (source_catalog, prompt_templates, scrape_logs)
6. Auth stubs (profiles, user_favorites)
7. Functions (find_water_body, find_species)
8. RLS policies
9. Seed data (species list, initial species aliases)
