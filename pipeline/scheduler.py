"""Scheduler — determines which sources are due for scraping."""

from pipeline.config import supabase


def get_due_sources(state: str = None) -> list[dict]:
    """Get active sources that are past their scrape frequency."""
    try:
        query = supabase.rpc("get_due_sources_simple").execute()
        if query.data:
            return query.data
    except Exception:
        pass

    # Fallback: direct query if RPC doesn't exist
    q = supabase.table("source_catalog").select("*").eq("status", "active")
    if state:
        q = q.eq("state", state)
    result = q.execute()

    # Filter to those past due
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    due = []
    for s in result.data:
        if s["last_scraped_at"] is None:
            due.append(s)
        else:
            last = datetime.fromisoformat(s["last_scraped_at"].replace("Z", "+00:00"))
            freq = timedelta(hours=s["scrape_frequency_hours"])
            if now - last >= freq:
                due.append(s)
    return due


def get_source_by_id(source_id: str) -> dict:
    """Get a specific source by ID."""
    result = supabase.table("source_catalog").select("*").eq("id", source_id).single().execute()
    return result.data


def get_stale_weather_bodies(state: str = None, max_age_hours: int = 6) -> list[dict]:
    """Get water bodies with stale or missing weather data."""
    q = supabase.table("data_source_links").select(
        "water_body_id,external_id,last_refreshed_at"
    ).eq("source_type", "noaa_station")

    if state:
        # Join through water_bodies to filter by state
        wbs = supabase.table("water_bodies").select("id").eq("state", state).execute()
        wb_ids = [w["id"] for w in wbs.data]
        if not wb_ids:
            return []
        q = q.in_("water_body_id", wb_ids[:100])  # Batch limit

    result = q.execute()

    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=max_age_hours)

    stale = []
    for link in result.data:
        if link["last_refreshed_at"] is None:
            stale.append(link)
        else:
            last = datetime.fromisoformat(link["last_refreshed_at"].replace("Z", "+00:00"))
            if last < cutoff:
                stale.append(link)

    return stale


def get_usgs_gauges(state: str = None) -> list[dict]:
    """Get all USGS gauge links, optionally filtered by state."""
    q = supabase.table("data_source_links").select(
        "water_body_id,external_id"
    ).eq("source_type", "usgs_gauge")

    result = q.execute()
    return result.data
