-- ============================================
-- 006: Functions and Triggers
-- ============================================

-- Auto-update updated_at timestamp on row modification
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to tables with updated_at
CREATE TRIGGER trg_water_bodies_updated_at
    BEFORE UPDATE ON water_bodies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_data_source_links_updated_at
    BEFORE UPDATE ON data_source_links
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_source_catalog_updated_at
    BEFORE UPDATE ON source_catalog
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- Lookup Functions (used by scraping pipeline)
-- ============================================

-- Find a water body by alias name, scoped to a state
-- Returns the water_body_id or NULL if not found
CREATE OR REPLACE FUNCTION find_water_body(
    p_alias TEXT,
    p_state CHAR(2)
) RETURNS UUID AS $$
    SELECT wb.id
    FROM water_body_aliases wba
    JOIN water_bodies wb ON wb.id = wba.water_body_id
    WHERE wba.alias_lower = LOWER(TRIM(p_alias))
      AND wb.state = p_state
    LIMIT 1;
$$ LANGUAGE sql STABLE;

-- Find a water body using fuzzy/trigram matching (fallback when exact match fails)
-- Returns top 5 candidates with similarity scores
CREATE OR REPLACE FUNCTION find_water_body_fuzzy(
    p_alias TEXT,
    p_state CHAR(2),
    p_threshold FLOAT DEFAULT 0.3
) RETURNS TABLE(water_body_id UUID, water_body_name TEXT, alias_matched TEXT, similarity FLOAT) AS $$
    SELECT
        wb.id AS water_body_id,
        wb.name AS water_body_name,
        wba.alias AS alias_matched,
        similarity(wba.alias_lower, LOWER(TRIM(p_alias))) AS similarity
    FROM water_body_aliases wba
    JOIN water_bodies wb ON wb.id = wba.water_body_id
    WHERE wb.state = p_state
      AND similarity(wba.alias_lower, LOWER(TRIM(p_alias))) > p_threshold
    ORDER BY similarity DESC
    LIMIT 5;
$$ LANGUAGE sql STABLE;

-- Find a species by alias name
-- Returns the species_id or NULL if not found
CREATE OR REPLACE FUNCTION find_species(p_alias TEXT) RETURNS UUID AS $$
    SELECT species_id
    FROM species_aliases
    WHERE alias_lower = LOWER(TRIM(p_alias))
    LIMIT 1;
$$ LANGUAGE sql STABLE;

-- Get all data sources and their health for a water body
CREATE OR REPLACE FUNCTION get_water_body_sources(p_water_body_id UUID)
RETURNS TABLE(
    source_type TEXT,
    external_id TEXT,
    source_url TEXT,
    health_status TEXT,
    last_refreshed_at TIMESTAMPTZ,
    last_value_summary TEXT,
    refresh_frequency_hours INT
) AS $$
    SELECT
        dsl.source_type,
        dsl.external_id,
        dsl.source_url,
        dsl.health_status,
        dsl.last_refreshed_at,
        dsl.last_value_summary,
        dsl.refresh_frequency_hours
    FROM data_source_links dsl
    WHERE dsl.water_body_id = p_water_body_id
    ORDER BY dsl.source_type;
$$ LANGUAGE sql STABLE;
