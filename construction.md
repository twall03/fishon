# CASTLINE — Construction Analysis

**Deep technical feasibility review | March 2026**

---

## TL;DR

This is buildable. Not "maybe buildable" — actually buildable, by one person, with current tools. The AI scraping pipeline is the right architecture. The cost model holds up. The timeline in the PRD is about 2x too aggressive but the sequence is right. The hardest problem isn't scraping — it's water body matching.

---

## Why This Wasn't Possible 18 Months Ago

Let's be specific about what changed, because this matters for the architecture decisions:

**Structured Outputs (GA February 2026)**
Claude now guarantees JSON schema conformance via `strict: true` tool use and `output_config.format`. This is the single biggest unlock. In 2024, you'd send HTML to an LLM and pray the JSON came back valid. Now you define a Pydantic model, pass its JSON schema, and get guaranteed conformant output. Every time. This alone makes the scraping pipeline production-grade instead of "cool demo."

**Haiku 4.5 ($1/M input, $5/M output)**
Fast, cheap, and legitimately good at structured extraction. For a task like "here's an HTML table of fish stocking data, extract it into this schema" — Haiku doesn't just work, it's overkill. This is a pattern-matching extraction task, not reasoning. Haiku eats this alive.

**Batch API (50% off, stackable with prompt caching)**
Scraping is inherently batch work. You don't need real-time responses — you're running cron jobs. Batch API drops Haiku to $0.50/M input, $2.50/M output. Combined with prompt caching (90% off cached system prompts), the cost for parsing 250+ sources daily is genuinely under $20/month. The PRD's $30-40 estimate is conservative. That's good.

**Claude Code / Agentic Development**
A solo founder with Claude Code operates at the velocity of a 3-4 person team for greenfield builds. The scraping pipeline, API, database schema, frontend — all of this can be built in the same conversation context. This isn't hype, it's the current reality of how this tool works. The bottleneck shifts from "writing code" to "making decisions."

---

## The AI Scraping Pipeline — Deep Dive

### Will Haiku Work for Scraping?

**Short answer: Yes, and it's the right tool.**

**Long answer:** The PRD describes a 7-step pipeline (Fetch → Clean → Parse → Validate → Deduplicate → Store → Notify). This is correct but I'd restructure the parsing layer. Here's why:

Government fish stocking pages fall into roughly 4 categories:

| Type | Example | Haiku Difficulty | % of Sources |
|------|---------|-----------------|--------------|
| HTML tables | Utah DWR (`dwrapps.utah.gov/fishstocking/Fish`) | Trivial | ~40% |
| Structured HTML (lists, divs) | Many state DNR pages | Easy | ~30% |
| PDFs (tabular) | Regulation docs, some stocking reports | Medium | ~20% |
| Unstructured prose/blogs | Regional fishing reports | Hard | ~10% |

For the first three categories, Haiku with structured outputs is not just adequate — it's better than traditional scrapers because it handles format variations without breaking. An HTML table with slightly different column headers? Haiku doesn't care. It reads semantically.

The fourth category (unstructured prose) is where you need Sonnet as a fallback. A fishing report that says "they dumped a bunch of bows in the Provo last Tuesday" needs actual comprehension. Haiku can do it sometimes. Sonnet does it reliably.

### The Real Architecture Should Be Three-Tier

The PRD describes Haiku as the parser with Sonnet as the self-healing fallback. I'd add a middle tier:

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   FETCH     │────▶│   PARSE (Haiku)  │────▶│   VALIDATE      │
│   Layer     │     │   + Structured   │     │   Middle Layer   │
│             │     │     Outputs      │     │                 │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                       │
                                              ┌────────▼────────┐
                                              │   CONFIDENCE    │
                                              │   SCORING       │
                                              │                 │
                                              ├─────┬─────┬─────┤
                                              │HIGH │ MED │ LOW │
                                              │     │     │     │
                                              │Store│Queue│Sonnet│
                                              │     │+Log │Retry │
                                              └─────┴─────┴─────┘
