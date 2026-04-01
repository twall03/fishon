# Requirements Document

## Introduction

The FishOn automated scraping pipeline — the core data engine. A Python service that fetches data from all source types (DWR stocking pages, USGS API, NOAA API, state parks conditions, fly shop reports), parses unstructured sources using Claude Haiku via the Anthropic API, validates and matches data against the water body bible, deduplicates, stores to Supabase, and logs everything. Runs on a cron schedule with health monitoring and failure alerting.

This is the system that makes FishOn self-running. Haiku does the reps. The pipeline orchestrates.

---

## Requirements

### Requirement 1: Source Catalog Management

**User Story:** As the pipeline, I need to know what sources to scrape, how often, and with what prompt, so that I can run autonomously on a schedule.

#### Acceptance Criteria
1. WHEN the pipeline starts THEN it SHALL read active sources from the `source_catalog` table.
2. WHEN a source is due for scraping (last_scraped_at + scrape_frequency_hours < now) THEN the pipeline SHALL queue it for processing.
3. WHEN a source has status `paused`, `broken`, or `retired` THEN the pipeline SHALL skip it.
4. WHEN a new source is added to the catalog THEN the pipeline SHALL pick it up on the next cycle without restart.

### Requirement 2: Fetch Layer

**User Story:** As the pipeline, I need to fetch raw content from source URLs reliably, handling different formats and failure modes.

#### Acceptance Criteria
1. WHEN fetching an HTML source THEN the system SHALL use HTTP GET with appropriate headers (User-Agent, Accept).
2. WHEN fetching a JS-rendered source THEN the system SHALL use Playwright as a fallback.
3. WHEN a fetch returns HTTP 4xx/5xx THEN the system SHALL log the error and increment `consecutive_failures` on the source.
4. WHEN a fetch times out (>30 seconds) THEN the system SHALL retry once, then log failure.
5. WHEN a fetch succeeds THEN the system SHALL save the raw HTML/content snapshot for audit.

### Requirement 3: Haiku Parse Layer

**User Story:** As the pipeline, I need to send unstructured content to Claude Haiku and get back structured JSON matching our schema.

#### Acceptance Criteria
1. WHEN parsing a stocking report THEN the system SHALL call Claude Haiku 4.5 via the Anthropic API with the source's prompt template.
2. WHEN calling Haiku THEN the system SHALL use structured outputs (tool use with strict: true) to guarantee JSON schema conformance.
3. WHEN Haiku returns results THEN they SHALL conform to the stocking event schema (water_body_name, species, quantity, date, county).
4. WHEN a source has a `prompt_template_id` THEN the system SHALL load the system prompt and schema from the `prompt_templates` table.
5. WHEN batch processing multiple sources THEN the system SHALL use the Anthropic Batch API for cost efficiency (50% discount).
6. WHEN Haiku parsing fails THEN the system SHALL log the error and mark the scrape as failed.

### Requirement 4: USGS Conditions Fetcher

**User Story:** As the pipeline, I need to pull real-time flow/level/temperature data from USGS for all wired gauges.

#### Acceptance Criteria
1. WHEN fetching USGS data THEN the system SHALL query the USGS Water Services API by gauge IDs from `data_source_links`.
2. WHEN USGS returns data THEN the system SHALL insert records into the `conditions` table with flow_cfs, level_ft, temp_f, and timestamp.
3. WHEN fetching USGS data THEN the system SHALL batch requests by state to minimize API calls.
4. WHEN a gauge returns no data THEN the system SHALL log it but not increment failures (gauges can have legitimate gaps).

### Requirement 5: NOAA Weather Fetcher

**User Story:** As the pipeline, I need to pull 7-day weather forecasts for all water bodies.

#### Acceptance Criteria
1. WHEN fetching weather THEN the system SHALL query the NOAA NWS API using coordinates from `data_source_links`.
2. WHEN NOAA returns a forecast THEN the system SHALL upsert into `weather_forecasts` (one row per water_body + forecast_date).
3. WHEN weather data is stale (fetched_at > 6 hours) THEN the system SHALL refresh it.
4. WHEN NOAA rate-limits or errors THEN the system SHALL backoff and retry.

### Requirement 6: Validation Middleware

**User Story:** As the pipeline, I need to validate every parsed record before storing it, catching bad data before it enters the bible.

#### Acceptance Criteria
1. WHEN a stocking event is parsed THEN the system SHALL validate: date is not future, date is not >90 days old, quantity > 0 (if present), species name resolves via `find_species()`.
2. WHEN a water body name is parsed THEN the system SHALL look it up via `find_water_body(alias, state)`. IF not found, try `find_water_body_fuzzy()`.
3. IF a water body name cannot be matched THEN the system SHALL log it in `scrape_logs.unmatched_names` and skip the event (do not insert with wrong water_body_id).
4. WHEN a stocking event passes validation THEN the system SHALL assign a confidence_score based on match quality and data completeness.
5. WHEN confidence_score < 0.7 THEN the system SHALL set `needs_review = true`.

### Requirement 7: Deduplication

**User Story:** As the pipeline, I need to avoid inserting duplicate stocking events when re-scraping the same source.

#### Acceptance Criteria
1. WHEN inserting a stocking event THEN the system SHALL use the dedup unique index (water_body_id, species_id, date, quantity) via ON CONFLICT DO NOTHING.
2. WHEN a duplicate is detected THEN the system SHALL increment `records_duplicated` in the scrape log.
3. WHEN the same source is scraped multiple times THEN only new events SHALL be inserted.

### Requirement 8: Scrape Logging

**User Story:** As the operator, I need full audit trails of every scrape run so I can monitor health and debug issues.

#### Acceptance Criteria
1. WHEN a scrape starts THEN the system SHALL create a `scrape_logs` entry with status `running`.
2. WHEN a scrape completes THEN the system SHALL update the log with: records_extracted, records_stored, records_duplicated, records_unmatched, confidence_avg, status (success/partial/failed).
3. WHEN unmatched water body names are found THEN the system SHALL store them in `scrape_logs.unmatched_names` as JSONB.
4. WHEN a scrape completes THEN the system SHALL update `source_catalog.last_scraped_at` and `data_source_links.last_refreshed_at` for affected water bodies.

### Requirement 9: Health Monitoring & Alerting

**User Story:** As the operator, I need to know when sources break or data quality degrades without checking manually.

#### Acceptance Criteria
1. WHEN a source reaches 3 consecutive failures THEN the system SHALL set `source_catalog.status = 'broken'`.
2. WHEN a source is marked broken THEN the system SHALL send an alert (webhook to Slack/Discord).
3. WHEN `data_source_links.last_refreshed_at` exceeds 2x the refresh_frequency THEN health_status SHALL be set to `stale`.
4. WHEN the pipeline completes a full cycle THEN it SHALL log a summary: sources processed, events stored, failures, duration.

### Requirement 10: Scheduling

**User Story:** As the system, I need to run scraping jobs on a configurable schedule without human intervention.

#### Acceptance Criteria
1. WHEN the pipeline runs THEN it SHALL check all sources and process those due for refresh.
2. WHEN configured as a cron job THEN the pipeline SHALL support running as a single invocation (not a long-running daemon).
3. WHEN the pipeline is invoked THEN it SHALL also run USGS and NOAA fetchers for any stale data.
4. WHEN the pipeline is invoked with a specific source_id THEN it SHALL process only that source (for manual reruns).
