# FishOn

**All Public Fishing Data. One App. Always Live.**

## What This Is

AI-native B2C app that aggregates all publicly available US fishing data (stocking reports, river flows, lake levels, weather, regulations) into a single map-based interface. Powered by an AI scraping pipeline using Claude Haiku for parsing and a self-healing maintenance system.

## Key Documents

- `FishOn_PRD.md` — Full product requirements document
- `construction.md` — Technical feasibility analysis and construction plan
- `.claude/decisions/` — Architectural decision records (ADRs)
- `.claude/states/` — State-by-state onboarding records

## Stack

- **Frontend:** Next.js + Mapbox GL JS (wrapped with Capacitor for iOS/Android)
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL + PostGIS on Supabase
- **Cache:** Redis (USGS data, 15-min TTL)
- **AI Boss:** Claude Opus 4.6 — orchestrates, reviews, quality control
- **AI Researcher:** Claude Sonnet 4.6 — builds bible, finds/verifies sources, self-heals broken references
- **AI Worker:** Claude Haiku 4.5 — scheduled scraping via Batch API, structured extraction
- **Auth:** Supabase Auth
- **Payments:** Stripe / RevenueCat
- **Push:** Firebase Cloud Messaging
- **Maps:** Mapbox
- **Monitoring:** Sentry + custom scraper health dashboard

## Core Data Model

Single `water_bodies` table is the source of truth (the "bible"). Every feature joins on `water_body_id`. See ADR-001 for rationale.

Key tables: `water_bodies`, `water_body_aliases`, `data_source_links`, `stocking_events`, `conditions`, `weather_forecasts`

## Pipeline

The scraping pipeline is at `pipeline/`. Run with:
```
python -m pipeline                    # full cycle (stocking + USGS + NOAA)
python -m pipeline --state UT         # full cycle for one state
python -m pipeline --usgs-only        # USGS conditions only
python -m pipeline --noaa-only        # NOAA weather only
python -m pipeline --source <uuid>    # specific source
```

## Development Process

Two tracks:
1. **Platform features:** Use `/add-feature` for spec-driven development
2. **Data operations:** Use `/state-onboard {STATE}` for state-by-state rollout
3. **Pipeline ops:** Use `/case` for COO oversight, pipeline commands, health checks

All architectural decisions logged in `.claude/decisions/`.

## Rules

- The water body bible is sacred. Never insert unvalidated data.
- State is the partition key. Every expansion is state-scoped.
- Prompt templates are versioned. Never overwrite without incrementing.
- Scraper accuracy must be >90% before a source goes live.
- Water body match rate must be >95% before a state is certified.
- When in doubt about a water body match, mark it `unverified` — wrong is worse than missing.
- **Every reference (URL/source) must be verified active before entering the system.**
- **References are living data.** They break, move, change format. The system must detect and adapt.
- 3 consecutive Haiku failures → source marked `broken` → Sonnet investigates → finds replacement or flags human.
