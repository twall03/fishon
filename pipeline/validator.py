"""Validation middleware — checks every parsed record before storage."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from pipeline.matcher import match_water_body, match_species


@dataclass
class ValidationResult:
    valid: bool = False
    water_body_id: str = None
    species_id: str = None
    confidence: float = 0.0
    match_type: str = None
    issues: list = field(default_factory=list)


def validate_stocking_event(water_body_name: str, species_raw: str,
                            quantity: int, event_date: str,
                            state: str) -> ValidationResult:
    """Validate a parsed stocking event. Returns validation result with IDs."""
    result = ValidationResult()
    confidence = 1.0

    # Date validation
    try:
        d = date.fromisoformat(event_date)
        if d > date.today():
            result.issues.append(f"Future date: {event_date}")
            confidence -= 0.3
        if d < date.today() - timedelta(days=365):
            result.issues.append(f"Date >1 year old: {event_date}")
            confidence -= 0.1
    except (ValueError, TypeError):
        result.issues.append(f"Invalid date: {event_date}")
        result.valid = False
        result.confidence = 0.0
        return result

    # Quantity validation
    if quantity is not None and quantity <= 0:
        result.issues.append(f"Invalid quantity: {quantity}")
        confidence -= 0.1
    if quantity is None:
        confidence -= 0.1

    # Water body matching
    wb_match = match_water_body(water_body_name, state)
    if wb_match.match_type == "unmatched":
        result.issues.append(f"Unmatched water body: {water_body_name}")
        result.valid = False
        result.confidence = 0.0
        result.match_type = "unmatched"
        return result

    result.water_body_id = wb_match.water_body_id
    result.match_type = wb_match.match_type
    if wb_match.match_type == "fuzzy":
        confidence = min(confidence, wb_match.confidence)

    # Species matching
    species_id = match_species(species_raw)
    if species_id:
        result.species_id = species_id
    else:
        result.issues.append(f"Unknown species: {species_raw}")
        confidence -= 0.3

    result.confidence = max(0.0, min(1.0, confidence))
    result.valid = True
    return result
