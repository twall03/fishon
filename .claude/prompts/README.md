# FishOn Prompt Library

Standardized prompts for the AI data collection ecosystem. These are used by Case (Opus) to deploy Sonnet agents for state onboarding, and refined after every state.

## Structure

```
prompts/
├── README.md                    ← you are here
├── sonnet/
│   ├── 01_source_discovery.md   ← find all data sources for a state
│   ├── 02_water_body_sweep.md   ← comprehensive water body extraction
│   ├── 03_geocode_enrich.md     ← coordinates, type, county for each
│   ├── 04_usgs_matching.md      ← match USGS gauges to water bodies
│   ├── 05_species_intel.md      ← species + how to catch per water body
│   ├── 06_reference_verify.md   ← verify all URLs are live and active
│   └── 07_self_heal.md          ← investigate and fix broken references
├── haiku/
│   ├── stocking_extract.md      ← template for stocking report parsing
│   └── conditions_extract.md    ← template for conditions/reports parsing
└── learnings.md                 ← what worked, what didn't, per state
```

## Rules

1. **Every prompt has a version number.** When you change it, increment.
2. **After each state, update learnings.md** with what worked and what failed.
3. **Prompts output structured JSON.** Always define the exact schema.
4. **State-specific context is injected at runtime** — the prompts are templates with `{STATE}`, `{STATE_NAME}`, etc. placeholders.
5. **Comprehensive > fast.** A sweep that misses 30% of waters wastes more time than a thorough one.
