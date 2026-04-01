# Utah (UT) — Data Sources

**Researched:** 2026-03-18
**Agent:** Sonnet 4.6
**Reviewed by:** Case (Opus)

---

## HIGH Priority Sources

### Source: Utah DWR Fish Stocking Report
- **Agency:** Utah Division of Wildlife Resources (DWR)
- **URL:** https://dwrapps.utah.gov/fishstocking/Fish
- **Verified:** YES — 2026-03-18
- **Type:** stocking
- **Format:** html_table (sortable, filterable by water/county/species)
- **Update Frequency:** weekly (as stocking events occur)
- **JS Rendered:** yes (sorting/filtering JS, but base table loads without JS)
- **Coverage:** statewide
- **History Depth:** 2002–2026 (25 years)
- **Notes:** Columns: water name, county, species, quantity, average length, date stocked. No login required. THE crown jewel source.
- **Scrape Difficulty:** easy
- **Priority:** high

### Source: Utah DWR Fish Utah Interactive Planner
- **Agency:** Utah DWR
- **URL:** https://dwrapps.utah.gov/fishing/fStart
- **Verified:** YES — 2026-03-18
- **Type:** fishing_guide | map
- **Format:** interactive_map (ArcGIS-based)
- **Update Frequency:** seasonal (DWR forecasts) / continuous (user ratings)
- **JS Rendered:** yes (full SPA)
- **Coverage:** statewide — comprehensive water body list with species, ratings, regulations
- **Notes:** Filter by species, rating, program type (Blue Ribbon, Community Pond). Each location has forecast rating, stocking schedule, regulations, access points. BEST SOURCE FOR COMPREHENSIVE WATER BODY LIST.
- **Scrape Difficulty:** hard (JS SPA, need to find underlying API)
- **Priority:** high

### Source: Utah 2026 Fishing Guidebook (PDF)
- **Agency:** Utah DWR
- **URL:** https://wildlife.utah.gov/guidebooks/fishing_guidebook.pdf
- **Verified:** YES — 2026-03-18 (3.6MB PDF)
- **Type:** regulations
- **Format:** pdf
- **Update Frequency:** annual
- **Coverage:** statewide
- **History Depth:** 2017–2026 (archived by year)
- **Notes:** Official regulations — species limits, season dates, special waters, gear restrictions. Text-layer PDF (machine-readable).
- **Scrape Difficulty:** medium
- **Priority:** high

### Source: Utah DEQ Fish Consumption Advisories
- **Agency:** Utah DEQ
- **URL:** https://deq.utah.gov/water-quality/utah-fish-advisories
- **Verified:** YES — 2026-03-18
- **Type:** conditions
- **Format:** html_table | pdf
- **Update Frequency:** annual
- **Coverage:** statewide (40+ water bodies)
- **Notes:** Contaminants: arsenic, mercury, selenium, PCBs. Consumption limits by population. Interactive map. PDF download available.
- **Scrape Difficulty:** easy
- **Priority:** high

### Source: USGS Stream Gauges — Utah
- **Agency:** USGS
- **URL:** https://api.waterdata.usgs.gov (query by state=UT)
- **Verified:** YES — 2026-03-18
- **Type:** conditions
- **Format:** api (JSON)
- **Update Frequency:** real-time (15-min intervals)
- **Coverage:** statewide — 138 active gauges (38 added June 2024–July 2025)
- **Notes:** Discharge (CFS), gauge height, water temp. Free, no key required for <50 req/hr. New API (old retiring Q1 2027).
- **Scrape Difficulty:** easy (structured API)
- **Priority:** high

### Source: NOAA Weather API — Utah
- **Agency:** NOAA/NWS
- **URL:** https://api.weather.gov/points/{lat},{lon}
- **Verified:** YES — 2026-03-18 (tested at 40.7,-111.9)
- **Type:** conditions
- **Format:** api (JSON)
- **Update Frequency:** real-time (hourly forecasts)
- **Coverage:** statewide (any lat/lon)
- **Notes:** Free, no API key. 7-day forecast. User-Agent header required.
- **Scrape Difficulty:** easy
- **Priority:** high

### Source: Bureau of Reclamation — Flaming Gorge
- **Agency:** U.S. Bureau of Reclamation
- **URL:** https://www.usbr.gov/uc/water/crsp/cs/fgd.html
- **Verified:** YES — 2026-03-18 (updated March 5, 2026)
- **Type:** conditions
- **Format:** html_list + dashboard
- **Update Frequency:** monthly (narrative) / daily (dashboard)
- **Coverage:** Flaming Gorge Reservoir
- **Notes:** Pool elevation, monthly inflow, daily release (CFS). Critical for Flaming Gorge + Green River below dam.
- **Scrape Difficulty:** medium
- **Priority:** high

### Source: CUWCD Reservoir & Stream Data
- **Agency:** Central Utah Water Conservancy District
- **URL:** https://data.cuwcd.gov/
- **Verified:** YES — 2026-03-18
- **Type:** conditions
- **Format:** interactive dashboard (JS-rendered)
- **Coverage:** 11 reservoirs (incl. Jordanelle, Strawberry, Utah Lake), 6 streams (incl. Provo)
- **Notes:** Key data for Strawberry and Jordanelle. Data loaded dynamically via JS.
- **Scrape Difficulty:** hard (need to inspect API calls)
- **Priority:** high

