# FISHON
## Product Requirements Document

**All Public Fishing Data. One App. Always Live.**

Prepared by Taylor | March 2026 | Version 1.0 | Confidential

---

## Table of Contents

1. Executive Summary
2. Problem Statement
3. Product Vision & Value Proposition
4. Target Users
5. Core Features (MVP)
6. Data Architecture
7. Technical Stack
8. Data Source Inventory
9. AI Scraping Pipeline
10. Construction Plan
11. Maintenance & Self-Healing System
12. Monetization
13. Marketing & Growth Engine
14. Competitive Landscape
15. Milestones & Timeline
16. Risk Assessment
17. Future Roadmap

---

## 1. Executive Summary

FishOn is an AI-native B2C application that aggregates all publicly available fishing data in the United States into a single, live, map-based interface. The product combines fish stocking reports from all 50 state wildlife agencies, real-time river flows and lake levels from USGS, weather conditions from NOAA, ice conditions from community reports, and fishing regulations into one unified experience.

The platform is powered by an AI scraping pipeline that uses LLM-based parsing (Claude Haiku) to extract structured data from hundreds of disparate government sources, eliminating the brittle scraper maintenance problem. The system is designed to be self-healing: when a source changes format, the AI adapts automatically with zero human intervention.

FishOn targets the 50+ million licensed anglers in the United States who currently check multiple state websites, forums, and apps to plan fishing trips. No existing product consolidates this data effectively, especially for western and mountain-state anglers.

| Detail | Value |
|---|---|
| **Target Launch** | Summer 2026 (Utah MVP) |
| **Pricing** | $7.99/month or $59.99/year |
| **MVP Scope** | 5–10 western states: UT, CO, ID, MT, WY, OR, WA, AZ, NM, NV |
| **Operating Cost** | ~$150–300/month (API + hosting) at scale of 200+ sources |

---

## 2. Problem Statement

Fishing data in the United States is extremely fragmented. Every state manages its own fish and wildlife agency with unique websites, publication formats, and update schedules. An angler planning a weekend trip currently needs to:

- Check their state's DWR/DNR website for recent stocking reports
- Visit a separate USGS page for river flow data
- Check weather forecasts across multiple services
- Search forums and social media for ice conditions and recent reports
- Cross-reference fishing regulations for the specific water body
- Repeat all of the above for every water body they're considering

This process takes 30–60 minutes per trip and the information is spread across 5–10 different sources. No existing product solves this comprehensively, particularly for western states where tailwater flows, stocking schedules, and ice-off timing are critical to fishing success.

---

## 3. Product Vision & Value Proposition

FishOn is the "onX for fishing" — a map-first application that shows anglers everything they need to know about any water body in one tap. The core value proposition is radical simplification: open one app, see what's fishing well right now.

**Core Promise:** Every public fishing data point in America, live, in one place, on a map.

### Key Differentiators

- **All 50 states:** No other app aggregates stocking data nationwide.
- **Actually live:** USGS data updates every 15 minutes. Stocking reports parsed within hours of publication.
- **AI-powered infrastructure:** Self-healing scrapers that adapt to source changes without developer intervention.
- **Map-first UX:** Tap any water body and see everything — stocking history, flows, conditions, regulations.
- **Western-first focus:** Built for trout anglers, tailwater fishers, and mountain-state fishing where conditions data is most critical.

---

## 4. Target Users

| Persona | Description | Key Need |
|---|---|---|
| **Weekend Warrior** | Fishes 1–2x/week, drives up to 2 hours for a good spot | Know where fish were just stocked and current conditions before driving |
| **Traveling Angler** | Plans multi-state fishing trips, unfamiliar with local conditions | One app that works across all states with consistent data |
| **Ice Fisher** | Needs ice thickness and conditions before heading out | Reliable, recent ice condition reports with safety data |
| **Fly Fisher** | Obsessed with river flows, hatches, and tailwater releases | Live CFS data with historical context and trend alerts |
| **Guide / Outfitter** | Professional who needs reliable conditions data for clients | Comprehensive, trustworthy data to plan client trips |

---

## 5. Core Features (MVP)

### 5.1 Interactive Map Layer

- Mapbox-powered base map with terrain, satellite, and topo views
- All fishable water bodies displayed as interactive polygons/lines
- Color-coded pins indicating recently stocked waters (green = stocked this week, yellow = this month, gray = older)
- Tap any water body to open a detail card
- Search and filter by species, water type, proximity, and stocking recency

