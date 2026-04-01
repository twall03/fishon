# ADR-004: Species Data Source — State DWR Planners

**Date:** 2026-03-27
**Status:** accepted

## Context

Evaluated USGS Aquatic GAP (HUC8 watershed-level species) as a nationwide source. Validated against 5 Utah water bodies — **45% average accuracy**. Fails because:

1. Stocked species invisible (Rainbow Trout, Kokanee, Lake Trout, Walleye, Bass — all placed by hatchery)
2. HUC8 blurs cold-water streams with warm-water lakes
3. ~10 false positives per water body (watershed species, not lake species)
4. Historical data doesn't reflect modern stocking/chemical treatments

**No single nationwide API exists for per-water-body species.**

## Decision

**State DWR/DNR fishing planners are the only accurate source for species per water body.** Each state maintains their own survey-confirmed species data tied to individual waters.

| State | Source | URL | Format |
|-------|--------|-----|--------|
| Utah | DWR Fish Utah Planner | `dwrapps.utah.gov/fishing/fStart` | JS SPA (find API underneath) |
| Idaho | IDFG Fishing Planner | TBD | TBD |
| Montana | FWP Fishing Guide | TBD | TBD |
| Wyoming | WGFD Fishing Atlas | TBD | TBD |

### Why state DWR data is authoritative
- Based on actual fish surveys (electrofishing, netting, creel surveys)
- Reflects current stocking programs
- Updated when management changes (poisoning, restocking, invasive introductions)
- Per water body, not per watershed

### Why federal data doesn't work
- USGS Aquatic GAP: 45% accuracy, misses all stocked species
- NAS: Only non-indigenous species
- Water Quality Portal: Inconsistent coverage
- GBIF/iNaturalist: Community observations, not authoritative
- NatureServe: HUC8-level only, no API

## Process

For each state onboard:
1. Find the state DWR fishing planner/atlas
2. Reverse-engineer the underlying API (these are all JS SPAs with REST backends)
3. Pull species per water body
4. Match to bible via name + proximity
5. Insert into `water_body_species` with `data_source: '{state}_dwr_planner'`, `confidence: 1.0`

This is per-state work. Each state is a separate research + scraping task. Sonnet researches the API, Haiku does ongoing extraction if needed.

## Consequences

- Species data is accurate, survey-confirmed, per water body
- Requires per-state research (no shortcut)
- Fits naturally into the state onboarding process (Phase 3)
- State agency data is the gold standard — matches what anglers see in guidebooks
