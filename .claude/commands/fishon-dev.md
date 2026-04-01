# FishOn Development Process

You are operating on FishOn — an AI-native fishing data platform. Follow this process for ALL development work.

## AI Hierarchy

FishOn is built and maintained by a three-tier AI system:

| Tier | Model | Role |
|------|-------|------|
| **Opus** | Claude Opus 4.6 | The Boss. Orchestrates, reviews, architects, quality control. Oversees the whole ecosystem. |
| **Sonnet** | Claude Sonnet 4.6 | The Researcher. Builds the bible per state, finds/verifies data sources, investigates broken references, self-heals. |
| **Haiku** | Claude Haiku 4.5 | The Worker. Scheduled scraping using Sonnet's verified references. Cheap, fast, structured extraction via Batch API. |

**Opus designs → Sonnet builds and maintains → Haiku runs the daily extraction.**

References are living data. They break, they move, they change format. Sonnet detects and adapts. Haiku keeps running. Opus keeps it honest.

## Project Architecture

FishOn has two parallel development tracks. Every task falls into one of these:

### Track 1: Platform Development
Features, infrastructure, API, frontend, auth, payments — traditional software.
- Use the spec-driven workflow: `/add-feature` → requirements.md → design.md → tasks.md
- Specs live in `.claude/specs/{feature-name}/`
- Execute tasks with `/start-task`

### Track 2: Data Operations
State onboarding, source cataloging, bible building, prompt tuning, accuracy validation.
- Use `/state-onboard {STATE_CODE}` for state-by-state rollout
- State records live in `.claude/states/{state_code}/`
- This track is repeatable — every state follows the same playbook

## Core Principles

### The Bible Is the Source of Truth
Every feature, every query, every notification ties back to `water_body_id`. The water body bible (PostgreSQL + PostGIS) is the foundation. If the bible is wrong, everything downstream is wrong.

### State-Scoped Expansion
The product expands one state at a time. Each state is an independent unit of work with its own:
- Water body bible entries
- Data source catalog
- Scraper prompt templates
- Accuracy metrics
- Certification status

### Data Lineage
For every data point in the app, you must be able to trace it back to:
- The source URL
- The raw HTML/PDF snapshot
- The Haiku prompt version that parsed it
- The validation results
- The confidence score

### Prompt Versioning
Haiku extraction prompts evolve. Every prompt template must be versioned. When a parse goes wrong, you need to know which prompt version produced it. Store prompt templates in the source catalog with version numbers.

### Incremental Bible Building
Start with top 100 waters per state. But when a stocking report mentions a water body NOT in the bible, auto-create a stub entry with `status: unverified`. The scraped data tells you what to add next.

## Decision Logging

Every non-trivial architectural decision gets recorded in `.claude/decisions/`.

Format:
```
# ADR-{number}: {Title}
**Date:** {date}
**Status:** accepted | superseded | deprecated
**Context:** Why this decision came up
**Decision:** What we decided
**Consequences:** What this means going forward
```

Before making a decision that changes the data model, stack, or architecture — check existing ADRs first.

## Quality Standards

### Scraper Accuracy
- A source is not production-ready until parse accuracy is >90% on 3+ test pages
- Test against historical snapshots, not just the current page
- Track accuracy in state onboarding records

### Water Body Match Rate
- Target >95% match rate (scraped water names → bible entries)
- Unmatched names get logged for review and bible expansion
- NEVER guess on a match — unmatched is better than mismatched

### Data Freshness
- Stocking events should appear in the app within 6 hours of publication
- USGS conditions update every 15 minutes (via cache with TTL)
- Weather forecasts update hourly

## Seasonal Awareness

Fishing data is inherently seasonal. Adjust accordingly:
- **Spring/Fall (stocking season):** Scrape stocking sources every 4-6 hours
- **Summer (peak fishing):** Maximum scraping frequency across all sources
- **Winter:** Reduce stocking scrapes to daily, add ice condition sources
- This saves API costs and reduces noise

## When In Doubt

1. Check the PRD (`FishOn_PRD.md`) for product intent
2. Check `construction.md` for architectural analysis
3. Check `.claude/decisions/` for past decisions
4. Check `.claude/states/` for state-specific context
5. Ask the user — don't assume
