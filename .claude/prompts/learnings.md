# Prompt Library — Learnings

What worked, what didn't, and what to change for the next state.

---

## Format

After each state onboarding, add an entry:

```markdown
## {STATE_CODE} — {STATE_NAME} ({date completed})

### Source Discovery (01)
- What worked:
- What didn't:
- Prompt changes made:

### Water Body Sweep (02)
- Total water bodies found:
- Missed any? How discovered?
- What worked:
- What didn't:
- Prompt changes made:

### Geocode & Enrich (03)
- % high confidence coordinates:
- % needing manual review:
- What worked:
- What didn't:
- Prompt changes made:

### USGS Matching (04)
- Gauges matched: X / Y total
- False matches caught:
- What worked:
- What didn't:
- Prompt changes made:

### Species Intel (05)
- Coverage: X% of water bodies have species data
- Accuracy issues found:
- What worked:
- What didn't:
- Prompt changes made:

### Reference Verification (06)
- Sources verified: X / Y
- Broken found:
- What worked:
- What didn't:

### Overall
- Time to complete onboarding:
- Biggest surprise:
- What to do differently next time:
```

---

## State Entries

### UT — Utah (2026-03-18, COMPLETE)

#### Source Discovery (01)
- **Sonnet agent, ~14 min runtime, 123 tool uses**
- What worked: Found 40+ sources, verified every URL, prioritized correctly. Naturally found State Parks conditions pages, DWR Fish Utah Planner, fly shop reports, Bureau of Reclamation data.
- What didn't: Nothing major
- Prompt changes: Added notes about dam/reservoir operators and state fishing apps

#### Water Body Sweep (02)
- **Sonnet agent, ~38 min runtime, 99 tool uses**
- Total water bodies found: **450** (120 reservoirs, 87 lakes, 66 creeks, 64 rivers, 58 ponds, 25 streams, 20 access points, 10 marinas)
- Missed any? Uinta backcountry lakes with alphanumeric codes only (A-1, B-3, etc.) — excluded, could add later
- What worked: Multi-source sweep (stocking reports + fishing guide PDF + regulations + USGS + ArcGIS electrofishing MapServer)
- Key insight: Sonnet found the ArcGIS layer on wrimaps.utah.gov that had backcountry lakes not in stocking data
- Prompt changes: Added note about alphanumeric-coded backcountry lakes

#### Geocode & Enrich (03)
- **Sonnet agent, ~6 min runtime, 26 tool uses**
- High confidence: 265/450 (59%)
- Medium confidence: 185/450 (41%)
- Needing manual review: 0
- What worked: All coordinates within Utah bounds, zero duplicates, zero positive longitudes
- USGS cross-validation: 107/155 rivers matched to gauges, 29 "far" matches all explainable (different river sections)

#### Automated Validation
- **Python script, instant**
- Bounding box check: 0 out of bounds
- Duplicate coordinates: 0
- Key waters check: 20/20 passed (Strawberry, Flaming Gorge, Provo, Green, etc.)
- County coverage: 100%
- Species coverage: 99% (444/450)

#### Database Import
- **Python script, ~2 min**
- 450 water bodies inserted to Supabase
- 704 aliases inserted
- 1,052 water_body_species entries
- 895 data_source_links (150 USGS, 450 NOAA, 295 DWR)
- Zero failures

#### Pipeline Test (Haiku stocking extraction)
- **Pipeline run, ~2 min**
- Input: Utah DWR AJAX endpoint (47KB HTML)
- Haiku extracted: 119 events (auto-chunked into 3 calls of ~20KB each)
- Validated: 119/119 matched to bible (100% match rate)
- Stored: 113 new events, 6 actual duplicates
- Fix applied: Changed from upsert to insert with exception handling for dedup index
- Fix applied: Added auto-chunking by `</tr>` boundaries for large pages

#### USGS + NOAA
- USGS: 150 gauge readings stored (flow CFS, level ft, temp)
- NOAA: 70 weather forecasts stored (7-day for 10 water bodies)

#### Overall
- **Total time: ~1 hour of agent work + pipeline building**
- Biggest surprise: 100% match rate on first pipeline run — the alias table worked perfectly
- Biggest lesson: Large HTML pages need chunking for Haiku (47KB fails, 20KB chunks work)
- What to do next time: Same exact process, but faster since pipeline is built

---

## Execution Recipe (copy for each new state)

This is the exact sequence that worked for Utah. Repeat for every state:

### Step 1: Source Discovery (~15 min)
```
Deploy Sonnet agent with prompt 01_source_discovery.md
→ Inject STATE_NAME and STATE_CODE
→ Review output, save to .claude/states/{state}/sources.md
```

### Step 2: Water Body Sweep (~40 min)
```
Deploy Sonnet agent with prompt 02_water_body_sweep.md
→ Inject sources from Step 1
→ Output: JSON array of water bodies
→ Save to .claude/states/{state}/water_bodies.json
```

### Step 3: Geocode & Enrich (~10 min)
```
Deploy Sonnet agent with prompt 03_geocode_enrich.md
→ Inject water body list from Step 2
→ Output: enriched JSON with coordinates
→ Save to .claude/states/{state}/water_bodies_geocoded.json
```

### Step 4: USGS Gauge Query (instant)
```python
# Query USGS legacy API for all gauges in state
url = f"https://waterservices.usgs.gov/nwis/site/?format=rdb&stateCd={STATE}&siteType=ST&siteStatus=active&hasDataTypeCd=iv"
→ Parse TSV, extract gauge_id, name, lat, lon
→ Save to /tmp/{state}_usgs_gauges.json
```

### Step 5: Automated Validation (instant)
```python
# Run validation script checking:
# 1. Bounding box (all coords within state)
# 2. Duplicate coordinates
# 3. USGS cross-validation (rivers vs gauges)
# 4. Key waters spot check
# 5. Completeness (county, species, confidence)
```

### Step 6: Database Import (~2 min)
```python
# Batch insert to Supabase:
# 1. water_bodies (with PostGIS POINT coordinates)
# 2. water_body_aliases (all name variants)
# 3. water_body_species (species per water body)
# 4. data_source_links (USGS gauges + NOAA coords + DWR stocking)
```

### Step 7: Seed Source + Prompt (~1 min)
```python
# Insert into prompt_templates (state-specific Haiku prompt)
# Insert into source_catalog (DWR stocking URL)
```

### Step 8: Pipeline Test (~2 min)
```bash
python -m pipeline --source <source_uuid>
# Verify: events extracted > 0, match rate > 95%, stored > 0
```

### Step 9: Update Records
```
Update .claude/states/{state}/onboard.md
Update .claude/prompts/learnings.md
Update /case current state section
```
