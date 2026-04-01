# State Onboarding Playbook — v3 (OSM + USGS)

Onboard a new state into FishOn. Two API calls for the bible, then layer data on top.

**Usage:** `/state-onboard {STATE_CODE}` (e.g., `/state-onboard UT`)

**See:** ADR-003 for rationale on the two-source approach.

---

## The Two Sources

| Water Type | Source | API | What It Gives Us |
|-----------|--------|-----|------------------|
| Lakes, reservoirs, ponds | **OpenStreetMap** | Overpass API | Name, type, center-point coordinates. Matches Mapbox map. |
| Rivers, streams | **USGS gauges** | Water Services API | Name with location ("PROVO RIVER NEAR HEBER, UT"), ground-truthed coords, real-time data. |

**County data** comes from GNIS (neither OSM nor USGS has county).

---

## Phase 1: Bible Foundation (2 API calls)

### 1a. OSM — Standing Water

```bash
python3 pipeline/osm.py {STATE}
```

- Queries Overpass API for all named `natural=water` + `waterway` features in the state bbox
- Deduplicates lakes by name (prefers relations over ways)
- Deduplicates rivers by name (centroids all segments)
- Saves to `.claude/states/{state}/osm_water_features.json`

### 1b. OSM Migration — Insert Lakes/Reservoirs/Ponds

```bash
python3 -m pipeline.osm_migrate --state {STATE} --apply
```

- Inserts lakes, reservoirs, ponds from OSM into `water_bodies`
- Sets `coord_source='osm'`, stores `osm_id` and `osm_type`
- Creates primary alias for each
- Skips creeks/streams (those come from USGS)

### 1c. USGS — River Gauges

```bash
python3 -m pipeline.usgs_rivers --state {STATE} --apply
```

- Fetches all active stream gauges from USGS Water Services API
- Cleans gauge names ("PROVO RIVER NR HEBER, UT" → "Provo River — Near Heber")
- Creates river/creek entries with `coord_source='usgs'`
- Wires USGS gauge `data_source_links` automatically
- Wires NOAA weather links from coordinates

### 1d. GNIS — County Backfill

```bash
python3 -m pipeline.enrich_gnis --state {STATE} --apply
```

- Queries GNIS MapServer (Layer 6 + 7) for all water features
- Matches bible entries by name + proximity
- Backfills missing county from GNIS

**After Phase 1:**
- Every lake/reservoir/pond has a pin matching the Mapbox map
- Every gauged river has a pin at the monitoring station
- All entries have county data

---

## Phase 2: Source Discovery

Research the state's public fishing data sources.

- [ ] Find state DWR/DNR/Game & Fish stocking report
- [ ] Find fishing regulations page
- [ ] Find any "where to fish" guides
- [ ] Check for regional fishing reports
- [ ] Verify every URL is live
- [ ] Document in `.claude/states/{state}/sources.md`

---

## Phase 3: Data Layer — Wire Sources

### 3a. NOAA Weather

```bash
python3 -m pipeline --noaa-only --state {STATE} --noaa-limit 500
```

Run multiple times if needed (NOAA rate-limited). All waters get 7-day forecasts.

### 3b. USGS Conditions

```bash
python3 -m pipeline --usgs-only --state {STATE}
```

Fetches real-time flow/level/temp for all wired gauges.

### 3c. Stocking Events

```bash
python3 -m pipeline --state {STATE}
```

Scrapes state DWR stocking reports via Haiku. Matches to bible via exact alias lookup.

---

## Phase 4: Prompt Engineering

For each stocking source:
- [ ] Write Haiku extraction prompt with structured output schema
- [ ] Test on 3+ sample pages
- [ ] Accuracy >90%
- [ ] Store in `prompt_templates` table
- [ ] Register in `source_catalog`

---

## Phase 5: Verification

- [ ] Water bodies on map match what Mapbox renders
- [ ] Stocking events linked to correct waters (match rate >95%)
- [ ] USGS conditions flowing for gauged rivers
- [ ] NOAA weather available for all waters
- [ ] No orphaned FK references
- [ ] Pipeline runs 3x without intervention

Mark `.claude/states/{state}/onboard.md` as `CERTIFIED`.

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `pipeline/osm.py` | Download OSM water features for a state |
| `pipeline/osm_migrate.py` | Insert OSM lakes/reservoirs/ponds into bible |
| `pipeline/usgs_rivers.py` | Create USGS gauge-based river entries |
| `pipeline/enrich_gnis.py` | Backfill county from GNIS |
| `pipeline/__main__.py` | Run stocking/USGS/NOAA pipelines |

---

## Rules

- **OSM = standing water. USGS = rivers.** No other coordinate sources.
- **GNIS = county only.** Not for coordinates.
- **No AI-guessed coordinates.** Ever.
- **No fuzzy matching for stocking.** Exact alias match only.
- **Species from state agencies only.** Never AI.
- **Verify before import.** Don't patch after Taylor catches it.
