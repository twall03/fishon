# Sonnet Prompt: USGS Gauge Matching

**Version:** 1
**Purpose:** Match USGS stream gauge stations to water bodies in the bible and create data_source_links
**Deployed by:** Case (Opus)
**Output:** Mapping of gauge IDs to water body names for database wiring

---

## Prompt

```
You have two datasets for {STATE_NAME} ({STATE_CODE}):

1. The FishOn water body bible (list of fishable waters with names and types)
2. A list of USGS stream gauge stations in this state

Your job is to match gauge stations to the correct water body in the bible.

### Water Body Bible
{PASTE_WATER_BODY_LIST}

### USGS Gauge Stations
{PASTE_USGS_GAUGE_LIST}

### Matching Rules

1. **Match by name similarity** — "PROVO RIVER NEAR WOODLAND, UT" matches "Provo River" or "Provo River - above Deer Creek"
2. **Match by proximity** — if a gauge is at coordinates near a water body, it's likely a match
3. **One gauge can match one water body** — but one water body can have multiple gauges (e.g., upstream and downstream)
4. **Rivers may have multiple gauges** — match each gauge to the nearest river section in the bible
5. **Lake gauges are rare** but exist for reservoir levels — match to the lake/reservoir

### For Unmatched Gauges
If a gauge exists on a river/stream NOT in the bible:
- Flag it as a potential bible addition
- Include the gauge name, ID, coordinates, and what water body it likely belongs to

### Output Format

```json
{
  "matched": [
    {
      "water_body_name": "Provo River - below Deer Creek Dam",
      "gauge_id": "USGS-10155500",
      "gauge_name": "PROVO RIVER NEAR CHARLESTON, UT",
      "gauge_lat": 40.4953,
      "gauge_lon": -111.4586,
      "confidence": "high",
      "notes": "Primary gauge for this river section"
    }
  ],
  "unmatched_gauges": [
    {
      "gauge_id": "USGS-10172200",
      "gauge_name": "RED BUTTE CREEK AT FT. DOUGLAS, UT",
      "gauge_lat": 40.7728,
      "gauge_lon": -111.8081,
      "suggested_water_body": "Red Butte Creek",
      "suggested_type": "creek",
      "notes": "Not in bible — small urban creek, may be fishable"
    }
  ]
}
```

### Critical Rules

1. **Never force a match.** If you're not sure, put it in unmatched_gauges.
2. **Gauge names use ALL CAPS and abbreviations** — "NR" = "NEAR", "BLW" = "BELOW", "ABV" = "ABOVE", "CR" = "CREEK", "R" = "RIVER"
3. **Gauge coordinates are authoritative** — use them to verify your name-based matches make geographic sense.
```

---

## Success Criteria

- [ ] Every bible river/stream checked against gauge list
- [ ] Matched gauges have confidence ratings
- [ ] Unmatched gauges flagged for potential bible additions
- [ ] No forced/wrong matches — unmatched is better than mismatched

## Known Pitfalls (update after each state)

- {will be populated as we learn}
