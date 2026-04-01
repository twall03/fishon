-- ============================================
-- 003: Time-Series Tables
-- ============================================

-- Stocking Events: accumulates forever
CREATE TABLE stocking_events (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    water_body_id     UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    species_id        UUID REFERENCES species(id),
    species_raw       TEXT NOT NULL,
    quantity          INT,
    date              DATE NOT NULL,
    source_agency     TEXT NOT NULL,
    source_url        TEXT NOT NULL,
    raw_text          TEXT,
    confidence_score  FLOAT NOT NULL DEFAULT 1.0 CHECK (confidence_score BETWEEN 0 AND 1),
    needs_review      BOOLEAN NOT NULL DEFAULT false,
    scrape_log_id     UUID,  -- FK added after scrape_logs table exists
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_stocking_dedup
    ON stocking_events(water_body_id, species_id, date, quantity)
    WHERE quantity IS NOT NULL;

CREATE INDEX idx_stocking_water_body ON stocking_events(water_body_id);
CREATE INDEX idx_stocking_date ON stocking_events(date DESC);
CREATE INDEX idx_stocking_species ON stocking_events(species_id);
CREATE INDEX idx_stocking_review ON stocking_events(needs_review) WHERE needs_review = true;

-- Conditions: USGS real-time data (ephemeral, 90-day retention target)
CREATE TABLE conditions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    water_body_id   UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    flow_cfs        FLOAT,
    level_ft        FLOAT,
    temp_f          FLOAT,
    timestamp       TIMESTAMPTZ NOT NULL,
    source          TEXT NOT NULL DEFAULT 'USGS',
    gauge_id        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conditions_latest ON conditions(water_body_id, timestamp DESC);
CREATE INDEX idx_conditions_gauge ON conditions(gauge_id);

-- Weather Forecasts: NOAA, 7-day forecasts (upsert on refresh)
CREATE TABLE weather_forecasts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    water_body_id   UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    forecast_date   DATE NOT NULL,
    temp_high_f     INT,
    temp_low_f      INT,
    wind_mph        INT,
    precip_chance   FLOAT,
    summary         TEXT,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_weather_dedup ON weather_forecasts(water_body_id, forecast_date);
CREATE INDEX idx_weather_water_body ON weather_forecasts(water_body_id, forecast_date);

-- Ice Reports: seasonal, community + agency
CREATE TABLE ice_reports (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    water_body_id    UUID NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
    thickness_in     FLOAT,
    quality          TEXT CHECK (quality IN ('good', 'fair', 'poor', 'unsafe', 'unknown')),
    reporter         TEXT,
    report_source    TEXT NOT NULL CHECK (report_source IN ('agency', 'community', 'scraped')),
    report_date      DATE NOT NULL,
    notes            TEXT,
    confidence_score FLOAT NOT NULL DEFAULT 1.0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ice_water_body ON ice_reports(water_body_id, report_date DESC);
