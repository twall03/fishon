# ADR-002: Dual-Source Water Body Geocoding (NHDPlus HR + GNIS)

**Date:** 2026-03-23
**Status:** accepted

## Context

Water body coordinates and metadata come from two complementary federal sources. Neither alone provides complete coverage:

- **NHDPlus HR** (USGS National Hydrography Dataset Plus High Resolution) — has polygon geometries for major lakes/reservoirs and flowlines for rivers/streams. Better centroids for big waters. But missing small waters, community ponds, and unnamed features.
- **GNIS** (Geographic Names Information System) — has point coordinates for every named water feature in the US, plus county names. Covers small waters NHDPlus misses. But only point geometry (no polygons), and coordinates are less precise for large features.

Utah was initially onboarded with NHDPlus only (v1). This left gaps: missing county data, small waters without coordinates, and no fallback when NHDPlus didn't have a match.

## Decision

**Use both sources in a layered approach: GNIS as foundation, NHDPlus as upgrade.**

### Source hierarchy (highest priority first):
1. **NHDPlus HR polygon centroid** — for lakes/reservoirs with polygon geometry
2. **GNIS point coordinate** — for everything else (small lakes, streams, springs)
3. **USGS gauge location** — fallback for rivers with active monitoring
4. **Unverified** — anything that can't match either source gets flagged, never published with AI-guessed coords

### GNIS provides:
- County name (authoritative — GNIS is the official US geographic names registry)
- Coordinates for small waters NHDPlus misses
- Feature classification (lake, reservoir, stream, etc.)

### NHDPlus provides:
- Superior coordinates via polygon centroids (averaged from actual shoreline geometry)
- Area data (areasqkm) for filtering significant vs tiny features
- Stream order for river importance ranking

### GNIS access method:
- **MapServer Layer 7** (Other Hydrographic Features): lakes, reservoirs, springs, etc.
- **MapServer Layer 6** (Streams): rivers, creeks, washes
- Endpoint: `https://carto.nationalmap.gov/arcgis/rest/services/geonames/MapServer/{layer}/query`
- Paginate at 2000 records per request
- Filter by `state_alpha` and `gaz_featureclass`
- Must set `outSR=4326` for WGS84 coordinates

### Disambiguation:
When multiple GNIS features share a name (e.g., "Hidden Lake" in 3 counties), use proximity to existing bible coordinates to pick the correct one. Matches >50km apart are flagged as suspicious.

## Pipeline integration

### New state onboard (onboard_v2.py):
1. Download GNIS (both layers) → foundation: name, county, initial coords
2. Download NHDPlus HR → upgrade: polygon centroids replace GNIS points for big waters
3. Import to bible with both sources recorded

### Existing state enrichment (enrich_gnis.py):
1. Download GNIS + NHDPlus for the state
2. Match bible entries to GNIS by name + proximity
3. Backfill missing county from closest GNIS match
4. Report unmatched entries and GNIS-only waters
5. Dry run by default, `--apply` to write changes

## Consequences

- Every state onboard now gets county data from day one
- Small waters that NHDPlus misses are covered by GNIS
- County mismatches surface data quality issues in the bible
- 5,000+ GNIS-only waters per state can be evaluated as potential bible additions
- Process is repeatable: same script, any state code