### 5.2 Water Body Detail Card

Tapping a water body opens a bottom sheet showing:

- **Stocking history:** species, quantity, date, source agency
- **Current conditions:** water level, flow rate (CFS), water temperature
- **Weather:** current + 5-day forecast for that location
- **Regulations:** season dates, limits, gear restrictions, special rules
- **Access points:** boat ramps, parking, trailheads (Phase 2)
- **Community reports:** ice conditions, recent catches (Phase 2)

### 5.3 Push Notification Alerts

- "Strawberry Reservoir was just stocked with 10,000 rainbow trout"
- Users set favorite water bodies and species preferences
- Alerts on stocking events, flow changes, and ice condition updates

### 5.4 Stocking Report Feed

- Chronological feed of all stocking events across subscribed states
- Filterable by state, species, water type, and date range
- Links to map location for each event

---

## 6. Data Architecture

### 6.1 Unified Data Schema

All data from all sources is normalized into a common schema centered on the water body as the primary entity.

| Entity | Key Fields | Source |
|---|---|---|
| **Water Body** | name, state, type, coordinates, geometry | USGS, NHD, state agencies |
| **Stocking Event** | water_body_id, species, quantity, date, agency | 50 state DWR/DNR websites |
| **Conditions** | water_body_id, flow_cfs, level_ft, temp_f, timestamp | USGS Water Services API |
| **Weather** | water_body_id, temp, wind, precip, forecast | NOAA/NWS API |
| **Regulation** | water_body_id, season, limits, gear, special_rules | State regulation PDFs/pages |
| **Ice Condition** | water_body_id, thickness, quality, reporter, date | Community reports, select agencies |

### 6.2 Database Design

- **Primary DB:** PostgreSQL with PostGIS extension for geospatial queries
- **Cache layer:** Redis for USGS real-time data (15-min TTL)
- **Search:** PostgreSQL full-text search (Elasticsearch if needed at scale)
- **Storage:** S3 for raw HTML snapshots, PDF archives, and scraper logs

---

## 7. Technical Stack

| Component | Technology |
|---|---|
| **Frontend (Mobile)** | React Native (Expo) or Flutter for iOS + Android |
| **Frontend (Web)** | Next.js with Mapbox GL JS |
| **Backend API** | FastAPI (Python) — lightweight, async, fast |
| **Database** | PostgreSQL + PostGIS on Supabase or Railway |
| **Scraping Engine** | Python (requests + BeautifulSoup for fetch, Claude Haiku for parse) |
| **AI Parsing** | Claude Haiku via Anthropic API — HTML/PDF to structured JSON |
| **Job Scheduler** | Celery + Redis or simple cron on Railway/Render |
| **Push Notifications** | Firebase Cloud Messaging (FCM) + APNs |
| **Hosting** | Render, Railway, or Fly.io (start cheap, scale as needed) |
| **Maps** | Mapbox (custom styles, overlays, bathymetry tiles) |
| **Auth & Payments** | Supabase Auth + Stripe / RevenueCat for subscriptions |
| **Monitoring** | Sentry (errors) + custom dashboard for scraper health |

---

## 8. Data Source Inventory

### 8.1 API-Based Sources (Structured, Free)

| Source | Data Provided | Update Freq | Access |
|---|---|---|---|
| **USGS Water Services** | River flows (CFS), lake levels, water temp | Every 15 min | REST API (free) |
| **NOAA/NWS** | Weather forecasts, precipitation, wind | Hourly | REST API (free) |
| **US Army Corps** | Reservoir levels, dam releases | Daily | Data feeds (free) |
| **EPA WQX** | Water quality metrics | Varies | REST API (free) |
| **NHD (USGS)** | Water body geometries, stream network | Static | Download (free) |

### 8.2 Scrape-Based Sources (Unstructured, 200+)

| Source Type | Data Provided | Est. Sources | Format |
|---|---|---|---|
| **State Stocking Reports** | Species, quantity, water body, date | 50+ pages | HTML, PDF, CSV |
| **State Regulations** | Seasons, limits, gear rules, closures | 50+ docs | PDF, HTML |
| **Regional Reports** | Conditions, hatches, fishing reports | 100+ pages | HTML, blog |
| **Ice Conditions** | Ice thickness, safety, access | 20+ sources | HTML, social |

---

## 9. AI Scraping Pipeline