```

**HIGH confidence (>95%):** Schema valid, values within expected ranges, species recognized, water body matched. Auto-store.

**MEDIUM confidence (70-95%):** Schema valid but something's off — unusual quantity, new species name, ambiguous water body match. Store but flag for daily review.

**LOW confidence (<70%):** Schema violations, zero records from a source that usually has data, unrecognized everything. Send to Sonnet for re-parse. If Sonnet also fails, queue for human review.

### The Validation Middle Layer — This Is Critical

The PRD mentions validation but doesn't go deep enough. This layer is what separates "cool project" from "production system." Here's what it needs:

**Schema Validation (Pydantic)**
```
- StockingEvent: water_body_name (str), species (str), quantity (int > 0),
  date (date, not future), source_agency (str), source_url (str)
```
Structured outputs from Claude already guarantee schema conformance, but you still need business logic validation on top.

**Business Rules**
- Quantity sanity: 1 < quantity < 500,000 (some hatchery plants are massive)
- Date sanity: not in the future, not more than 90 days old (for "new" events)
- Species normalization: map the 200+ ways people write "Rainbow Trout" to a canonical species list
- Water body fuzzy matching: this is the hard one (see Doubts section)

**Deduplication**
- Composite key: `(water_body_id, species, date, quantity)` — all four fields must match to be a dupe
- Handle partial dupes: same water + species + date but different quantity = likely an update, not a dupe
- Track source_url to catch re-scraping the same page

**Historical Baseline Comparison**
- If Utah DWR usually yields 5-15 stocking events per scrape and suddenly yields 0 or 200, something changed
- Track rolling averages per source, alert on >2 standard deviation swings

### Cost Projection — Revised and Realistic

Using current pricing with Batch API + prompt caching:

| Phase | Sources | Scrapes/Day | Haiku Cost/Month | Sonnet (healing)/Month | Total AI/Month |
|-------|---------|-------------|------------------|----------------------|----------------|
| MVP (Utah) | 5-8 | 4 | ~$1 | ~$0.50 | ~$1.50 |
| 10 States | 50-80 | 4 | ~$8 | ~$3 | ~$11 |
| 50 States | 250+ | 4-6 | ~$18 | ~$8 | ~$26 |

These are lower than the PRD estimates because:
1. Batch API (50% off) is perfect for cron-scheduled scraping
2. Prompt caching means system prompts (the extraction schema, examples, species list) are cached across calls — 90% off on those tokens
3. Most government pages are small. We're talking 1-3K tokens of content per page, not 10K

The AI cost is genuinely trivial. Even at 50-state scale, it's less than a Netflix subscription.

---

## Honest Doubts

### 1. Water Body Matching Is the Hardest Problem

This is the sleeper problem that will eat more engineering time than anything else.

A stocking report says "Blue Lake." There are 47 Blue Lakes in Colorado alone. Utah DWR says "Strawberry Reservoir" but USGS calls it "Strawberry River at Reservoir" and NHDPlus calls it something slightly different.

**You need a water body reconciliation system:**
- Import NHDPlus HR geometries as the canonical water body list per state
- Build a fuzzy matching layer (Levenshtein distance + state + county + type)
- Use geospatial proximity when available (some reports include county or region)
- Build a manual override table for known mismatches
- Consider having Haiku/Sonnet help with disambiguation ("Given these 3 'Blue Lakes' in Colorado, which one is most likely based on the context of this stocking report from Boulder County?")

This isn't unsolvable, but it's the kind of problem that takes a week of iteration to get right, not an afternoon.

### 2. The Timeline Is ~2x Too Aggressive

The PRD says "Week 1-2: Foundation" covering database setup + Utah scraper + USGS + NOAA + orchestration + source catalog. That's at least 3-4 weeks of work even with AI assistance, because:

- NHDPlus HR data download and import into PostGIS is its own multi-day task (large shapefiles, data cleaning, geometry validation)
- The USGS API is transitioning to new endpoints (legacy retiring Q1 2027) — need to build against the new API which has less community documentation
- Validation middle layer design and testing takes iteration
- Water body matching (see above) is a research problem, not just a coding task

**Realistic timeline:**

| Phase | PRD Estimate | Realistic Estimate | What's Included |
|-------|-------------|-------------------|-----------------|
| Foundation | Weeks 1-2 | Weeks 1-4 | DB, Utah scraper, validation, USGS, NOAA |
| Map & Frontend | Weeks 3-4 | Weeks 5-7 | Mapbox, stocking pins, detail cards, search |
| State Expansion | Weeks 5-8 | Weeks 8-14 | 5-10 states, normalization, payments, alerts |
| Native + Growth | Weeks 9-12 | Skip for now | Ship web as PWA first |

**My strong recommendation:** Skip native apps entirely for MVP. A responsive Next.js app with Mapbox works great on mobile. Ship it as a PWA. Only go native after you have 500+ paying subscribers who are asking for it. React Native adds 4-6 weeks of dev time and app store review delays for marginal UX improvement.

### 3. Regulations Parsing Should Be Phase 2+

The PRD includes regulations in the MVP detail card. Fishing regulations are:
- Long, complex legal documents
- Full of exceptions, special zones, seasonal variations
- Published as multi-hundred-page PDFs
- Different structure in every state

Stocking reports are tables. Regulations are legal text. The parsing difficulty is 10x higher. Haiku can extract from a table reliably. Extracting "the daily bag limit for rainbow trout on the Provo River below Deer Creek Dam from January 1 to the second Saturday in July is 2 fish under 15 inches on flies and lures only" from a 300-page PDF — that's a Sonnet job, and it's a hard one.

**Recommendation:** For MVP, link to the state's regulation page for each water body. Don't try to parse and structure the regulations. Add that in Phase 2 when you have revenue and can invest the time.

### 4. The Self-Healing System Is Phase 2

The self-healing pipeline described in the PRD (detect → diagnose with Sonnet → auto-update Haiku prompt → verify) is elegant but it's a significant engineering effort in itself. Building a system that automatically rewrites its own prompts and validates the changes is not trivial.

**For MVP:** Build good monitoring + alerting. When a scraper breaks, you get a Slack notification, you look at the page, you fix the prompt manually. At 10 sources this takes 20 minutes a week. The self-healing system pays off at 100+ sources — build it when you're scaling, not when you're launching.

### 5. PDF Parsing Needs a Strategy

Several states publish stocking reports as PDFs, not HTML. The pipeline needs a PDF-to-text step before sending to Haiku. Options:

- **PyMuPDF / pdfplumber**: Good for tabular PDFs. Extract tables directly.
- **Claude vision (multimodal)**: Send the PDF page as an image. This actually works well for messy PDFs but costs more tokens.
- **PDF-to-HTML conversion**: Then run through the normal HTML pipeline.

PyMuPDF + Haiku is the pragmatic choice. For truly messy PDFs, fall back to multimodal Sonnet.

### 6. USGS API Migration

The USGS legacy Water Services endpoints are retiring Q1 2027. The new API (`api.waterdata.usgs.gov`) is the one to build against. But the new API has less community documentation and fewer code examples.

Without an API key: 50 requests/IP/hour. That's tight if you're polling hundreds of gauges every 15 minutes.

**You need an API key** (free registration). With a key: 1,000 requests/hour. Still might need to batch requests by state or optimize polling frequency.

---

## Proposed Construction Sequence

### Sprint 1: Data Foundation (Weeks 1-2)

**Goal:** Data flows from Utah DWR into a PostGIS database.

1. PostgreSQL + PostGIS on Supabase — schema for water_bodies, stocking_events, conditions, scrape_logs
2. Import NHDPlus HR water body geometries for Utah
3. Build fetch module (requests + Playwright fallback)
4. Build Haiku parse module with structured outputs
5. Build validation middle layer (Pydantic models, business rules, confidence scoring)
6. First end-to-end scrape: Utah DWR → Haiku → validate → store
7. Water body fuzzy matching system (name + state + type → water_body_id)

**Exit criteria:** Utah stocking events in the database, matched to NHDPlus water bodies, with validation passing.

### Sprint 2: Live Data Sources (Weeks 3-4)

**Goal:** USGS and NOAA data flowing, scraper orchestration running.

1. USGS Water Services integration (new API, not legacy) — stream gauges for Utah
2. NOAA NWS integration — forecasts for Utah water body coordinates
3. Redis cache layer for USGS data (15-min TTL)
4. Cron-based scheduler (start simple — APScheduler or even system cron)
5. Source catalog table: URL, scrape type, frequency, prompt template, health status
6. Scraper health logging: HTTP status, record count, parse confidence, delta from baseline
7. Slack/Discord webhook alerts for failures

**Exit criteria:** All three data sources (stocking, flows, weather) updating automatically on schedule.

### Sprint 3: API + Map Frontend (Weeks 5-7)

**Goal:** Beautiful map showing Utah data in a browser.

1. FastAPI backend: endpoints for water bodies, stocking events, conditions, weather
2. Next.js frontend with Mapbox GL JS
3. Utah water bodies rendered as interactive features on the map
4. Color-coded stocking pins (green/yellow/gray by recency)
5. Bottom sheet detail card: stocking history, current conditions, weather
6. Stocking feed (chronological list with filters)
7. Search by water body name and species
8. Mobile responsive (this IS the mobile app for now)

**Exit criteria:** Deployed web app showing live Utah fishing data. Shareable URL.

### Sprint 4: Multi-State Expansion (Weeks 8-12)

**Goal:** 5-10 western states with data flowing.

1. Research and catalog sources for CO, ID, MT, WY (start with 4)
2. Build prompt templates per source (most will be variations of Utah's)
3. Test parse quality per source — iterate on prompts until >90% accuracy
4. USGS expansion: bulk add stream gauges for new states
5. NHDPlus HR import for new states
6. Cross-state species normalization (canonical species list)
7. Add OR, WA, AZ, NM, NV as bandwidth allows

**Exit criteria:** 5+ states with live stocking + conditions data, >90% parse accuracy.

### Sprint 5: Monetization + Growth (Weeks 13-16)

**Goal:** People are paying for FishOn.

1. Supabase Auth (email + Google/Apple OAuth)
2. Stripe subscription integration (free tier + Pro at $7.99/mo)
3. Paywall gate: free = last 7 days of pins, Pro = full history + alerts + filters
4. Firebase Cloud Messaging for push notifications
5. User favorites: save water bodies, set species preferences
6. Stocking alert notifications when favorites get stocked
7. SEO landing pages per water body (auto-generated from data)

**Exit criteria:** Live subscriptions processing. First paying customer.

---

## What Could Actually Kill This

**Ranked by likelihood × impact:**

1. **Water body matching accuracy** (HIGH) — If 20% of stocking events map to the wrong lake, the product is useless. This needs to be >95% accurate. Budget serious time here.

2. **Scope creep** (HIGH) — The PRD is huge. The temptation to build everything at once will be strong. Ship Utah-only, charge money, then expand. A working product for one state beats a half-built product for ten.

3. **State websites behind Cloudflare/bot protection** (MEDIUM) — Some state sites may block automated requests. Mitigation: respectful rate limiting, rotating user agents, and reaching out to agencies for data partnerships if blocked.

4. **Solo founder bandwidth** (MEDIUM) — School + job + startup. The system can be mostly automated once built, but the building phase is intense. Be realistic about weekly hours available.

5. **onX builds this feature** (LOW-MEDIUM) — They have the brand and the users. But they're focused on bass/warm-water fishing and Midwest markets. Western trout anglers are underserved. Move fast and own that niche.

---

## Things the PRD Gets Right

Credit where it's due — the core architecture decisions are solid:

- **AI parsing over CSS selectors** — Correct. Self-adapting beats brittle.
- **Map-first UX** — Correct. Fishing is inherently spatial.
- **FastAPI + PostGIS** — Correct. Right tools for the job.
- **Starting with Utah** — Correct. Build one state well before expanding.
- **Cost model** — Correct. AI costs are genuinely negligible relative to subscription revenue.
- **Western-first focus** — Correct. onX and Fishbrain are weak here. Smart wedge.

---

## Bottom Line

This is a real product with a real market. The AI scraping architecture is not just feasible — it's the only sane way to aggregate data from 250+ disparate government sources without hiring a team. The validation middle layer is what makes it production-grade. The costs are laughably low relative to even modest subscriber numbers.

The biggest risks are execution speed (timeline needs to be realistic), water body matching accuracy (budget extra time), and scope discipline (ship Utah first, resist the urge to build everything).

Build it.

---

*Analysis prepared for FishOn construction planning. March 2026.*
