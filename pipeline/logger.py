"""Scrape logging — audit trail for every pipeline run."""

from datetime import datetime, timezone
from pipeline.config import supabase


def start_scrape(source_id: str, prompt_template_id: str = None) -> str:
    """Create a scrape_logs entry. Returns the log ID."""
    result = supabase.table("scrape_logs").insert({
        "source_id": source_id,
        "prompt_template_id": prompt_template_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running"
    }).execute()
    return result.data[0]["id"]


def complete_scrape(log_id: str, records_extracted: int = 0, records_stored: int = 0,
                    records_duplicated: int = 0, records_unmatched: int = 0,
                    confidence_avg: float = None, unmatched_names: list = None,
                    errors: dict = None, status: str = "success"):
    """Update scrape_logs with final results."""
    update = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "records_extracted": records_extracted,
        "records_stored": records_stored,
        "records_duplicated": records_duplicated,
        "records_unmatched": records_unmatched,
        "status": status
    }
    if confidence_avg is not None:
        update["confidence_avg"] = confidence_avg
    if unmatched_names:
        update["unmatched_names"] = unmatched_names
    if errors:
        update["errors"] = errors

    supabase.table("scrape_logs").update(update).eq("id", log_id).execute()


def update_source_health(source_id: str, success: bool):
    """Update source_catalog after a scrape attempt."""
    now = datetime.now(timezone.utc).isoformat()

    if success:
        supabase.table("source_catalog").update({
            "last_scraped_at": now,
            "last_success_at": now,
            "consecutive_failures": 0,
            "status": "active"
        }).eq("id", source_id).execute()
    else:
        # Increment failures
        source = supabase.table("source_catalog").select("consecutive_failures").eq("id", source_id).execute()
        failures = (source.data[0]["consecutive_failures"] or 0) + 1
        update = {
            "last_scraped_at": now,
            "consecutive_failures": failures
        }
        if failures >= 3:
            update["status"] = "broken"
        supabase.table("source_catalog").update(update).eq("id", source_id).execute()
        return failures >= 3  # Returns True if source is now broken
