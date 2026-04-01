# ADR-003: Two-Source Bible — OSM for Standing Water, USGS for Rivers

**Date:** 2026-03-24
**Status:** accepted

## Context

The water body bible was built from 3+ sources (GNIS, NHDPlus HR, Sonnet research) and had duplicates, wrong coordinates, and inconsistent names. Mapbox renders OpenStreetMap data — the map already shows every water body correctly. Meanwhile, rivers need section-level pins (not one centroid for a 100-mile river), and USGS already has gauges at specific points along every major river.

## Decision

**Two federal sources. Both cover all 50 states. Both are structured APIs.**

| Water Type | Source | API | What It Provides |
|-----------|--------|-----|------------------|
| Lakes, reservoirs, ponds | **OpenStreetMap** (via Overpass API) | `overpass-api.de/api/interpreter` | Name, type, center-point coordinates. Matches what Mapbox renders. |
| Rivers, streams | **USGS gauges** (via Water Services API) | `waterservices.usgs.gov/nwis/site/` | Name with location context ("PROVO RIVER NEAR HEBER, UT"), ground-truthed coordinates, real-time flow/level/temp. |

### Why OSM for lakes
- One OSM feature = one lake = one pin. Clean 1:1 mapping.
- Coordinates land exactly on the water feature users see on the Mapbox map.
- Covers every named lake, reservoir, and pond including small community ponds.
- 1,300+ unique named standing water features in Utah alone.

### Why USGS for rivers
- Rivers are long. A single centroid for "Provo River" lands in the middle of nowhere useful.
- USGS gauges are specific points on specific rivers with location names like "PROVO RIVER NEAR HEBER, UT".
- Each gauge = a natural "section" pin with real-time data already attached.
- Ground-truthed coordinates (physically installed instruments).
- Major fishable rivers have multiple gauges = multiple pins (Weber River has 10, Provo River has 4).
- 178 active gauges covering 141 unique rivers in Utah. ~9,000+ nationally.

### What about rivers without gauges?
- Small creeks/streams without USGS gauges are typically not destination fishing spots.
- If a river has no gauge, it stays in the bible from its original source (DWR, Sonnet research) but won't have real-time conditions.
- Future option: add OSM river entries as fallback for ungauged rivers.

### County data
- OSM and USGS don't provide county. GNIS remains the source for county backfill via `pipeline/enrich_gnis.py`.

## State Onboarding Process (Universal)

For any new state:

1. **OSM Overpass query** — download all named lakes/reservoirs/ponds → insert as bible entries
2. **USGS gauge query** — download all active stream gauges → insert as river section entries
3. **GNIS enrichment** — backfill county for all entries
4. **NOAA wiring** — create weather links using coordinates
5. **DWR stocking import** — match stocking reports to bible via aliases
6. **Verify** — match rate >95%, coordinates within state bbox

Two API calls for the foundation. Same script, any state code.

## Coordinate Hierarchy

| Source | Used For | Priority |
|--------|----------|----------|
| OSM center point | Lakes, reservoirs, ponds | Primary for standing water |
| USGS gauge location | River sections | Primary for flowing water |
| GNIS point | County backfill, small water gap-fill | Metadata only |
| NHDPlus HR centroid | Legacy fallback | Deprecated — OSM replaces this |
| AI/Sonnet research | Never | Banned (ADR-002 lesson) |

## Schema

Water bodies table tracks provenance:
- `osm_id BIGINT` — OSM way/relation ID (for standing water)
- `osm_type TEXT` — 'way' or 'relation'
- `coord_source TEXT` — 'osm', 'usgs', 'gnis', 'nhdplus', 'legacy'

River sections use existing `parent_id` for hierarchy when needed.

## Consequences

- Every lake pin lands exactly on the water feature visible on the Mapbox map
- Every river pin is at a real monitoring point with live data
- State onboarding is 2 API calls + enrichment, not weeks of Sonnet research
- No AI-guessed coordinates anywhere in the system
- Consistent process for all 50 states
- Gap: ungauged rivers/streams have no pin. Acceptable tradeoff — they're rarely fished.
