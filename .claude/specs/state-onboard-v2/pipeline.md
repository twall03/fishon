# State Onboarding Pipeline v2

**The right way. One unified process. No patches.**

This document defines the ONLY acceptable way to populate data for a state. Every step must complete and validate before the next begins. No shortcuts. No AI guessing.

---

## Principles

1. **The data is the product.** Wrong data is worse than no data.
2. **One source of truth per data type.** Not multiple sources stitched together.
3. **Validate before import, not after.** If it can't be validated, don't import it.
4. **Authoritative sources only.** State agency planners, NHDPlus, USGS. Never AI guessing.
5. **Aliases before imports.** The state's exact water body names must be in the alias table BEFORE importing stocking events.

---

## The Pipeline (in order, no skipping)

### Step 1: State Agency Planner → Water Bodies + Species

**Source:** The state's official fishing planner/database.
- Utah: DWR Fish Utah Planner (`dwrapps.utah.gov/fishing/fStart`)
- Idaho: IDFG Fishing Planner API (`idfg.idaho.gov/ifwis/fishingPlanner/`)
- Montana: FWP FishMT (`myfwp.mt.gov/fishMT/`)
- Wyoming: WGFD ArcGIS Fishing Guide FeatureServer

**What we get:** Water body name, type, county, species present (survey-confirmed).

**What we store:**
- `water_bodies`: name, state, county, type
- `water_body_species`: species confirmed by state agency surveys (confidence: 1.0, data_source: "{state}_agency_planner")

**Validation:** Every water body must have at least a name, state, county, and type. Species must resolve to our canonical species table.

### Step 2: NHDPlus HR → Coordinates

**Source:** USGS NHDPlus HR MapServer
- Layer 9 (NHDWaterbody): polygons for lakes/reservoirs → centroid = pin location
- Layer 3 (NetworkNHDFlowline): lines for rivers/streams → midpoint = pin location

**What we store:**
- `water_bodies.coordinates`: PostGIS POINT from NHDPlus polygon/line centroid

**Validation:**
- Every coordinate must be within the state's bounding box
- No duplicate coordinates
- No zero coordinates
- Lakes/reservoirs get polygon centroids (exact center of water body)
- Rivers get flowline midpoints or USGS gauge coordinates

**Fallback for unmatched waters:** USGS gauge coordinates for rivers. For waters that can't be matched to NHDPlus, mark as `status: unverified` and DO NOT show on map.

### Step 3: Stocking Report Names → Aliases

**Source:** The state's stocking report page.

**Before importing any stocking data**, scrape the stocking report and extract EVERY unique water body name the state uses. Add each as an alias in `water_body_aliases` linked to the correct bible entry.

**Why this step exists:** DWR uses "DEER CR RES", our bible says "Deer Creek Reservoir". Without this alias, stocking events won't match. We learned this the hard way — 3,000+ events had to be deleted because aliases were missing.

**What we store:**
- `water_body_aliases`: each DWR/FWP/IDFG water body name → linked to correct water_body_id
- Source: "state_dwr_stocking"

**Validation:** Each alias must map to exactly one water body. If ambiguous, skip it and log for human review.

### Step 4: USGS Gauges → Data Source Links

**Source:** USGS Water Services API (by state code).

**What we store:**
- `data_source_links`: gauge_id → water_body_id, source_type = "usgs_gauge"

**Matching:** By gauge name + proximity to bible water bodies. Only exact or very high confidence matches.

### Step 5: NOAA → Data Source Links

**Source:** Derived from water body coordinates.

**What we store:**
- `data_source_links`: coordinates → water_body_id, source_type = "noaa_station"

### Step 6: Validation Gate

**Before proceeding to time-series data, ALL of the following must be true:**
- [ ] Every water body has coordinates within state bounds
- [ ] Every water body has at least one species from the state planner OR is marked as "no species data"
- [ ] Every water body that appears in stocking reports has its DWR name as an alias
- [ ] USGS gauges are wired to the correct rivers
- [ ] No duplicate water bodies, no duplicate aliases with conflicting targets
- [ ] Spot check: 10 known water bodies verified manually (name, location, species)

**If validation fails, FIX IT before importing time-series data.**

### Step 7: Stocking Events (time-series)

**Source:** State stocking report page/API.
**Matching:** EXACT alias match only. No fuzzy. If a name doesn't match, log it as unmatched. Never force-match.

### Step 8: USGS Conditions (time-series)

**Source:** USGS Water Services API.
**No matching needed** — gauge_id → water_body_id is already wired in Step 4.

### Step 9: NOAA Weather (time-series)

**Source:** NOAA NWS API.
**No matching needed** — coordinates are in data_source_links from Step 5.

---

## What NOT To Do

- ❌ AI-guess coordinates (use NHDPlus)
- ❌ AI-guess species (use state planner)
- ❌ Fuzzy-match stocking events (exact alias only)
- ❌ Import stocking before aliases are set up
- ❌ Import time-series before bible is validated
- ❌ Patch bad data after import (fix the pipeline, re-import clean)
- ❌ Move fast on data quality (move slow, get it right)
