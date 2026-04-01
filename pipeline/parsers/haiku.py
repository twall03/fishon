"""Haiku parser — sends unstructured HTML to Claude Haiku for structured extraction."""

import json
from dataclasses import dataclass
from pipeline.config import anthropic


@dataclass
class StockingEvent:
    water_body_name: str
    species: str
    quantity: int = None
    date: str = None
    county: str = None
    average_length_inches: float = None


STOCKING_TOOL = {
    "name": "extract_stocking_events",
    "description": "Extract all fish stocking events from the page content",
    "input_schema": {
        "type": "object",
        "properties": {
            "stocking_events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "water_body_name": {"type": "string", "description": "Exact water body name from the page"},
                        "species": {"type": "string", "description": "Normalized species name (e.g., Rainbow Trout)"},
                        "quantity": {"type": "integer", "description": "Number of fish stocked"},
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        "county": {"type": "string", "description": "County name"},
                        "average_length_inches": {"type": "number", "description": "Average fish length in inches"}
                    },
                    "required": ["water_body_name", "species", "quantity", "date"]
                }
            }
        },
        "required": ["stocking_events"]
    }
}


def _call_haiku(html_chunk: str, system_prompt: str) -> list[StockingEvent]:
    """Single Haiku API call for one chunk of HTML."""
    response = anthropic.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
        system=system_prompt,
        tools=[STOCKING_TOOL],
        tool_choice={"type": "tool", "name": "extract_stocking_events"},
        messages=[{
            "role": "user",
            "content": f"Extract all fish stocking events from this page:\n\n{html_chunk}"
        }]
    )

    for block in response.content:
        if block.type == "tool_use":
            events_data = block.input.get("stocking_events", [])
            return [
                StockingEvent(
                    water_body_name=e.get("water_body_name", ""),
                    species=e.get("species", ""),
                    quantity=e.get("quantity"),
                    date=e.get("date"),
                    county=e.get("county"),
                    average_length_inches=e.get("average_length_inches")
                )
                for e in events_data
            ]
    return []


def parse_stocking(html: str, system_prompt: str) -> list[StockingEvent]:
    """Send HTML to Haiku with structured outputs. Chunks large pages."""
    chunk_size = 20000  # ~20K chars per chunk — safe for Haiku context
    all_events = []

    if len(html) <= chunk_size:
        return _call_haiku(html, system_prompt)

    # Split by table rows to avoid cutting mid-row
    rows = html.split("</tr>")
    current_chunk = ""

    for row in rows:
        if len(current_chunk) + len(row) > chunk_size and current_chunk:
            events = _call_haiku(current_chunk, system_prompt)
            all_events.extend(events)
            current_chunk = row + "</tr>"
        else:
            current_chunk += row + "</tr>"

    # Process final chunk
    if current_chunk.strip():
        events = _call_haiku(current_chunk, system_prompt)
        all_events.extend(events)

    return all_events
