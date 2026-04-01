# Sonnet Prompt: Comprehensive Water Body Sweep

**Version:** 1
**Purpose:** Build the complete water body bible for a state — every fishable water, not just the popular ones
**Deployed by:** Case (Opus)
**Output:** Structured JSON list of every fishable water body for database import

---

## Prompt

```
You are building a comprehensive database of EVERY fishable water body in {STATE_NAME} ({STATE_CODE}).

This is not "top 100" — this is a full sweep. Every lake, reservoir, river, creek, pond, stream, and marina that an angler might fish. If the state manages it, stocks it, monitors it, or people fish there — it goes in the list.

### Your Sources (found during source discovery)
{PASTE_SOURCES_FROM_PHASE_1}

### Your Tasks

#### 1. Extract from stocking reports
Go to the stocking report source and extract EVERY unique water body name that appears.
- Include historical data — a water that was stocked 2 years ago but not recently still goes in the bible
- Record the exact name the state uses (this becomes an alias for matching)

#### 2. Extract from fishing guides / "where to fish"
If the state has a fishing guide, atlas, or "where to fish" page:
- Extract every water body listed
- Include waters that are NOT stocked (wild/native fisheries, catch-and-release waters)
- These are the rivers and streams that stocking reports miss

#### 3. Extract from regulations
Scan the fishing regulations for water bodies mentioned by name:
- Special regulation waters (slot limits, catch-and-release, gear restrictions)
- These are often the most popular/important fisheries
- Record any water-body-specific regulations for later use

#### 4. Cross-reference with USGS
USGS gauge stations for {STATE_CODE} have been queried. Cross-reference gauge station names with your water body list:
- Match gauges to existing water bodies
- Add any monitored rivers/streams not already in your list

#### 5. Classify each water body
For EVERY water body, determine:
- **name**: canonical display name (proper capitalization)
- **type**: lake | reservoir | river | creek | pond | stream | marina | access_point
- **county**: county or region if available (critical for disambiguation)
- **state**: {STATE_CODE}
- **is_stocked**: true/false based on stocking data
- **known_species**: list of species known to be present (from stocking data, fishing guides)
- **special_regulations**: any water-body-specific rules
- **name_variants**: every name variant you've seen across sources (these become aliases)

### Output Format

Return a JSON array. One object per water body:

```json
[
  {
    "name": "Strawberry Reservoir",
    "type": "reservoir",
    "county": "Wasatch",
    "state": "{STATE_CODE}",
    "is_stocked": true,
    "known_species": ["Rainbow Trout", "Cutthroat Trout", "Kokanee Salmon"],
    "special_regulations": "Cutthroat trout: immediate release required",
    "name_variants": ["Strawberry Reservoir", "Strawberry Res", "Strawberry"],
    "source_notes": "Found in: stocking reports, fishing guide, special regulations"
  }
]
```

### Critical Rules

1. **COMPREHENSIVE over fast.** Missing a major river is worse than taking extra time.
2. **Include small waters.** Community ponds, small creeks, urban fishing spots — if the state stocks it or manages it, include it.
3. **Separate entries for multi-section waters.** A long river with multiple access points, gauge stations, or regulation zones should get separate entries per section (e.g., "Provo River - below Deer Creek Dam", "Provo River - Provo Canyon").
4. **Separate entries for multi-state waters.** Flaming Gorge gets entries for each state it's in, with marinas/access points as separate entries.
5. **Record where you found each water body** in source_notes. This is the audit trail.
6. **When in doubt, INCLUDE it.** We can remove false positives. We can't find false negatives.
7. **Do NOT make up water bodies.** Only include waters you found in actual state sources.
```

---

## Success Criteria

- [ ] Every water body from stocking reports extracted
- [ ] Non-stocked fisheries included (wild rivers, C&R waters)
- [ ] Special regulation waters captured
- [ ] USGS-monitored waters cross-referenced
- [ ] Each water body has type, county, and at least one source note
- [ ] Multi-section waters have separate entries
- [ ] Name variants captured for alias table
- [ ] Total count feels comprehensive for the state (not just 50-100)

## Expected Counts by State Size

| State Size | Expected Water Bodies |
|------------|---------------------|
| Small (RI, DE) | 50-150 |
| Medium (UT, NV) | 200-500 |
| Large (CO, MT) | 400-800 |
| Very Large (CA, AK) | 800+ |

If your count is significantly below these ranges, you probably missed a source.

## Known Pitfalls (update after each state)

- **UT (2026-03-18):** Prompt worked well. 450 waters found. Key learnings:
  - Sonnet found the ArcGIS electrofishing MapServer layer on wrimaps.utah.gov — caught backcountry lakes not in stocking data
  - Hundreds of Uinta backcountry lakes have alphanumeric codes only (A-1, B-3, WR-79) — no common names. Excluded for now, could be a separate pass
  - 100% county coverage achieved — the guidebook and stocking reports both include county
  - 99% species coverage — only 6 waters missing species data (very small/obscure ones)
  - Community ponds (58) are a significant category — all stocked, easy to miss if you only look at "natural" waters
  - Multi-section rivers worked well — Provo, Green, Weber all have separate section entries
  - Flaming Gorge has marina entries for Utah side — matches our access-point design decision
  - The "when in doubt, INCLUDE it" rule worked — better to have 450 and trim than 200 and miss
