"""FishOn Pipeline — CLI entry point.

Usage:
    python -m pipeline                  # full cycle (all due sources + USGS + NOAA)
    python -m pipeline --source <id>    # run specific source
    python -m pipeline --usgs           # USGS conditions only
    python -m pipeline --noaa           # NOAA weather only
    python -m pipeline --state UT       # all sources for a state
    python -m pipeline --stocking       # stocking scrapes only
"""

import time
import click
from pipeline.config import supabase
from pipeline import fetcher, logger, alerts, scheduler, storage, validator
from pipeline.parsers import haiku, usgs, noaa


def run_stocking_scrape(source: dict):
    """Run a single stocking source through the full pipeline."""
    print(f"\n{'='*50}")
    print(f"SCRAPING: {source['name']} ({source['state']})")
    print(f"  URL: {source['url']}")

    # Load prompt template
    prompt_template = None
    if source.get("prompt_template_id"):
        pt = supabase.table("prompt_templates").select("*").eq(
            "id", source["prompt_template_id"]
        ).single().execute()
        prompt_template = pt.data

    if not prompt_template:
        # Try to find active template for this state + type
        pt = supabase.table("prompt_templates").select("*").eq(
            "state", source["state"]
        ).eq("source_type", source["source_type"]).eq("is_active", True).execute()
        if pt.data:
            prompt_template = pt.data[0]

    if not prompt_template:
        print("  ERROR: No prompt template found. Skipping.")
        return

    # Start log
    log_id = logger.start_scrape(source["id"], prompt_template["id"])
    start_time = time.time()

    # Fetch
    print("  Fetching...")
    result = fetcher.fetch(source["url"], js_rendered=source.get("js_rendered", False))
    if not result.success:
        print(f"  FETCH FAILED: {result.error or result.status_code}")
        logger.complete_scrape(log_id, status="failed", errors={"fetch": result.error})
        is_broken = logger.update_source_health(source["id"], success=False)
        if is_broken:
            alerts.send_alert(f"Source BROKEN: {source['name']} ({source['state']}) — 3 consecutive failures")
        return
    print(f"  Fetched {result.response_size:,} bytes in {result.elapsed_ms}ms")

    # Parse with Haiku
    print("  Parsing with Haiku...")
    try:
        events = haiku.parse_stocking(result.html, prompt_template["system_prompt"])
    except Exception as e:
        print(f"  HAIKU PARSE FAILED: {e}")
        logger.complete_scrape(log_id, status="failed", errors={"haiku": str(e)})
        logger.update_source_health(source["id"], success=False)
        return
    print(f"  Extracted {len(events)} events")

    # Validate and match
    print("  Validating...")
    validated = []
    unmatched_names = []
    confidence_sum = 0

    for event in events:
        v = validator.validate_stocking_event(
            water_body_name=event.water_body_name,
            species_raw=event.species,
            quantity=event.quantity,
            event_date=event.date,
            state=source["state"]
        )

        if not v.valid:
            if v.match_type == "unmatched":
                unmatched_names.append(event.water_body_name)
            continue

        validated.append({
            "water_body_id": v.water_body_id,
            "species_id": v.species_id,
            "species_raw": event.species,
            "quantity": event.quantity,
            "date": event.date,
            "source_agency": source["name"],
            "source_url": source["url"],
            "raw_text": f"{event.water_body_name} | {event.species} | {event.quantity} | {event.date}",
            "confidence": v.confidence
        })
        confidence_sum += v.confidence

    print(f"  Validated: {len(validated)}, Unmatched: {len(unmatched_names)}")

    # Store
    print("  Storing...")
    store_result = storage.store_stocking_events(validated, scrape_log_id=log_id)
    print(f"  Stored: {store_result.stored}, Duplicated: {store_result.duplicated}")

    # Complete log
    elapsed = time.time() - start_time
    logger.complete_scrape(
        log_id,
        records_extracted=len(events),
        records_stored=store_result.stored,
        records_duplicated=store_result.duplicated,
        records_unmatched=len(unmatched_names),
        confidence_avg=confidence_sum / len(validated) if validated else None,
        unmatched_names=list(set(unmatched_names)) if unmatched_names else None,
        status="success" if store_result.stored > 0 else "partial"
    )
    logger.update_source_health(source["id"], success=True)

    print(f"  Done in {elapsed:.1f}s")
    if unmatched_names:
        unique_unmatched = list(set(unmatched_names))
        print(f"  Unmatched names: {unique_unmatched[:10]}")


