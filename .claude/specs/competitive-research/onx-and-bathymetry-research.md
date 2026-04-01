# Competitive Research: onX Features + Bathymetry Data Sources

_Research conducted: 2026-03-18_

---

## Part 1: onX Feature Analysis for FishOn

### onX Hunt Features — Evaluated for FishOn

| Feature | What It Does | FishOn Priority | Build Difficulty | Mapping to Our Data |
|---|---|---|---|---|
| **Waypoints** | Mark GPS pins with custom icons and notes | HIGH | EASY | Direct port — mark spots, fish holds, structure |
| **Notes on locations** | Text attached to a saved waypoint | HIGH | EASY | Add fishing notes to any pin |
| **Geotagged Photos** | Attach photos to a location | HIGH | EASY | Photo of catch at GPS location |
| **GPS Track Recording** | Record route/trip as a path | MEDIUM | MEDIUM | Track float trips, kayak runs, hike-in routes |
| **Offline Maps** | Download tiles for no-service use | HIGH | MEDIUM | Critical — Utah canyon country has zero cell service |
| **Custom Markers/Pins** | User-defined icons for waypoints | MEDIUM | EASY | Fish hold, structure, access, launch |
| **Land Ownership Boundaries** | Color-coded public/private land | MEDIUM | HARD | Access to shoreline — who owns the bank? |
| **Weather Overlay** | Hyper-local forecast per terrain | HIGH | MEDIUM | We already have weather; visualize on map |
| **Topo/Terrain Layers** | Elevation contours on the map | HIGH | EASY | Critical for understanding canyon reservoirs |
| **Satellite Imagery** | High-res aerial photos | HIGH | EASY | Monitor water levels, vegetation, shoreline access |
| **Recent/Seasonal Imagery** | Updated photos showing changes | MEDIUM | HARD | Water level fluctuation is huge in Utah reservoirs |
| **3D Map View (TerrainX)** | 3D terrain visualization | LOW | HARD | Nice-to-have; not MVP |
| **Sharing** | Share waypoints/maps with friends | HIGH | MEDIUM | Core social feature for guide clients, fishing buddies |
| **Lists/Folders for Waypoints** | Organize pins into trip folders | MEDIUM | EASY | "Flaming Gorge trip", "Strawberry summer spots" |
| **Distance Measuring Tool** | Measure distance on the map | MEDIUM | EASY | Measure drift distance, troll path length |
| **Route Builder** | Plan a path between waypoints | LOW | MEDIUM | Useful for float planning |
| **In-Dash / CarPlay** | Navigate from your vehicle | MEDIUM | MEDIUM | Nice for drive-to lakes |
| **Acreage Calculation** | Measure an area on the map | LOW | EASY | Could measure a cove or flat |
| **Game Management Units** | Hunting-specific regulatory zones | N/A → adapt | MEDIUM | Fish management units / closures / regulations by zone |

**onX Hunt features that do NOT apply to fishing:**
- Trail Camera Integration — hunting only
- CWD Detection — hunting only
- Draw Odds / Tag Application — hunting only
- Historic Wildfire Layers — indirect relevance only
- Possible Access Indicators — partially applicable (access to water)

---

### onX Fish — What It Actually Offers

onX Fish is in early rollout as of early 2026, available only in 10 Midwest states (MN, WI, MI, ND, SD, IN, OH, IL, IA, MO). Price: $34.99/year.

**Fishing-Specific Features (unique to Fish vs. Hunt):**
- **Lake Finder with Filters** — search by species, trophy potential, keeper potential, high abundance
- **CPUE (Catch Per Unit Effort) data** — compares fishery productivity, historical population data
- **Size Distribution Analysis** — shows size class breakdown per lake
- **Area Insights** — tips from professional anglers per water body
- **Access Points + Boat Ramps** — mapped public launch sites and parking
- **CarPlay** for in-vehicle navigation to fishing spots
- **Moon phase tracking** specific to fishing