This is the core technical innovation of FishOn. Rather than building and maintaining brittle CSS-selector scrapers for 200+ sources, the platform uses LLM-based parsing that adapts to format changes automatically.

### 9.1 Pipeline Architecture

1. **Fetch:** Python requests library hits the source URL and retrieves raw HTML. For JS-rendered pages (rare for government sites), Playwright is used as a fallback.
2. **Clean:** Strip navigation, footers, scripts, and ads. Extract the main content area. This step is optional — Haiku can ignore irrelevant content, but trimming reduces token cost.
3. **Parse:** Send the cleaned HTML to Claude Haiku with a structured extraction prompt. The prompt defines the exact JSON schema expected (water_body, species, quantity, date, etc.).
4. **Validate:** Run schema validation on the returned JSON. Check for anomalies (e.g., stocking quantity > 100,000, dates in the future, unknown species names). Flag suspicious outputs for review.
5. **Deduplicate:** Compare against existing records to avoid inserting duplicate stocking events. Use composite keys (water_body + species + date) for matching.
6. **Store:** Write validated, deduplicated records to PostgreSQL. Archive the raw HTML snapshot to S3 for debugging and reprocessing.
7. **Notify:** If new stocking events were detected, trigger push notifications to users who have favorited the relevant water bodies.

### 9.2 Haiku Prompt Strategy

Each source category (stocking, regulations, conditions) uses a tailored system prompt that defines the extraction schema and handles common edge cases. The prompt includes:

- Explicit JSON schema with field types and allowed values
- Examples of expected output for similar sources
- Instructions to return an empty array if no relevant data is found (prevents hallucination)
- Species normalization rules (e.g., "rainbow" = "Rainbow Trout", "bows" = "Rainbow Trout")

### 9.3 Cost Projections

| Metric | Conservative | At Scale |
|---|---|---|
| **Sources scraped** | 50 (10 states) | 250+ (50 states) |
| **Scrape frequency** | Every 6 hours | Every 4 hours |
| **Haiku calls/day** | 200 | 1,500 |
| **Avg tokens/call** | ~2,000 input + 500 output | ~2,000 input + 500 output |
| **Est. Haiku cost/day** | ~$0.15 | ~$1.10 |
| **Est. Haiku cost/month** | ~$4.50 | ~$33 |

*Total AI parsing cost at full 50-state scale is approximately $30–40/month. This is trivial relative to even a handful of paying subscribers.*

---

## 10. Construction Plan

### Phase 1: Foundation (Week 1–2)

**Goal:** Working scraping pipeline for Utah with data flowing into a database.

1. **Database setup:** PostgreSQL + PostGIS on Supabase. Define schema for water bodies, stocking events, conditions, and scrape logs.
2. **Utah stocking scraper:** Build the first scraper targeting Utah DWR stocking reports. Fetch HTML, send to Haiku, validate output, store in DB.
3. **USGS integration:** Connect to USGS Water Services API for all Utah stream gauges and lake level stations. Set up 15-min polling with Redis cache.
4. **NOAA integration:** Pull weather forecasts for Utah fishing locations via NOAA API.
5. **Scraper orchestration:** Set up cron-based scheduling for all scrapers. Build logging and alerting for failures.
6. **Source catalog:** Create a configuration table mapping each source URL to its scrape type, frequency, and Haiku prompt template.

### Phase 2: Map & Frontend (Week 3–4)

**Goal:** Beautiful, functional map UI showing Utah data.

1. **Mapbox setup:** Initialize Mapbox GL JS with custom style. Import Utah water body geometries from NHD dataset.
2. **Stocking pins:** Render stocking events as color-coded pins on the map. Green = stocked this week, yellow = this month.
3. **Water body detail card:** Bottom sheet that opens on tap showing stocking history, current conditions, and weather.
4. **Stocking feed:** Chronological list view of all stocking events with filters.
5. **Search:** Search by water body name, species, or region.
6. **Mobile responsive:** Ensure the web app works well on mobile browsers as a pseudo-app while native is in development.

### Phase 3: State Expansion (Week 5–8)

**Goal:** Expand from Utah to 5–10 western states.

1. **State-by-state scraper build:** Add CO, ID, MT, WY, OR, WA, AZ, NM, NV. Each state requires: finding source URLs, crafting Haiku prompts, testing output quality, and adding to the scheduler.
2. **USGS expansion:** Add all stream gauges in new states. USGS API supports bulk queries by state.
3. **Cross-state normalization:** Ensure species names, water body types, and measurement units are consistent across states.
4. **Subscription system:** Implement Stripe / RevenueCat for payment processing. Gate content behind paywall after free tier.
5. **Push notifications:** Firebase Cloud Messaging for stocking alerts. Users select favorite water bodies and species.