def run_usgs(state: str = None):
    """Fetch USGS conditions for all wired gauges."""
    print(f"\n{'='*50}")
    print(f"USGS CONDITIONS{f' ({state})' if state else ''}")

    gauge_links = scheduler.get_usgs_gauges(state)
    gauge_ids = [g["external_id"] for g in gauge_links]
    print(f"  Gauges to query: {len(gauge_ids)}")

    if not gauge_ids:
        print("  No gauges found.")
        return

    conditions = usgs.fetch_conditions(gauge_ids)
    print(f"  Readings received: {len(conditions)}")

    # Convert to dicts for storage
    condition_dicts = [
        {"gauge_id": c.gauge_id, "flow_cfs": c.flow_cfs,
         "level_ft": c.level_ft, "temp_f": c.temp_f,
         "timestamp": c.timestamp}
        for c in conditions
    ]

    stored = storage.store_conditions(condition_dicts)
    print(f"  Stored: {stored}")


def run_noaa(state: str = None, limit: int = 50):
    """Fetch NOAA weather for stale water bodies."""
    print(f"\n{'='*50}")
    print(f"NOAA WEATHER{f' ({state})' if state else ''}")

    stale = scheduler.get_stale_weather_bodies(state)
    print(f"  Stale forecasts: {len(stale)}")

    # Limit to prevent hammering NOAA
    to_fetch = stale[:limit]
    total_stored = 0

    for link in to_fetch:
        coords = link.get("external_id", "")
        if not coords or "," not in coords:
            continue

        lat, lon = coords.split(",")
        try:
            forecasts = noaa.fetch_forecast(float(lat), float(lon))
            if forecasts:
                forecast_dicts = [
                    {"forecast_date": f.forecast_date, "temp_high_f": f.temp_high_f,
                     "temp_low_f": f.temp_low_f, "wind_mph": f.wind_mph,
                     "precip_chance": f.precip_chance, "summary": f.summary}
                    for f in forecasts
                ]
                stored = storage.upsert_weather(link["water_body_id"], forecast_dicts)
                total_stored += stored
        except Exception as e:
            print(f"  Error for {coords}: {e}")

        time.sleep(0.3)  # Rate limit respect

    print(f"  Forecasts stored: {total_stored}")


@click.command()
@click.option("--source", default=None, help="Run specific source by ID")
@click.option("--usgs-only", "usgs_only", is_flag=True, help="USGS conditions only")
@click.option("--noaa-only", "noaa_only", is_flag=True, help="NOAA weather only")
@click.option("--stocking", is_flag=True, help="Stocking scrapes only")
@click.option("--state", default=None, help="Filter by state code (e.g., UT)")
@click.option("--noaa-limit", default=50, help="Max NOAA fetches per run")
def main(source, usgs_only, noaa_only, stocking, state, noaa_limit):
    """FishOn Data Pipeline — fetch, parse, validate, store."""
    print("=" * 50)
    print("FISHON PIPELINE")
    print("=" * 50)

    start = time.time()

    if usgs_only:
        run_usgs(state)
    elif noaa_only:
        run_noaa(state, limit=noaa_limit)
    elif source:
        src = scheduler.get_source_by_id(source)
        if src:
            run_stocking_scrape(src)
        else:
            print(f"Source not found: {source}")
    else:
        # Full cycle
        # 1. Stocking scrapes
        if not noaa_only:
            due_sources = scheduler.get_due_sources(state)
            print(f"\nSources due for scraping: {len(due_sources)}")
            for src in due_sources:
                run_stocking_scrape(src)

        # 2. USGS conditions
        if not stocking:
            run_usgs(state)

        # 3. NOAA weather
        if not stocking:
            run_noaa(state, limit=noaa_limit)

    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"PIPELINE COMPLETE — {elapsed:.1f}s")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