**Shared Features (ported from Hunt):**
- Waypoints, offline maps, landownership data
- Weather forecasts, radar, wind, barometric pressure
- Recent satellite imagery (monitoring water levels and vegetation)

**What onX Fish notably LACKS:**
- Bathymetric/depth charts for lakes — not mentioned anywhere
- Stocking reports — not mentioned
- USGS stream conditions / flow data
- Species-specific regulations by water body
- Catch logging / logbook
- Social/community features

**The critical gap onX Fish has vs. what FishOn already has:**
FishOn already has stocking data for 450 Utah water bodies, USGS real-time conditions, and weather. onX Fish's CPUE and fishery intelligence layer is the thing we lack — but their lake-level biological data appears to come from state agency survey data (the same kind Utah DWR publishes in its fisheries technical reports).

---

### FishOn MVP Feature Priority Matrix

Based on onX's approach adapted for fishing + our existing data advantages:

**HIGH priority for MVP:**
1. Interactive map of Utah's 450 water bodies with our existing data surfaced on-tap
2. Waypoints (mark spots, name them, attach notes + photos)
3. Offline map tiles for Utah
4. Topo + satellite basemap toggle
5. Weather overlay (we already have the data)
6. Stocking layer (we already have the data — show as map pins)
7. USGS conditions layer for streams/rivers (we already have it)
8. Access points + boat ramps per water body
9. Species filter (show only lakes stocked with cutthroat, etc.)