### Phase 4: Native App & Growth (Week 9–12)

**Goal:** Launch native mobile apps and begin marketing.

- Build React Native (Expo) app for iOS and Android
- Port all web functionality to native with offline map support
- Submit to App Store and Google Play
- Begin content marketing engine (see Section 13)
- Launch in r/flyfishing, r/fishing, state fishing subreddits
- Reach out to fishing YouTubers / TikTok creators for partnerships

---

## 11. Maintenance & Self-Healing System

This is the critical section. The entire business model depends on the system maintaining itself with minimal human intervention.

### 11.1 Health Monitoring Layer

Every scraper run is logged with the following metadata:

- Source URL, timestamp, HTTP status code, response size
- Haiku parse result: number of records extracted, confidence flags
- Validation result: pass/fail, specific failures
- Comparison to last successful run: record count delta, new vs. updated records

A health dashboard aggregates this data and surfaces anomalies. Alert thresholds trigger notifications to your phone via Slack/Discord webhook.

### 11.2 Self-Healing Pipeline

When a scraper fails or produces anomalous output, the system follows this automated recovery process:

1. **Detection:** Scrape returns HTTP error, zero records, or fails validation checks (record count drops >50% from baseline, unknown field values, schema violations).
2. **Diagnosis:** System automatically fetches the source page and sends it to Claude Sonnet (upgraded from Haiku for complex reasoning) with the prompt: "This page previously contained fish stocking data in [format]. The current page looks different. Identify what changed and extract the data using the updated format."
3. **Adaptation:** If Sonnet successfully extracts data from the new format, the system updates the Haiku prompt template for that source to match the new page structure. Logs the change for human review.
4. **Fallback:** If Sonnet cannot extract data (page removed, login wall added, fundamentally changed), the system marks the source as "needs human review" and sends an alert. Continues serving cached data for that source.
5. **Verification:** After adaptation, the system runs the updated scraper 3x over 24 hours to verify consistency before marking the source as healthy.

### 11.3 Ongoing Operations Cost

| Component | Monthly Cost |
|---|---|
| Claude Haiku (routine scraping) | $30–40 |
| Claude Sonnet (self-healing events) | $5–15 (only when failures occur) |
| USGS / NOAA API calls | Free |
| Hosting (Render/Railway) | $25–50 |
| PostgreSQL (Supabase) | $25 |
| Mapbox | $0–50 (free tier generous) |
| Redis | $10 |
| S3 storage | $5 |
| Firebase (push notifications) | Free tier |
| **TOTAL** | **~$100–200/month** |

*Break-even at approximately 15–25 subscribers. Every subscriber beyond that is nearly pure margin.*

### 11.4 Human Intervention Estimate

- **Weekly:** 15-minute dashboard review. Check scraper health, data quality metrics, subscriber growth.
- **Monthly:** 1–2 hours reviewing self-healing logs, manually fixing any sources that couldn't auto-recover (estimate 1–3 per month).
- **Quarterly:** Add new data sources, expand to new states, implement feature requests.

---

## 12. Monetization

### 12.1 Pricing Model

| Tier | Features | Price |
|---|---|---|
| **Free** | View map, see stocking pins (last 7 days), limited detail cards | $0 |
| **Pro** | Full stocking history, live conditions, push alerts, all states, species filters, favoriting | $7.99/mo or $59.99/yr |
| **Guide (Future)** | Pro + API access, client sharing, branded reports, historical analytics | $19.99/mo |

### 12.2 Revenue Projections

| Milestone | Subscribers | MRR | ARR |
|---|---|---|---|
| Break-even | 25 | $200 | $2,400 |
| 6 months | 200 | $1,600 | $19,200 |
| 12 months | 1,000 | $8,000 | $96,000 |
| 24 months | 5,000 | $40,000 | $480,000 |

---

## 13. Marketing & Growth Engine

The data IS the content. Every new stocking event, every flow change, every ice report is a piece of content that can be automatically distributed across channels.

### 13.1 Automated Content Pipeline

