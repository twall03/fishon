-- ============================================
-- 008: Replace JSONB attributes with real columns
-- Every water body gets all attributes. Show what's populated, hide what's NULL.
-- ============================================

-- Add real attribute columns
ALTER TABLE water_bodies
    ADD COLUMN surface_acres    FLOAT,
    ADD COLUMN max_depth_ft     FLOAT,
    ADD COLUMN avg_flow_cfs     FLOAT,
    ADD COLUMN elevation_ft     FLOAT,
    ADD COLUMN boat_ramps       INT,
    ADD COLUMN access_type      TEXT,
    ADD COLUMN has_stocking      BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN has_flow_data     BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN has_level_data    BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN has_ice_data      BOOLEAN NOT NULL DEFAULT false;

-- Drop JSONB column and its GIN index
DROP INDEX IF EXISTS idx_water_bodies_attributes;
ALTER TABLE water_bodies DROP COLUMN attributes;