**MEDIUM priority (post-MVP):**
10. GPS trip tracking
11. Sharing waypoints with friends
12. Land ownership boundaries (hard to build, but onX's killer feature)
13. Recent satellite imagery
14. Waypoint folders/lists
15. CarPlay integration

**LOW priority / future:**
16. CPUE / fishery intelligence layer (needs state agency data partnership)
17. 3D terrain view
18. Route builder
19. Catch logbook (Fishbrain territory — viable differentiator though)

---

## Part 2: Bathymetry Data Sources

### What Is Bathymetry

Bathymetric data = underwater depth contours for lakes and reservoirs. In fishing apps, this shows as a depth map with color gradients and contour lines, helping anglers find drop-offs, humps, flats, channels, and other fish-holding structure.

---

### Data Source 1: USGS — What's Actually Available

USGS does publish bathymetric data, but coverage for US inland lakes is extremely thin and inconsistent.

**What USGS has on ScienceBase for Utah specifically:**
- Lake Powell (UT-AZ): Multiple high-resolution datasets exist
  - Multibeam echosounder tracklines from 2017 USGS–Bureau of Reclamation survey
  - 2-meter resolution GeoTIFF elevation models
  - 1-meter topobathymetric DEM for 1947–2018 period
- Great Salt Lake: Several topobathymetric models exist (half-meter resolution, 2002–2016 data; causeway breach models for 2024–2025)
- Colorado River through Cataract Canyon: Elevation models exist

**The hard truth:** USGS has deep coverage for major federal reservoirs (Lake Powell) and research subjects (Great Salt Lake) but essentially nothing for Utah's 448 other fishable water bodies. No Strawberry Reservoir, no Flaming Gorge full bathymetry, no Fish Lake, no Bear Lake beyond research snapshots.

**Data format:** GeoTIFF raster DEMs, point cloud XYZ files, shapefiles. All are raw scientific data, not tiled map services.

**Access:** ScienceBase (sciencebase.gov) — free download, no API needed, but requires data processing to render as map tiles.

---

### Data Source 2: Garmin / Navionics

**Garmin's approach:** They sell two distinct products:
- **LakeVü HD / LakeVü Ultra** — professionally surveyed inland lake charts (primarily Midwest and South, ~17,000 US lakes)
- **Navionics+** — integrated charts including freshwater, with "up to 1-foot contours" for covered lakes
- **QuickDraw Contours Community** — crowdsourced user sonar data; users with Garmin fish finders map their own lakes and the community data is shared back through the Garmin ecosystem

**Developer access:** No public API found. Garmin/Navionics does not appear to have a documented developer licensing program for third-party apps. Their data is sold as chart cards for their own hardware and through the Navionics app.

**How Fishbrain gets depth maps:** Fishbrain Pro explicitly licenses **Garmin HD depth maps** for US and Canada. This is a confirmed commercial data deal — not a public API. Quote from Fishbrain Pro page: "Garmin® provides HD depth contour maps for US and Canada."

**Cost to license from Garmin/Navionics:** Not publicly documented. Would require a direct business inquiry. Likely 5-figure annual licensing fee at minimum.

---

### Data Source 3: C-MAP

C-MAP (owned by Navico, same parent as Lowrance, Simrad, B&G) is a major competitor to Navionics in chart data.

**Developer access:** No public developer portal found. C-MAP's data is proprietary and licensed through their hardware ecosystem (Lowrance, Simrad devices) and the C-MAP app.

**How apps use C-MAP data:** Typically through Navico/C-MAP business licensing — not a self-serve API. Similar commercial arrangement as Navionics/Garmin.

---

### Data Source 4: Crowdsourced Sonar Upload

Several ecosystems allow users to upload sonar logs that build community depth maps:

**Garmin QuickDraw Contours:**
- Users with Garmin fish finders record GPS + sonar depth continuously while on the water
- Data uploads to the QuickDraw Community via Garmin ActiveCaptain app
- Available to all Garmin users as a free layer in compatible apps
- Format: Garmin's proprietary QuickDraw format; not directly accessible outside Garmin ecosystem

**Navionics SonarChart Live:**
- Same concept — users contribute sonar logs, Navionics processes them
- The resulting community charts are available in the Navionics app
- No third-party API access documented

**Lowrance / Insight Genesis:**
- Lowrance had a program called Insight Genesis for crowdsourced sonar; unclear current status post-Navico consolidation

**Deeper Sonar:**
- Deeper makes a castable sonar device (popular for bank fishing / no-boat scenarios)
- The Deeper app creates depth maps from the device's readings
- These are stored per-user in the Deeper app; no public API or data export for third parties confirmed
- Critically relevant for FishOn: many Utah anglers fish from shore or float tubes — Deeper sonar is the primary device used by this segment

**Viability for FishOn:** Building a user sonar upload pipeline is technically viable but requires:
1. Parsing Garmin, Lowrance, or Humminbird sonar log formats (some are documented, some are reverse-engineered)
2. Processing raw XYZ depth+GPS points into rendered contour tiles
3. Community incentive to contribute data (chicken-and-egg problem)

---

### Data Source 5: State Agencies

**Utah DWR:** Publishes fisheries survey data (stocking, population, CPUE) but does not appear to publish bathymetric charts. The Fish Utah tool shows water body locations but no depth data.

**Utah Division of Water Resources:** Manages reservoir storage — has capacity curves and volume data per reservoir but not bathymetric contour maps for public download.

**Utah AGRC (GIS):** No bathymetric layer found in their available water data.

**Other states:** Some state DNR/DWR agencies have published basic bathymetric survey data for their most-fished lakes, often as scanned PDFs rather than GIS data. Minnesota DNR is the gold standard — they have GIS-ready bathymetric data for thousands of lakes. Utah has nothing comparable.

---

### Data Source 6: Academic / Research Datasets

Some Utah lakes have been surveyed for research purposes:
- Bear Lake: Studied extensively for its endemic species and geology; some bathymetric data exists in academic publications
- Utah Lake: Shallow, well-documented; USGS has some survey data
- Lake Powell: Best-covered (federal reservoir, major recreation area)

These require finding individual studies, requesting data, and processing raw formats into usable map tiles.

---

### Bathymetry Data Formats (What You'll Actually Work With)

| Format | Description | Source |
|---|---|---|
| GeoTIFF raster DEM | Gridded elevation values; common for USGS data | USGS ScienceBase |
| XYZ point cloud | Longitude, latitude, depth as comma-separated points | Raw sonar exports, some USGS data |
| Shapefile (SHP) | Vector contour lines at specific depth intervals | Processed bathymetry products |
| MBTiles | Pre-rendered raster tiles for offline maps | What you'd generate from source data |
| Garmin QuickDraw (.qct) | Garmin proprietary format | Garmin ecosystem only |
| S-57 / S-63 | Nautical chart format; used by NOAA and commercial chart vendors | Navionics, C-MAP data |

For a web/mobile app: source data needs to be converted to MBTiles or served as a vector tile source (e.g., Mapbox vector tiles). This requires a processing pipeline: raw DEMs → contour generation (GDAL/QGIS) → tile generation → hosted tile server.

---

### Realistic Paths to Bathymetry for FishOn

**Path A: License Garmin/Navionics (Most Coverage, High Cost)**
- Negotiate a data licensing deal
- Covers ~17,000 US lakes at up to 1-foot contours
- No Utah-specific gaps beyond the data Garmin already has
- Cost: Unknown but likely expensive; requires business relationship
- Timeline: 3–6 months to negotiate and integrate
- Verdict: Right long-term play once there's funding. Not an MVP path.

**Path B: Open USGS Data for Key Utah Waters (Free, Limited Coverage)**
- Lake Powell: Full high-res data available free from ScienceBase
- Great Salt Lake: Well-covered (though not a fishing lake)
- A handful of other waters: Research as needed
- Most Utah fishing lakes: No data exists
- Format work: Process GeoTIFFs through GDAL → contour lines → tile server
- Verdict: Good for showcasing the feature on featured waters (Lake Powell, maybe Strawberry if found). Not viable as a comprehensive solution.

**Path C: Build a User Contribution Pipeline (Free Data, Long Lead Time)**
- Let users upload sonar logs from Garmin, Lowrance, Humminbird devices
- Process into community depth maps (similar to QuickDraw)
- Start with FishOn's own surveying of top 20–30 Utah lakes
- Incentivize: "Contribute depth data, get premium free" or leaderboard
- Verdict: Viable long-term moat. Requires 1–2 years to reach meaningful coverage. Could be done in parallel with licensing.

**Path D: Partner with Deeper Sonar (Niche but Relevant)**
- Deeper sells castable sonar popular with shore/float tube anglers — exactly FishOn's Utah audience
- A partnership could integrate Deeper data into FishOn maps
- Deeper has no documented public API but a B2B conversation is worth having
- Verdict: Worth a conversation. Low effort to explore.

**Path E: Scrape/Source Academic + Agency Data Lake by Lake (Partial, Free)**
- Research each of the top 50 Utah fishing lakes individually
- Pull any existing academic surveys, agency reports, or scanned charts
- Digitize and process into usable contour data
- Verdict: Labor-intensive but could get ~20–30 key lakes covered at low cost. Good for MVP depth map layer on featured waters.

---

### Bottom Line Recommendation for FishOn

**For MVP:** Don't build bathymetry. It is the hardest single feature to do well and every competitor either licenses expensive proprietary data (Fishbrain from Garmin) or has been doing crowdsourcing for years (Navionics). Launching without it is fine — onX Fish launched without it.

**Short term (6–12 months post-launch):**
- Process the free USGS data for Lake Powell and Utah Lake
- Start a user sonar contribution program (backend pipeline, simple upload flow)
- Reach out to Garmin/Navionics about licensing terms so you know the number

**Medium term (12–24 months):**
- If funding allows, license Garmin depth maps for Utah coverage
- Launch depth map layer as a premium feature
- Build community contribution as a free path to contributing data

**Our current data advantages over onX Fish (as of today):**
- 450 Utah water bodies already in database
- Stocking data (onX Fish doesn't have this)
- USGS real-time stream/river conditions
- Weather per location
- Species presence data
- Utah-only focus (depth >> breadth for early users)

These are the things to ship. Bathymetry is a Phase 2+ feature.