- **Push notifications:** Instant alerts to subscribers when their favorited waters get stocked.
- **Social posts:** Claude generates Instagram/TikTok captions from stocking data. "10,000 rainbows just dropped in Strawberry Reservoir. Water temp: 52°F. Flows: perfect. Go get 'em."
- **Email digest:** Weekly email summarizing stocking events, best conditions, and top water bodies for each subscriber's state.
- **SEO pages:** Auto-generated landing pages for every water body ("Strawberry Reservoir Fishing Conditions") that rank for long-tail search queries.

### 13.2 Community Growth Channels

- Reddit: r/flyfishing (370k), r/fishing (900k+), every state fishing subreddit
- Fishing YouTube/TikTok creators — offer free Pro accounts for shoutouts
- Facebook fishing groups (massive, underserved audience)
- Fishing forums: The Drake, Western Fly Fisher, Trout Underground
- Local fly shops: QR code flyers, partnership referral codes

---

## 14. Competitive Landscape

| Competitor | Strengths | Weaknesses | FishOn Advantage |
|---|---|---|---|
| **onX Fish** | Brand recognition from onX Hunt, good maps | Midwest/bass focused, weak on conditions data, no stocking reports | All 50 states, western focus, live stocking + conditions |
| **Fishbrain** | Large user base, social features, catch logging | Light on conditions/stocking, social-first not data-first | Data-first approach, actual live conditions vs. user anecdotes |
| **Fishidy** | Decent map interface, some bathymetry | Mediocre execution, stale data, limited states | AI-powered freshness, comprehensive coverage |
| **State DWR Sites** | Authoritative source data | One state at a time, ugly UX, no mobile, no alerts | All states unified, beautiful UX, push alerts |

---

## 15. Milestones & Timeline

| Date | Milestone | Success Metric |
|---|---|---|
| **Mar 2026** | Utah MVP: scraping pipeline + map UI | Utah stocking data live, USGS flowing, map functional |
| **Apr 2026** | Expand to 5 western states | CO, ID, MT, WY scrapers running with >90% accuracy |
| **May 2026** | Launch web app + subscription | 50 paying subscribers, <5 scraper failures/week |
| **Jun 2026** | 10-state coverage + push notifications | 200 subscribers, content pipeline automated |
| **Aug 2026** | Native iOS + Android app launch | App Store live, 500 subscribers |
| **Dec 2026** | 25+ states, community features, bathymetry v1 | 1,000+ subscribers, $8k MRR |
| **Jun 2027** | All 50 states, full self-healing, guide tier | 5,000 subscribers, $40k MRR |

---

## 16. Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **State blocks scraping** | Medium | Low — public data, respectful rate limits | Rotate IPs, cache aggressively, contact agency for data partnership |
| **Haiku quality degrades** | Medium | Low — task is formulaic | Validation checks catch bad output; fall back to Sonnet |
| **onX builds this feature** | High | Medium — they have resources | Move fast, build community moat, be the data-first brand before they catch up |
| **Solo founder burnout** | High | Medium — school + job + startup | Automate everything, keep scope tight, AI handles maintenance |
| **Data accuracy issues** | High | Medium — LLM parsing isn't perfect | Community reporting layer validates data, confidence scoring, source links |
| **Seasonal revenue dips** | Low | High — fishing is seasonal | Annual subscriptions, ice fishing retention, off-season planning features |

---

## 17. Future Roadmap

Beyond the core MVP, FishOn can expand into high-value adjacent features:

- **Bathymetry layers:** Depth maps for major lakes and reservoirs. Source from USGS bathymetric surveys, partner with Navionics, or crowdsource via user sonar uploads.
- **Community reports:** User-submitted catch reports, photos, ice conditions. Builds engagement and validates AI-sourced data. Moderated with AI.
- **AI fishing assistant:** "Where should I fish this weekend?" — Claude analyzes stocking data, conditions, weather, and user preferences to recommend the optimal water body.
- **Historical analytics:** Trend charts for any water body: stocking frequency over years, seasonal flow patterns, catch rate correlations. Premium/guide tier feature.
- **Offline maps:** Download state/regional maps for backcountry trips with no cell service. Critical for western anglers.
- **Guide booking marketplace:** Connect anglers with local guides. Revenue via booking commission. Long-term monetization play.
- **Gear recommendations:** AI-powered gear suggestions based on species, conditions, and water body. Affiliate revenue potential.
- **Hatch charts:** Insect hatch calendars by region and water body for fly fishers. High-value niche data.
- **International expansion:** Canada, Europe, New Zealand, South America — same architecture, new sources.

---

*Built different. Built to run itself.*

**FishOn — 2026**
