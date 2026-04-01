# Design Document

## Overview

A Python CLI service (`pipeline/`) that orchestrates all data collection for FishOn. Runs as a cron job or manual invocation. Fetches from sources, parses with Haiku, validates against the bible, deduplicates, stores to Supabase, and logs everything.

## Architecture

```
pipeline/
├── __init__.py
├── main.py              ← CLI entry point: python -m pipeline
├── config.py            ← env vars, Supabase client, Anthropic client
├── scheduler.py         ← determines which sources are due
├── fetcher.py           ← HTTP fetch layer (requests + Playwright fallback)
├── parsers/
│   ├── __init__.py
│   ├── haiku.py         ← Haiku API calls with structured outputs
│   ├── usgs.py          ← USGS Water Services API
│   └── noaa.py          ← NOAA NWS API
├── validator.py         ← validation middleware + confidence scoring
├── matcher.py           ← water body + species alias matching
├── storage.py           ← Supabase insert/upsert operations
├── logger.py            ← scrape_logs management
└── alerts.py            ← Slack/Discord webhook alerts
```

## Components

### config.py
```python
# Loads from .env
ANTHROPIC_API_KEY
SUPABASE_URL
SUPABASE_SERVICE_KEY
ALERT_WEBHOOK_URL  # Slack/Discord (optional)
```
Uses `supabase-py` for database operations and `anthropic` SDK for Haiku calls.

### main.py — CLI Entry Point
```
python -m pipeline                    # run full cycle (all due sources)
python -m pipeline --source <id>      # run specific source
python -m pipeline --usgs             # run USGS fetch only
python -m pipeline --noaa             # run NOAA fetch only
python -m pipeline --state UT         # run all sources for a state
```

### scheduler.py
Queries `source_catalog` for sources where:
- `status = 'active'`
- `last_scraped_at + scrape_frequency_hours < now()` OR `last_scraped_at IS NULL`

Returns list of sources to process this cycle.

### fetcher.py
```python
def fetch(url: str, js_rendered: bool = False) -> FetchResult:
    """Fetch raw content from URL. Returns HTML string + metadata."""
    # 1. HTTP GET with User-Agent header
    # 2. If js_rendered, use Playwright
    # 3. Timeout: 30s, one retry
    # 4. Return FetchResult(html, status_code, response_size, elapsed_ms)
```

### parsers/haiku.py
```python
def parse_stocking(html: str, prompt_template: PromptTemplate) -> list[StockingEvent]:
    """Send HTML to Haiku with structured outputs. Return parsed events."""
    # 1. Load system prompt from prompt_template
    # 2. Call Anthropic API with tool_use (strict: true) for guaranteed JSON
    # 3. Return list of StockingEvent dataclasses
```

Uses Anthropic Python SDK with tool use:
```python
response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=8192,
    system=prompt_template.system_prompt,
    tools=[{
        "name": "extract_stocking_events",
        "description": "Extract fish stocking events from the page",
        "input_schema": prompt_template.schema_json
    }],
    tool_choice={"type": "tool", "name": "extract_stocking_events"},
    messages=[{"role": "user", "content": f"Extract all stocking events:\n\n{html}"}]
)
```

### parsers/usgs.py
```python
def fetch_conditions(gauge_ids: list[str]) -> list[Condition]:
    """Query USGS API for latest readings on given gauges."""
    # Batch by state, query USGS instantaneous values API
    # Parse JSON response into Condition dataclasses
    # No Haiku needed — structured API
```

### parsers/noaa.py
```python
def fetch_forecast(lat: float, lon: float) -> list[WeatherForecast]:
    """Query NOAA for 7-day forecast at coordinates."""
    # 1. GET /points/{lat},{lon} to get grid endpoint
    # 2. GET grid forecast URL for 7-day forecast
    # 3. Parse into WeatherForecast dataclasses
```

### validator.py
```python
def validate_stocking_event(event: StockingEvent, state: str) -> ValidationResult:
    """Validate a parsed stocking event. Returns (valid, confidence, issues)."""
    # 1. Date check: not future, not >90 days old
    # 2. Quantity check: > 0 if present
    # 3. Species match: find_species(event.species_raw) → species_id
    # 4. Water body match: find_water_body(event.water_body_name, state) → water_body_id
    # 5. If exact match fails, try find_water_body_fuzzy()
    # 6. Compute confidence score based on match quality
    # 7. Return ValidationResult(valid, confidence, water_body_id, species_id, issues)
```

