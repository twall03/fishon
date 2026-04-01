# Overnight Status Report — Case

**Date:** 2026-03-18 → 2026-03-19
**For:** Taylor

---

## What Got Done

### Utah — COMPLETE ✅
- 450 water bodies in bible (344 primary, 106 children)
- 4,149 stocking events (2024-2026)
- 165 USGS condition readings
- 700+ weather forecasts
- 21 ice reports
- 15 State Parks conditions (temp, level, ice, algae)
- Coordinates fixed with NHDPlus HR federal data
- Pipeline running: `python -m pipeline --state UT`

### App Features — BUILT ✅
- Full-screen Mapbox outdoor terrain map
- Mapbox GL circle layer pins (no more DOM element bugs)
- Pins scale with zoom, glow on hover/select
- Labels appear at zoom 9+
- Search bar with alias matching
- Filter chips: Recently Stocked, Lakes, Rivers, Live Flow
- **Detail bottom sheet:** conditions (with source + timestamp + link), stocking history (with dates + source links), species, weather forecast
- **Hot Bites page:** recent stocking activity feed, tap to fly to water on map
- **Explore page:** browse/search all waters, filter by type/stocked
- **Bottom navigation:** Map | Hot Bites | Explore
- One pin per water body (parent_id filtering hides children)
- Loading screen with FishOn branding

### Pipeline — OPERATIONAL ✅
- Automated scraping pipeline at `pipeline/`
- Haiku extraction with structured outputs + auto-chunking
- USGS + NOAA integrations
- Validation middleware + confidence scoring
- Deduplication + scrape logging
- State Parks conditions scraper (Haiku)
- `python -m pipeline.onboard --state XX --file /tmp/xx_waters.json` for new states

### Coordinate Fix — DONE ✅
- NHDPlus HR federal polygon centroids for all lakes/reservoirs
- NHDPlus HR flowline midpoints for rivers
- USGS gauge coordinates for gauged rivers
- Reusable onboard script uses NHD first, always

### Montana — IMPORTED ✅
- 546 waters researched by Sonnet, 344 imported with NHD coordinates
- 277 NHD geocoded, 67 USGS geocoded
- 234 USGS gauges wired, 344 NOAA wired
- 492 USGS condition readings fetched

### Wyoming — IMPORTED ✅
- 372 waters researched by Sonnet, 298 imported with NHD coordinates
- 214 NHD geocoded, 85 USGS geocoded
- 109 USGS gauges wired, 298 NOAA wired
- 492 USGS condition readings fetched

### Idaho — IMPORTED ✅
- Sonnet agent found **13,962 waters** via IDFG Fishing Planner API + Stocking API + Species Presence + Regulations PDF
- 2,379 stocked waters, 4,102 with survey-confirmed species, 439 anadromous waters
- 122,769 historical stocking records from IDFG going back to the 1960s
- 2,671 imported to Supabase so far with NHD geocoding (from earlier batch — full 13,962 available for re-import)
- All world-class Idaho fisheries present: Henry's Lake, Silver Creek, South Fork Snake, Middle Fork Salmon, Lake Pend Oreille, etc.

### Database Totals (final)
| Metric | Count |
|--------|-------|
| **Water bodies** | **3,766** (UT: 450, MT: 344, WY: 298, ID: 2,671) |
| Aliases | 4,176 |
| Species entries | 2,711 |
| Stocking events | 4,149 |
| USGS conditions | 1,149 |
| Weather forecasts | 735 |
| Data source links | 4,552 |

### What The Agents Found
| State | Waters Researched | Sources Used | Highlights |
|-------|------------------|-------------|-----------|
| **Idaho** | 13,962 | IDFG API, Stocking API, Species Presence, Regs PDF | 122K stocking records, 439 anadromous waters |
| **Montana** | 546 | FWP Regs, 40 Drainage Plans, Mountain Lakes Guide, Blue Ribbon list | All 16 Blue Ribbon streams, 80+ Absaroka-Beartooth alpine lakes |
| **Wyoming** | 372 | WGFD 8 Regional Guides, Blue/Red Ribbon PDF, Yellowstone NP Regs, USGS 650 gauges | Full Yellowstone NP coverage, Wind River Range lakes |

---

## What Still Needs Doing

### Immediate (when agents finish)
1. Import Idaho, Montana, Wyoming water bodies via `pipeline/onboard.py`
2. Run pipeline for each state to populate stocking/conditions/weather
3. Verify coordinates with NHDPlus for each state

### App Features To Build
4. onX-style waypoints (user-saved spots) — needs auth
5. Offline maps (Mapbox supports this, Capacitor integration needed)
6. Bathymetry layers (research still pending — Sonnet agent was investigating Navionics, Humminbird, USGS sources)
7. Better mobile responsive polish
8. Capacitor wrap for iOS/Android
9. Push notifications for stocking alerts

### Data Gaps
10. Regulations parsing from fishing guidebook PDFs
11. Fly shop fishing reports (Haiku scraper per source)
12. Species intel enrichment (popular methods, baits, tips per water body)
13. Full NOAA coverage (only ~100/450 Utah waters have weather so far)

---

## Key Learnings Recorded
- Never use AI-guessed coordinates (use NHDPlus HR) — `memory/feedback_coordinates.md`
- State onboarding playbook updated with mandatory NHD step
- Prompt library learnings updated for Utah
- Full execution recipe documented in `learnings.md`

---

## How To Run Things

```bash
# Start the app
cd web && npm run dev

# Run the pipeline
cd .. && python -m pipeline --state UT

# Import a new state (after Sonnet builds the water body list)
python -m pipeline.onboard --state ID --file /tmp/idaho_waters.json

# Check database status
python -c "from pipeline.config import supabase; [print(f'{t}: {supabase.table(t).select(\"id\", count=\"exact\").execute().count}') for t in ['water_bodies','stocking_events','conditions','weather_forecasts']]"
```

---

*— Case, COO*
