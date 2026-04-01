"""Storage layer — inserts validated data into Supabase."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pipeline.config import supabase


@dataclass
class StorageResult:
    stored: int = 0
    duplicated: int = 0
    failed: int = 0


def store_stocking_events(events: list[dict], scrape_log_id: str = None) -> StorageResult:
    """Insert validated stocking events. ON CONFLICT = duplicate, skip."""
    result = StorageResult()

    for event in events:
        row = {
            "water_body_id": event["water_body_id"],
            "species_id": event.get("species_id"),
            "species_raw": event["species_raw"],
            "quantity": event.get("quantity"),
            "date": event["date"],
            "source_agency": event.get("source_agency", ""),
            "source_url": event.get("source_url", ""),
            "raw_text": event.get("raw_text"),
            "confidence_score": event.get("confidence", 1.0),
            "needs_review": event.get("confidence", 1.0) < 0.7,
            "scrape_log_id": scrape_log_id
        }

        try:
            resp = supabase.table("stocking_events").insert(row).execute()
            if resp.data:
                result.stored += 1
        except Exception as e:
            err = str(e).lower()
            if "duplicate" in err or "unique" in err or "23505" in err:
                result.duplicated += 1
            else:
                result.failed += 1
                print(f"    Storage error: {e}")

    # Update data_source_links for affected water bodies
    water_body_ids = set(e["water_body_id"] for e in events if e.get("water_body_id"))
    now = datetime.now(timezone.utc).isoformat()
    for wb_id in water_body_ids:
        try:
            supabase.table("data_source_links").update({
                "last_refreshed_at": now,
                "health_status": "healthy"
            }).eq("water_body_id", wb_id).eq("source_type", "state_dwr").execute()
        except Exception:
            pass

    return result


def store_conditions(conditions: list[dict]) -> int:
    """Insert USGS conditions. Returns count stored."""
    if not conditions:
        return 0

    # Need to map gauge_id to water_body_id via data_source_links
    gauge_ids = [c["gauge_id"] for c in conditions]
    links = supabase.table("data_source_links").select(
        "water_body_id,external_id"
    ).eq("source_type", "usgs_gauge").in_("external_id", gauge_ids).execute()

    gauge_to_wb = {l["external_id"]: l["water_body_id"] for l in links.data}

    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for c in conditions:
        wb_id = gauge_to_wb.get(c["gauge_id"])
        if not wb_id:
            continue
        rows.append({
            "water_body_id": wb_id,
            "flow_cfs": c.get("flow_cfs"),
            "level_ft": c.get("level_ft"),
            "temp_f": c.get("temp_f"),
            "timestamp": c.get("timestamp", now),
            "source": "USGS",
            "gauge_id": c["gauge_id"]
        })

    if not rows:
        return 0

    # Batch insert
    stored = 0
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        try:
            supabase.table("conditions").insert(batch).execute()
            stored += len(batch)
        except Exception:
            # Insert one by one on batch failure
            for row in batch:
                try:
                    supabase.table("conditions").insert(row).execute()
                    stored += 1
                except Exception:
                    pass

    # Update data_source_links health
    for gauge_id, wb_id in gauge_to_wb.items():
        try:
            supabase.table("data_source_links").update({
                "last_refreshed_at": now,
                "health_status": "healthy"
            }).eq("water_body_id", wb_id).eq("source_type", "usgs_gauge").execute()
        except Exception:
            pass

    return stored


def upsert_weather(water_body_id: str, forecasts: list[dict]) -> int:
    """Upsert weather forecasts for a water body. Returns count stored."""
    if not forecasts:
        return 0

    now = datetime.now(timezone.utc).isoformat()
    stored = 0

    for f in forecasts:
        row = {
            "water_body_id": water_body_id,
            "forecast_date": f["forecast_date"],
            "temp_high_f": f.get("temp_high_f"),
            "temp_low_f": f.get("temp_low_f"),
            "wind_mph": f.get("wind_mph"),
            "precip_chance": f.get("precip_chance"),
            "summary": f.get("summary"),
            "fetched_at": now
        }
        try:
            supabase.table("weather_forecasts").upsert(
                row, on_conflict="water_body_id,forecast_date"
            ).execute()
            stored += 1
        except Exception:
            pass

    # Update data_source_links health
    try:
        supabase.table("data_source_links").update({
            "last_refreshed_at": now,
            "health_status": "healthy"
        }).eq("water_body_id", water_body_id).eq("source_type", "noaa_station").execute()
    except Exception:
        pass

    return stored
