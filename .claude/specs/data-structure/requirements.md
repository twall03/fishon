# Requirements Document

## Introduction

FishOn's core data structure — the "bible" — on Supabase (PostgreSQL + PostGIS). This is the foundation every feature builds on. It defines how water bodies, stocking events, conditions, weather, and scraping infrastructure are stored, related, and queried. The schema must support state-by-state expansion, geospatial queries for the map layer, fuzzy name matching from scraped data, and future Supabase Auth integration for user-facing features.

Hosted on Supabase. Created and managed via Supabase CLI. PostGIS extension enabled for geospatial queries.

---

## Requirements

### Requirement 1: Supabase Project Setup

**User Story:** As a developer, I want the database hosted on Supabase with PostGIS enabled, so that I have managed PostgreSQL with geospatial support and a path to Supabase Auth.

#### Acceptance Criteria
1. WHEN the Supabase project is created THEN the system SHALL have PostgreSQL with the PostGIS extension enabled.
2. WHEN the project is initialized THEN the system SHALL be manageable via Supabase CLI (`supabase migration`, `supabase db push`).
3. WHEN the schema is defined THEN it SHALL be stored as versioned SQL migrations in the repository under `supabase/migrations/`.
4. WHEN the project is created THEN Row Level Security (RLS) SHALL be enabled on all tables to support future Supabase Auth integration.

---

### Requirement 2: Water Body Bible (Core Entity)

**User Story:** As the system, I need a canonical registry of fishable water bodies with geospatial data, so that every data point (stocking, conditions, weather) can be linked to a specific location on the map.

#### Acceptance Criteria
1. WHEN a water body is stored THEN it SHALL have: id (UUID), name, state (2-letter code), county, type (enum: lake, reservoir, river, creek, pond, stream), coordinates (PostGIS POINT), geometry (PostGIS GEOMETRY), attributes (JSONB), popularity_rank, status (enum: active, seasonal, closed, unverified), created_at, updated_at.
2. WHEN a water body has type `lake` or `reservoir` THEN `attributes` MAY include: surface_acres, max_depth_ft, has_stocking, has_level_data, boat_ramps.
3. WHEN a water body has type `river` or `creek` THEN `attributes` MAY include: usgs_gauge_id, avg_flow_cfs, has_flow_data, access_type.
4. WHEN a geospatial query is made (e.g., "waters within 50 miles") THEN the system SHALL return results using PostGIS spatial indexing on the `coordinates` column.
5. WHEN filtering by state THEN the system SHALL use an indexed `state` column for efficient per-state queries.
6. IF a water body is discovered via scraping but not yet verified THEN the system SHALL create it with `status: unverified`.

---

### Requirement 3: Water Body Aliases (Rosetta Stone)

**User Story:** As the scraping pipeline, I need to match inconsistent water body names from different sources to canonical bible entries, so that stocking events and conditions link to the correct water body.

#### Acceptance Criteria
1. WHEN an alias is stored THEN it SHALL have: id, water_body_id (FK), alias (text), source (enum: state_dwr, usgs, nhdplus, manual, scraped), is_primary (bool).
2. WHEN a scraped water body name is looked up THEN the system SHALL perform case-insensitive matching against all aliases for the given state.
3. WHEN multiple aliases exist for the same water body THEN exactly one SHALL be marked `is_primary = true`.
4. WHEN a new name variant is discovered during scraping THEN the system SHALL be able to insert it as a new alias with `source: scraped`.

---

### Requirement 4: Data Source Links (External System Wiring)

**User Story:** As the system, I need to know which USGS gauge, NHDPlus feature, and state DWR page maps to each water body, so that conditions, geometries, and scraping targets are correctly wired.

#### Acceptance Criteria
1. WHEN a data source link is stored THEN it SHALL have: id, water_body_id (FK), source_type (enum: usgs_gauge, noaa_station, state_dwr_page, nhdplus_feature), external_id (text), source_url (text, nullable).
2. WHEN a water body has a USGS gauge linked THEN the conditions pipeline SHALL use the `external_id` to query USGS for flow/level data.
3. WHEN a water body has multiple data sources of the same type THEN the system SHALL support multiple links (e.g., a river with 2 gauge stations).

---

### Requirement 5: Stocking Events (Time-Series)

**User Story:** As an angler, I want to see what fish were stocked, where, and when, so that I can plan trips to recently stocked waters.

