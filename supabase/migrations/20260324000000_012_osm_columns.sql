-- Add OSM provenance tracking to water_bodies
ALTER TABLE water_bodies ADD COLUMN IF NOT EXISTS osm_id BIGINT;
ALTER TABLE water_bodies ADD COLUMN IF NOT EXISTS osm_type TEXT;
ALTER TABLE water_bodies ADD COLUMN IF NOT EXISTS coord_source TEXT NOT NULL DEFAULT 'legacy';

CREATE UNIQUE INDEX IF NOT EXISTS idx_water_bodies_osm ON water_bodies(osm_id) WHERE osm_id IS NOT NULL;

-- Add 'merged' to status check constraint
ALTER TABLE water_bodies DROP CONSTRAINT IF EXISTS water_bodies_status_check;
ALTER TABLE water_bodies ADD CONSTRAINT water_bodies_status_check
    CHECK (status IN ('active', 'seasonal', 'closed', 'unverified', 'merged'));

-- Add 'osm' to water_body_aliases source check constraint
ALTER TABLE water_body_aliases DROP CONSTRAINT IF EXISTS water_body_aliases_source_check;
ALTER TABLE water_body_aliases ADD CONSTRAINT water_body_aliases_source_check
    CHECK (source IN ('state_dwr', 'usgs', 'nhdplus', 'manual', 'scraped', 'osm', 'state_dwr_stocking'));
