# Implementation Plan

- [~] 1. Project setup and dependencies
  - Create `pipeline/` directory with `__init__.py`
  - Create `requirements.txt` with: anthropic, supabase, requests, python-dotenv, click
  - Create `config.py` loading .env (API keys, Supabase URL)
  - Install dependencies
  - _Requirements: 1_

- [ ] 2. Core infrastructure
- [ ] 2.1 Create `config.py` with Supabase + Anthropic clients
  - Load .env via python-dotenv
  - Initialize Supabase client with service role key
  - Initialize Anthropic client
  - _Requirements: 1_

- [ ] 2.2 Create `logger.py` for scrape_logs management
  - `start_scrape(source_id, prompt_template_id) → log_id`
  - `complete_scrape(log_id, result)`
  - `update_source_health(source_id, success)`
  - _Requirements: 8, 9_

- [ ] 2.3 Create `alerts.py` for webhook notifications
  - `send_alert(message)` via Discord/Slack webhook
  - Only fires if ALERT_WEBHOOK_URL is configured
  - _Requirements: 9_

- [ ] 3. Fetch layer
- [ ] 3.1 Create `fetcher.py`
  - `fetch(url, js_rendered=False) → FetchResult`
  - HTTP GET with User-Agent, 30s timeout, one retry
  - Return html, status_code, response_size
  - _Requirements: 2_

- [ ] 4. Matching and validation
- [ ] 4.1 Create `matcher.py`
  - `match_water_body(name, state) → MatchResult` using Supabase RPC find_water_body + find_water_body_fuzzy
  - `match_species(name) → species_id` using Supabase RPC find_species
  - _Requirements: 6_

- [ ] 4.2 Create `validator.py`
  - `validate_stocking_event(event, state) → ValidationResult`
  - Date checks, quantity checks, species/water body matching, confidence scoring
  - _Requirements: 6, 7_

- [ ] 5. Parsers
- [ ] 5.1 Create `parsers/haiku.py`
  - `parse_stocking(html, prompt_template) → list[StockingEvent]`
  - Anthropic SDK with tool_use (strict: true) for structured outputs
  - Handle chunking for large pages
  - _Requirements: 3_

- [ ] 5.2 Create `parsers/usgs.py`
  - `fetch_conditions(gauge_ids) → list[Condition]`
  - USGS Water Services API (legacy, with plan to migrate to new API)
  - Batch by state
  - _Requirements: 4_

- [ ] 5.3 Create `parsers/noaa.py`
  - `fetch_forecast(lat, lon) → list[WeatherForecast]`
  - NOAA NWS API: /points → grid forecast
  - _Requirements: 5_

- [ ] 6. Storage layer
- [ ] 6.1 Create `storage.py`
  - `store_stocking_events(events, scrape_log_id) → StorageResult`
  - ON CONFLICT DO NOTHING for dedup
  - Count stored vs duplicated
  - Update data_source_links.last_refreshed_at
  - `store_conditions(conditions)`
  - `upsert_weather(forecasts)`
  - _Requirements: 7, 8_

- [ ] 7. Scheduler and CLI
- [ ] 7.1 Create `scheduler.py`
  - Query source_catalog for due sources
  - Filter by status = active, past due based on frequency
  - _Requirements: 1, 10_

- [ ] 7.2 Create `main.py` CLI entry point
  - `python -m pipeline` — full cycle
  - `--source <id>` — specific source
  - `--usgs` — USGS only
  - `--noaa` — NOAA only
  - `--state <code>` — all sources for state
  - Orchestrates: scheduler → fetch → parse → validate → store → log
  - _Requirements: 10_

- [ ] 8. Seed Utah sources into database
  - Insert Utah DWR stocking source into `source_catalog`
  - Insert Haiku prompt template into `prompt_templates`
  - Verify pipeline can read source + prompt from DB
  - _Requirements: 1, 3_

- [ ] 9. End-to-end test
  - Run full pipeline against Utah DWR stocking page
  - Verify stocking events land in `stocking_events` table
  - Verify dedup works (run twice, no duplicates)
  - Verify scrape_logs has complete audit trail
  - Run USGS fetch for Utah gauges, verify conditions table
  - Run NOAA fetch for sample water bodies, verify weather_forecasts table
  - _Requirements: 1-10_
