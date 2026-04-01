# Sonnet Prompt: Geocode & Enrich Water Bodies

**Version:** 1
**Purpose:** Add coordinates, elevation, and physical attributes to every water body in the bible
**Deployed by:** Case (Opus)
**Output:** Enriched JSON with coordinates for database import

---

## Prompt

```
You have a list of fishable water bodies for {STATE_NAME} ({STATE_CODE}). Each needs coordinates and physical attributes so it can be placed on a map.

### Water Body List
{PASTE_WATER_BODY_JSON_FROM_PHASE_2}

### For Each Water Body, Find:

1. **Coordinates** (latitude, longitude) — the primary access point or centroid
   - For lakes/reservoirs: center of the water body or main boat ramp
   - For rivers/creeks: a popular access point or the midpoint of the fishable section
   - For marinas: the marina itself
   - Sources: NHDPlus, Google Maps, state fishing maps, agency websites

2. **Elevation** (feet above sea level) — if readily available

3. **Physical attributes** (where known):
   - surface_acres (lakes/reservoirs)
   - max_depth_ft (lakes/reservoirs)
   - avg_flow_cfs (rivers — from USGS if a gauge exists)
   - boat_ramps count
   - access_type: "wade", "float", "boat", "shore", or combination

4. **Verify the water body exists** — confirm it's a real, fishable location
   - If you can't find coordinates for something, flag it rather than guessing

### Output Format

Return the enriched JSON array:

```json
[
  {
    "name": "Strawberry Reservoir",
    "type": "reservoir",
    "county": "Wasatch",
    "state": "{STATE_CODE}",
    "latitude": 40.1706,
    "longitude": -111.1483,
    "elevation_ft": 7602,
    "surface_acres": 17164,
    "max_depth_ft": 108,
    "boat_ramps": 3,
    "access_type": "boat, shore",
    "is_stocked": true,
    "known_species": ["Rainbow Trout", "Cutthroat Trout", "Kokanee Salmon"],
    "special_regulations": "Cutthroat trout: immediate release required",
    "name_variants": ["Strawberry Reservoir", "Strawberry Res", "Strawberry"],
    "geocode_source": "NHDPlus",
    "geocode_confidence": "high",
    "needs_review": false
  }
]
```

### Confidence Levels
- **high**: coordinates from NHDPlus, state agency map, or verified source
- **medium**: coordinates from general geocoding, approximate location
- **low**: estimated coordinates, could not verify precisely
- **unverified**: could not find coordinates — flag for human review

### Critical Rules

1. **Never guess coordinates.** If you can't find them, set geocode_confidence to "unverified" and needs_review to true.
2. **Coordinates must be in {STATE_CODE}.** If your lat/long falls outside the state boundaries, something is wrong.
3. **Use decimal degrees** (e.g., 40.1706, -111.1483), not DMS.
4. **Western hemisphere longitudes are NEGATIVE** (e.g., -111, not 111).
```

---

## Success Criteria

- [ ] Every water body has coordinates or is flagged for review
- [ ] Coordinates are within state boundaries
- [ ] Confidence levels assigned
- [ ] Physical attributes populated where available
- [ ] No guessed coordinates — unknowns are flagged, not fabricated

## Known Pitfalls (update after each state)

- {will be populated as we learn}
