# Sonnet Prompt: Source Discovery

**Version:** 1
**Purpose:** Find every public fishing data source for a state
**Deployed by:** Case (Opus)
**Output:** Structured source catalog for `.claude/states/{state_code}/sources.md`

---

## Prompt

```
You are researching public fishing data sources for {STATE_NAME} ({STATE_CODE}).

Your job is to find EVERY publicly accessible data source related to fishing in this state. Be exhaustive. This list will be used to build a fishing data aggregation platform.

Find and document the following:

### 1. State Fish & Wildlife Agency
- What is the agency called? (DWR, DNR, Game & Fish, Fish & Wildlife, etc.)
- Main website URL
- Stocking reports page URL — where do they publish fish stocking data?
  - What format? (HTML table, PDF, CSV, interactive map, database query tool)
  - How often updated?
  - How far back does the history go?
- Fishing regulations page URL
- Any "where to fish" guide or fishing atlas
- Any interactive fishing map
- Any API or structured data feed

### 2. Federal Sources for {STATE_CODE}
- USGS stream gauges: how many active gauges in this state?
  - Query: https://api.waterdata.usgs.gov/v2/monitoring-locations?state={STATE_CODE}&monitoring_location_type=Stream&active=true
- NOAA weather: confirm weather.gov API works for this state's coordinates
- Army Corps of Engineers: any reservoirs/dams in this state?
- EPA water quality data available?

### 3. Regional / Community Sources
- Any regional fishing report websites (fly shops, guides, fishing clubs)
- Any ice fishing condition reports (if applicable to this state)
- Any state-specific fishing forums or report sites

### 4. Verify Every URL
For EACH URL you find:
- Confirm it loads (not 404, not behind a login wall)
- Note the exact format of the data
- Note if JavaScript rendering is required
- Note any rate limiting or access restrictions

### Output Format
Return a structured list in this exact format for each source:

## Source: {name}
- **Agency:** {agency name}
- **URL:** {url}
- **Verified:** YES/NO — {date checked}
- **Type:** stocking | regulations | conditions | reports | fishing_guide | map
- **Format:** html_table | html_list | pdf | csv | api | json | interactive_map
- **Update Frequency:** real-time | daily | weekly | monthly | seasonal | static | unknown
- **JS Rendered:** yes | no
- **Coverage:** statewide | regional ({region}) | single water body
- **History Depth:** {how far back data goes}
- **Notes:** {anything unusual — pagination, login walls, rate limits, etc.}
- **Scrape Difficulty:** easy | medium | hard
- **Priority:** high | medium | low (based on data value for anglers)
```

---

## Success Criteria

- [ ] State agency identified with main URL
- [ ] Stocking report source found (or confirmed it doesn't exist)
- [ ] Regulations source found
- [ ] USGS gauge count for state confirmed
- [ ] Every URL verified as active
- [ ] At least 3 sources documented
- [ ] Priority ranked for scraping order

## Known Pitfalls (update after each state)

- **UT (2026-03-18):** Prompt worked well. Sonnet found 40+ sources, verified URLs, prioritized correctly. Key learnings:
  - Sonnet naturally found State Parks individual conditions pages — good, these are underrated sources
  - Sonnet correctly identified the DWR Fish Utah Planner as a JS SPA and flagged it as hard to scrape
  - Sonnet caught the Sportsman's Warehouse 403 block and noted it
  - Sonnet found regional tourism/guide service sites that have high-quality fishing reports
  - The "verify every URL" instruction worked — Sonnet actually tested them and reported HTTP status
  - Consider adding: "Check for any state fishing app or mobile-specific data source"
  - Consider adding: "Check for any dam/reservoir operator websites (Bureau of Reclamation, state water authorities)"
  - The prompt could be more specific about finding the state's comprehensive water body list vs just finding sources
