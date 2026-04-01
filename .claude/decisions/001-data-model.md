# ADR-001: Water Body Data Model

**Date:** 2026-03-18
**Status:** accepted

## Context

FishOn's core entity is the water body. Every feature (stocking events, conditions, weather, alerts, favorites) joins against `water_body_id`. The data model needs to handle different water body types (lakes, rivers, creeks, reservoirs) with different attributes while keeping queries simple and the map layer uniform.

Two approaches considered:
1. Separate tables per water body type (river_bodies, lake_bodies, etc.)
2. Single table with JSONB attributes column for type-specific fields

## Decision

**Single `water_bodies` table with JSONB `attributes` column.**

Core schema:
- `water_bodies` — universal fields (name, state, county, type, coordinates, geometry) + JSONB `attributes` for type-specific data
- `water_body_aliases` — every known name variant for fuzzy matching from scraped data
- `data_source_links` — maps water bodies to external system IDs (USGS gauge, NHDPlus feature, state DWR page)

State is a column with an index, not a separate schema or table partition. At projected scale (5,000-20,000 water bodies per state), PostgreSQL handles this trivially.

JSONB `attributes` holds type-specific fields:
- Rivers: usgs_gauge_id, avg_flow_cfs, access_type
- Lakes/Reservoirs: surface_acres, max_depth_ft, boat_ramps
- All types: has_stocking, has_flow_data, has_level_data

## Consequences

- One table, one query, one API endpoint for the map layer
- Adding new attributes never requires a migration
- JSONB is queryable and indexable in PostgreSQL
- Trade-off: no strict schema enforcement on type-specific fields (mitigated by application-level validation)
- The alias table is the critical piece for matching scraped data to canonical water bodies
