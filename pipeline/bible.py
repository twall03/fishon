"""Shared bible access utilities — canonical data loading from Supabase."""

from collections import defaultdict
from pipeline.config import supabase
from pipeline.geo import parse_wkb


def load_water_bodies(state: str, fields: str = 'id,name,state,county,type,coordinates,status') -> list[dict]:
    """Load all active water bodies for a state, paginated."""
    all_wb = []
    offset = 0
    while True:
        result = supabase.table("water_bodies").select(fields).eq("state", state).neq("status", "merged").range(offset, offset + 999).execute()
        if not result.data:
            break
        all_wb.extend(result.data)
        if len(result.data) < 1000:
            break
        offset += 1000
    return all_wb


def load_water_bodies_with_coords(state: str) -> list[dict]:
    """Load water bodies with parsed lat/lon coordinates."""
    entries = load_water_bodies(state)
    for w in entries:
        coords = parse_wkb(w.get('coordinates'))
        w['lat'] = coords[0] if coords else None
        w['lon'] = coords[1] if coords else None
    return entries


def load_aliases(state: str = None) -> tuple[dict, dict]:
    """Load aliases. Returns (alias_to_wb_id, wb_id_to_aliases).

    If state is provided, only loads aliases for that state's water bodies.
    """
    alias_to_wb = {}
    wb_to_aliases = defaultdict(list)

    if state:
        wb_ids = [w['id'] for w in load_water_bodies(state, fields='id')]
        batch_size = 100
        for i in range(0, len(wb_ids), batch_size):
            batch = wb_ids[i:i + batch_size]
            result = supabase.table("water_body_aliases").select("alias,water_body_id").in_("water_body_id", batch).execute()
            for a in result.data:
                alias_to_wb[a["alias"].lower().strip()] = a["water_body_id"]
                wb_to_aliases[a["water_body_id"]].append(a["alias"])
    else:
        offset = 0
        while True:
            result = supabase.table("water_body_aliases").select("alias,water_body_id").range(offset, offset + 999).execute()
            if not result.data:
                break
            for a in result.data:
                alias_to_wb[a["alias"].lower().strip()] = a["water_body_id"]
                wb_to_aliases[a["water_body_id"]].append(a["alias"])
            if len(result.data) < 1000:
                break
            offset += 1000

    return alias_to_wb, dict(wb_to_aliases)


def load_species_map() -> dict[str, str]:
    """Load species lookup: {name_lower: species_id}."""
    sp_map = {}
    for s in supabase.table("species").select("id,common_name").execute().data:
        sp_map[s["common_name"].lower()] = s["id"]
    for a in supabase.table("species_aliases").select("alias,species_id").limit(500).execute().data:
        sp_map[a["alias"].lower()] = a["species_id"]
    return sp_map
