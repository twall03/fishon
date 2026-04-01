---
name: Bible Strategy — OSM + USGS
description: Two-source bible strategy decided 2026-03-24. OSM for standing water, USGS gauges for rivers. Universal across all 50 states.
type: project
---

Two federal sources for the water body bible (ADR-003):

- **OSM** (Overpass API) = lakes, reservoirs, ponds. Pins match Mapbox map exactly.
- **USGS gauges** (Water Services API) = rivers. Each gauge = a section pin with real-time data and a location name like "PROVO RIVER NEAR HEBER, UT".
- **GNIS** = county backfill only (neither OSM nor USGS has county).

**Why:** Replaces the broken GNIS/NHDPlus/Sonnet patchwork that had duplicates, wrong coords, and inconsistent names.

**How to apply:** For any state: 2 API calls (OSM + USGS), GNIS enrichment for county, then wire NOAA + import stocking data.

See `.claude/decisions/003-osm-usgs-bible-sources.md` for full rationale.