### Source: Utah Division of Water Resources — 47 Reservoir Levels
- **Agency:** Utah DNR
- **URL:** https://water.utah.gov/reservoirlevels/
- **Verified:** YES — 2026-03-18
- **Type:** conditions
- **Format:** ArcGIS dashboard
- **Update Frequency:** daily
- **Coverage:** 47 reservoirs statewide
- **Notes:** ArcGIS REST API likely accessible if layer URLs identified.
- **Scrape Difficulty:** hard (ArcGIS dashboard)
- **Priority:** high

### Source: Utah State Parks — Individual Conditions Pages
- **Agency:** Utah Division of State Parks
- **URLs:**
  - Jordanelle: https://stateparks.utah.gov/parks/jordanelle/current-conditions/
  - Echo: https://stateparks.utah.gov/parks/echo/current-conditions/
  - Starvation: https://stateparks.utah.gov/parks/starvation/current-conditions/
  - Utah Lake: https://stateparks.utah.gov/parks/utah-lake/current-conditions/
  - Scofield: https://stateparks.utah.gov/parks/scofield/current-conditions/
  - (20+ more state parks with fishing)
- **Verified:** YES — 2026-03-18 (all checked, all active and recently updated)
- **Type:** conditions
- **Format:** html_list
- **Update Frequency:** weekly (manually by park staff)
- **Coverage:** per water body (20+ state park lakes)
- **Notes:** Water temp, water level %, ice conditions, algae status. High signal-to-noise. Easy to scrape.
- **Scrape Difficulty:** easy
- **Priority:** high

### Source: Fly Shop Reports (Multiple)
- **Orvis:** https://fishingreports.orvis.com/west/utah — 5 rivers, weekly, easy
- **Trout Bum 2:** https://www.troutbum2.com/utah-fly-fishing-reports/ — Provo/Green/Weber, weekly, easy
- **Western Rivers:** https://westernriversflyfishing.com/fishing-reports/ — N. Utah rivers, weekly, easy
- **Flaming Gorge Resort:** https://flaminggorgeresort.com/river-fishing-report/ — Green River, weekly, easy
- **Beehive Fishing:** https://www.beehivefishing.com/fishing-reports/tag/Utah — Green/Provo/Weber, monthly
- **Fly Fish Food:** https://www.flyfishfood.com/blogs/fly-fishing-reports/ — Green/Weber, monthly
- **All verified active 2026-03-18**
- **Priority:** high (for fly fishing rivers — methods, hatches, flies)

### Source: Utah Fish Reports
- **Agency:** Independent aggregator
- **URL:** https://www.utahfishreports.com/
- **Verified:** YES — 2026-03-18
- **Type:** reports | conditions | stocking
- **Format:** html_list (text + photos, paginated)
- **Update Frequency:** multiple times per week
- **Coverage:** statewide (117+ pages of archived reports)
- **Notes:** Mix of DWR staff, park rangers, marina operators, anglers. Includes ice conditions.
- **Scrape Difficulty:** medium (pagination, inconsistent structure)
- **Priority:** high

---

## MEDIUM Priority Sources

- DWR Regional Forecasts (4 regions via GovDelivery) — seasonal bulletins, static URLs per bulletin
- DWR Fisheries Technical Reports — ~70 PDFs, survey data per water body
- State Parks Fishing Map — hub page for 20+ state park fisheries
- Flaming Gorge Water Database (flaminggorge.water-data.com) — daily reservoir data
- Utah Lake Water Levels (utahlake.gov) — hourly
- Utah DEQ Water Quality Network (WQData LIVE) — 15 sites, real-time, public login available
- NRCS SNOTEL — 100+ stations, snowpack data (predicts spring runoff)
- Snoflo (snoflo.org) — aggregates USGS into unified view
- Sport Fishing Report (sportfishingreport.com) — per-lake pages with stocking tables
- Sportsman's Warehouse Reports — **BLOCKED (403)**

## LOW Priority Sources

- DWR Blue Ribbon Fisheries — static designations
- DWR Record Fish — all-time records by species
- Utah Open Water Data Portal (ArcGIS) — water management data
- USGS Water Quality — periodic sampling
- AA-Fishing — editorial summaries
- Jeremy Allan Fly Fishing — infrequent updates
- Norrik — Flaming Gorge/Strawberry reports (stale)
- FisherMap — 1,083 spots mapped but hard to scrape
- Army Corps — **NO Utah lakes** (confirmed negative)
- Flaming Gorge Country — stale content
- Bear Lake (bearlake.org) — stale content

---

## Key Findings

1. **No Army Corps lakes in Utah.** All managed by Bureau of Reclamation or state.
2. **138 active USGS gauges** — 38 new since mid-2024.
3. **DWR stocking database is the crown jewel** — 25 years, updated weekly.
4. **DWR Fish Utah Planner has the most comprehensive water body list** — but requires JS SPA scraping.
5. **State Parks conditions pages are underrated** — weekly updates, easy scrape, 20+ waters.
6. **Fly shop reports are gold for river intel** — 6+ shops publishing weekly.
7. **Sportsman's Warehouse blocks automated access (403).**
8. **GovDelivery regional bulletins are static** — new URL per bulletin, need to monitor.
