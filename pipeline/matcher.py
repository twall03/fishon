"""Water body and species matching against the bible."""

from dataclasses import dataclass
from pipeline.config import supabase


@dataclass
class MatchResult:
    water_body_id: str = None
    match_type: str = None  # "exact", "fuzzy", "unmatched"
    confidence: float = 0.0
    matched_name: str = None


def match_water_body(name: str, state: str) -> MatchResult:
    """Look up water body by exact alias match only. No fuzzy matching."""
    result = supabase.rpc("find_water_body", {"p_alias": name, "p_state": state}).execute()

    if result.data:
        return MatchResult(
            water_body_id=result.data,
            match_type="exact",
            confidence=1.0,
            matched_name=name
        )

    return MatchResult(match_type="unmatched", confidence=0.0)


def match_species(name: str) -> str | None:
    """Look up species_id by name or alias. Returns UUID or None."""
    result = supabase.rpc("find_species", {"p_alias": name}).execute()
    return result.data if result.data else None