Confidence scoring:
- Exact alias match + known species + valid date + quantity present = 1.0
- Fuzzy match (similarity > 0.8) = 0.8
- Fuzzy match (similarity 0.5-0.8) = 0.6
- Missing quantity = -0.1
- Unknown species = 0.5

### matcher.py
```python
def match_water_body(name: str, state: str) -> MatchResult:
    """Look up water body by name. Exact first, fuzzy fallback."""
    # 1. Call find_water_body(name, state) via Supabase RPC
    # 2. If NULL, call find_water_body_fuzzy(name, state)
    # 3. Return MatchResult(water_body_id, match_type, confidence)

def match_species(name: str) -> str | None:
    """Look up species_id by name/alias."""
    # Call find_species(name) via Supabase RPC
```

### storage.py
```python
def store_stocking_events(events: list[ValidatedEvent], scrape_log_id: str):
    """Insert validated stocking events. Handle dedup via ON CONFLICT."""
    # 1. Batch insert with ON CONFLICT DO NOTHING
    # 2. Count stored vs duplicated
    # 3. Update data_source_links.last_refreshed_at for affected water bodies
    # 4. Return StorageResult(stored, duplicated)

def store_conditions(conditions: list[Condition]):
    """Insert USGS conditions records."""

def upsert_weather(forecasts: list[WeatherForecast]):
    """Upsert NOAA weather forecasts."""
```

### logger.py
```python
def start_scrape(source_id: str, prompt_template_id: str) -> str:
    """Create scrape_logs entry, return log_id."""

def complete_scrape(log_id: str, result: ScrapeResult):
    """Update scrape_logs with final counts and status."""

def update_source_health(source_id: str, success: bool):
    """Update source_catalog: last_scraped_at, consecutive_failures, status."""
```

### alerts.py
```python
def send_alert(message: str):
    """Send webhook to Slack/Discord."""
    # POST to ALERT_WEBHOOK_URL with JSON payload
    # Only if ALERT_WEBHOOK_URL is configured
```

## Data Flow

### Stocking Scrape (one source)
```
1. scheduler picks source from source_catalog
2. logger.start_scrape() → scrape_log_id
3. fetcher.fetch(source.url) → raw HTML
4. haiku.parse_stocking(html, prompt) → [StockingEvent]
5. For each event:
   a. matcher.match_water_body(name, state) → water_body_id
   b. matcher.match_species(species_raw) → species_id
   c. validator.validate(event) → confidence, issues
   d. If valid: storage.store() (dedup via ON CONFLICT)
   e. If unmatched: add to unmatched_names
6. logger.complete_scrape(log_id, results)
7. logger.update_source_health(source_id, success)
8. If failures >= 3: alerts.send_alert()
```

### USGS Fetch (all gauges for a state)
```
1. Query data_source_links WHERE source_type = 'usgs_gauge' AND state
2. Batch gauge_ids
3. usgs.fetch_conditions(gauge_ids) → [Condition]
4. storage.store_conditions(conditions)
5. Update data_source_links.last_refreshed_at per gauge
```

### NOAA Fetch (stale weather)
```
1. Query data_source_links WHERE source_type = 'noaa_station' AND stale
2. For each: noaa.fetch_forecast(lat, lon) → [WeatherForecast]
3. storage.upsert_weather(forecasts)
4. Update data_source_links.last_refreshed_at
```

## Error Handling

| Error | Action |
|-------|--------|
| HTTP 4xx/5xx on fetch | Log, increment consecutive_failures, skip |
| Haiku API error | Log, mark scrape failed, skip |
| Haiku returns empty array | Log as partial (source may have no new data — not necessarily an error) |
| Water body unmatched | Log in unmatched_names, skip event, don't insert |
| Species unmatched | Insert with species_id = NULL, needs_review = true |
| Duplicate event (dedup index) | Silently skip, count as duplicated |
| USGS rate limit | Backoff 5s, retry once |
| NOAA rate limit | Backoff 5s, retry once |
| 3 consecutive failures | Mark source broken, send alert |

## Dependencies

```
anthropic          # Anthropic Python SDK
supabase           # Supabase Python client
requests           # HTTP fetching
python-dotenv      # .env loading
click              # CLI framework
```

Playwright is optional — only needed for JS-rendered sources (not needed for MVP).

## Testing Strategy

1. **Unit tests per module:** fetcher, haiku parser, validator, matcher, storage
2. **Integration test:** full pipeline run against Utah DWR with real data
3. **Validation test:** insert known-bad data, verify rejection
4. **Dedup test:** run pipeline twice on same data, verify no duplicates
5. **Alert test:** simulate 3 failures, verify webhook fires