#### Acceptance Criteria
1. WHEN a stocking event is stored THEN it SHALL have: id, water_body_id (FK), species (text, normalized), quantity (integer), date (date), source_agency (text), source_url (text), raw_text (text, nullable — original scraped text for audit), confidence_score (float 0-1), created_at.
2. WHEN checking for duplicates THEN the system SHALL use the composite key (water_body_id, species, date, quantity) to prevent duplicate inserts.
3. WHEN querying stocking events THEN the system SHALL support filtering by: state, species, date range, water_body_id, and recency (stocked this week / this month).
4. IF a stocking event has confidence_score < 0.7 THEN the system SHALL flag it for review by storing `needs_review: true`.

---

### Requirement 6: Conditions (USGS Time-Series)

**User Story:** As an angler, I want to see current river flows, lake levels, and water temperatures, so that I know real-time conditions before heading out.

#### Acceptance Criteria
1. WHEN a conditions record is stored THEN it SHALL have: id, water_body_id (FK), flow_cfs (float, nullable), level_ft (float, nullable), temp_f (float, nullable), timestamp (timestamptz), source (text — e.g., "USGS"), gauge_id (text).
2. WHEN conditions are queried THEN the system SHALL return the most recent record for the given water_body_id.
3. WHEN conditions data is older than 1 hour THEN the system SHALL indicate staleness to downstream consumers.

---

### Requirement 7: Weather Forecasts

**User Story:** As an angler, I want to see the weather forecast for a specific water body, so that I can plan around conditions.

#### Acceptance Criteria
1. WHEN a weather forecast is stored THEN it SHALL have: id, water_body_id (FK), forecast_date (date), temp_high_f (int), temp_low_f (int), wind_mph (int), precip_chance (float), summary (text), fetched_at (timestamptz).
2. WHEN a forecast is queried THEN the system SHALL return up to 7 days of forecast for the given water_body_id.
3. WHEN a forecast record is older than 6 hours THEN it SHALL be considered stale and eligible for refresh.

---

### Requirement 8: Canonical Species List

**User Story:** As the system, I need a canonical list of fish species with normalized names, so that "rainbow", "bows", "Rainbow Trout", and "Oncorhynchus mykiss" all map to the same species.

#### Acceptance Criteria
1. WHEN a species is stored THEN it SHALL have: id, common_name (canonical — e.g., "Rainbow Trout"), scientific_name (nullable), species_group (enum: trout, bass, panfish, catfish, walleye, pike, salmon, carp, other).
2. WHEN the system encounters a species name variant THEN it SHALL look up against `species_aliases` to find the canonical species_id.
3. WHEN a species alias is stored THEN it SHALL have: id, species_id (FK), alias (text — e.g., "bows", "rainbow", "RBT").

---

### Requirement 9: Scraping Infrastructure Tables

**User Story:** As the scraping pipeline, I need to track data sources, scrape runs, prompt versions, and health metrics, so that the system is observable and maintainable.

#### Acceptance Criteria
1. **Source Catalog:** WHEN a source is stored THEN it SHALL have: id, state (2-letter), name, url, source_type (enum: stocking, regulations, conditions, reports), format (enum: html_table, html_list, pdf, csv, api), scrape_frequency_hours (int), prompt_template_id (FK, nullable), status (enum: active, paused, broken, needs_review), last_scraped_at, created_at.
2. **Prompt Templates:** WHEN a prompt template is stored THEN it SHALL have: id, name, version (int), source_type, system_prompt (text), schema_json (JSONB), examples (JSONB, nullable), is_active (bool), created_at.
3. **Scrape Logs:** WHEN a scrape run completes THEN it SHALL log: id, source_id (FK), started_at, completed_at, http_status (int), response_size_bytes (int), records_extracted (int), records_stored (int), confidence_avg (float), errors (JSONB, nullable), prompt_template_id (FK).
4. WHEN a source's scrape log shows 3 consecutive failures THEN the source status SHALL be updated to `broken`.

---

### Requirement 10: Future-Proofing for Supabase Auth

**User Story:** As a developer, I want the schema to be ready for user accounts, favorites, and subscriptions, so that adding auth later doesn't require restructuring.

#### Acceptance Criteria
1. WHEN tables are created THEN all tables SHALL have RLS policies enabled (even if initially permissive).
2. WHEN the schema is designed THEN it SHALL include a `profiles` table stub (id referencing `auth.users`, display_name, subscription_tier, created_at) ready for Supabase Auth.
3. WHEN the schema is designed THEN it SHALL include a `user_favorites` table stub (user_id, water_body_id, notify_on_stocking bool, created_at) ready for future use.
4. WHEN RLS policies are created THEN they SHALL initially allow all access (to be tightened when auth is implemented).
