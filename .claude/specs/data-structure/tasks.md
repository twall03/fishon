# Implementation Plan

- [x] 1. Initialize Supabase project
  - Run `supabase init` in the repo root
  - Link to a new Supabase project (or create one via CLI)
  - Verify PostGIS, pg_trgm, and uuid-ossp extensions are available
  - _Requirements: 1_

- [x] 2. Create core schema migration
- [x] 2.1 Create `water_bodies` table with PostGIS columns
  - Define table with all columns, CHECK constraints, and JSONB attributes
  - Create all indexes (state, type, status, coordinates GIST, geometry GIST, parent_id, attributes GIN)
  - Add `updated_at` auto-update trigger
  - _Requirements: 2_

- [x] 2.2 Create `water_body_aliases` table
  - Define table with generated `alias_lower` column
  - Create indexes (alias_lower, water_body_id, trigram GIN)
  - Create unique partial index for `is_primary`
  - _Requirements: 3_

- [x] 2.3 Create `data_source_links` table
  - Define table with health tracking columns (last_refreshed_at, health_status, refresh_frequency_hours, last_value_summary)
  - Create indexes (water_body_id, source_type, health_status, last_refreshed_at)
  - _Requirements: 4_

- [x] 2.4 Create `species` and `species_aliases` tables
  - Define species table with common_name, scientific_name, species_group
  - Define species_aliases table with generated `alias_lower` column
  - Create unique index on alias_lower
  - _Requirements: 8_

- [x] 3. Create time-series tables migration
- [x] 3.1 Create `stocking_events` table
  - Define table with confidence_score, needs_review, scrape_log_id, raw_text audit fields
  - Create deduplication unique index on (water_body_id, species_id, date, quantity)
  - Create query indexes (water_body_id, date DESC, species_id, needs_review)
  - _Requirements: 5_

- [x] 3.2 Create `conditions` table
  - Define table with flow_cfs, level_ft, temp_f, timestamp, gauge_id
  - Create index on (water_body_id, timestamp DESC) for latest-value queries
  - _Requirements: 6_

- [x] 3.3 Create `weather_forecasts` table
  - Define table with 7-day forecast fields
  - Create unique index on (water_body_id, forecast_date) for upsert
  - _Requirements: 7_

- [x] 3.4 Create `ice_reports` table
  - Define table with thickness, quality, reporter, report_source
  - Create index on (water_body_id, report_date DESC)
  - _Requirements: 5, 7_

- [x] 4. Create scraping infrastructure migration
- [x] 4.1 Create `prompt_templates` table
  - Define table with system_prompt, schema_json, examples, species_map, version, is_active
  - Create indexes (state + source_type, unique active per state+type)
  - NOTE: Must be created before source_catalog due to FK dependency
  - _Requirements: 9_

- [x] 4.2 Create `source_catalog` table
  - Define table with state, url, format, scrape_frequency, consecutive_failures, prompt_template_id FK
  - Create indexes (state, status, next-scrape scheduling)
  - _Requirements: 9_

- [x] 4.3 Create `scrape_logs` table
  - Define table with full audit fields: records_extracted, records_stored, records_duplicated, records_unmatched, unmatched_names JSONB, raw_snapshot_url
  - Create indexes (source_id + started_at DESC, status, unmatched)
  - _Requirements: 9_

- [x] 5. Create auth stubs and RLS migration
- [x] 5.1 Create `profiles` and `user_favorites` stub tables
  - Define profiles referencing auth.users
  - Define user_favorites with notify preferences
  - Create unique index on (user_id, water_body_id)
  - _Requirements: 10_

- [x] 5.2 Enable RLS on all tables with permissive policies
  - Enable RLS on every table
  - Create permissive public read + user-scoped write policies
  - _Requirements: 10_

- [x] 6. Create database functions migration
- [x] 6.1 Create `find_water_body(alias, state)` function
  - Case-insensitive lookup via alias_lower, state-scoped through join
  - Returns UUID or NULL
  - _Requirements: 3_

- [x] 6.2 Create `find_species(alias)` function
  - Case-insensitive lookup via species_aliases.alias_lower
  - Returns UUID or NULL
  - _Requirements: 8_

- [x] 6.3 Create `updated_at` auto-trigger function
  - Generic trigger function that sets updated_at = NOW() on UPDATE
  - Attached to water_bodies, data_source_links, source_catalog, profiles
  - _Requirements: 2, 4_

- [x] 6.4 Create `find_water_body_fuzzy(alias, state, threshold)` function
  - Trigram similarity matching for when exact match fails
  - Returns top 5 candidates with similarity scores
  - _Requirements: 3_

- [x] 6.5 Create `get_water_body_sources(water_body_id)` function
  - Returns all data sources and their health for a given water body
  - _Requirements: 4_

- [x] 7. Seed canonical species data
  - 35 species inserted across trout, bass, panfish, catfish, walleye, pike, salmon, carp, other
  - Common aliases for each (e.g., Rainbow Trout: "rainbow", "bows", "RBT", "bow")
  - Stored as seed migration (007)
  - _Requirements: 8_

- [x] 8. Push migrations and verify
  - All 7 migrations applied to remote Supabase project (yibkspvmihypiahemgta)
  - 35 species verified via REST API
  - Species aliases verified (e.g., "bows" → Rainbow Trout)
  - Water bodies table exists and is queryable (empty, ready for bible building)
  - All tables have RLS enabled
  - _Requirements: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10_
