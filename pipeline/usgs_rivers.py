"""
USGS River Bible — Create river section entries from USGS stream gauges.

Each active USGS gauge becomes a river pin in the bible with:
- Ground-truthed coordinates
- Location-specific name ("PROVO RIVER NEAR HEBER, UT")
- Automatic real-time conditions data

Usage:
    python3 -m pipeline.usgs_rivers --state UT              # Dry run
    python3 -m pipeline.usgs_rivers --state UT --apply       # Apply
"""

import re, click, requests
from collections import defaultdict
from pipeline.config import supabase
from pipeline.geo import parse_wkb, haversine_km


def fetch_usgs_gauges(state: str) -> list[dict]:
    """Fetch all active USGS stream gauges for a state."""
    url = f"https://waterservices.usgs.gov/nwis/site/?format=rdb&stateCd={state}&siteType=ST&siteStatus=active&hasDataTypeCd=iv"
    print(f"[USGS] Fetching gauges for {state}...")
    resp = requests.get(url, timeout=30, headers={"User-Agent": "FishOn/1.0"})
    lines = [l for l in resp.text.split('\n') if l and not l.startswith('#')]

    gauges = []
    for line in lines[2:]:
        parts = line.strip().split('\t')
        if len(parts) >= 6:
            try:
                gauges.append({
                    'gauge_id': f"USGS-{parts[1]}",
                    'site_no': parts[1],
                    'name': parts[2],
                    'lat': float(parts[4]),
                    'lon': float(parts[5]),
                })
            except (ValueError, IndexError):
                pass

    print(f"  Active gauges: {len(gauges)}")
    return gauges


def clean_gauge_name(raw_name: str, state: str = 'UT') -> tuple[str, str]:
    """Parse USGS gauge name into (river_name, location_qualifier).

    'PROVO RIVER NEAR HEBER, UT' → ('Provo River', 'near Heber')
    'WEBER R NR OAKLEY, UT' → ('Weber River', 'near Oakley')
    """
    name = raw_name.strip()

    # Remove state suffix (handles any 2-letter state code)
    name = re.sub(rf',?\s*{re.escape(state)}\.?$', '', name, flags=re.IGNORECASE).strip()

    # Find the split point (NEAR, NR, AT, AB, BL, ABOVE, BELOW)
    river_part = name
    location_part = ''
    for pattern in [r'\s+(NEAR|NR)\s+', r'\s+AT\s+', r'\s+(ABOVE|AB)\s+', r'\s+(BELOW|BL)\s+']:
        m = re.search(pattern, name, re.IGNORECASE)
        if m:
            river_part = name[:m.start()].strip()
            qualifier = m.group().strip().lower()
            qualifier = qualifier.replace(' nr ', ' near ').replace('nr', 'near').replace('ab', 'above').replace('bl', 'below')
            location = name[m.end():].strip()
            location_part = f"{qualifier} {location}"
            break

    # Expand abbreviations in river name
    river_part = river_part.replace(' R ', ' River ').replace(' CR ', ' Creek ').replace(' CK ', ' Creek ')
    if river_part.endswith(' R'):
        river_part = river_part[:-2] + ' River'
    if river_part.endswith(' CR') or river_part.endswith(' CK'):
        river_part = river_part[:-3] + ' Creek'
    river_part = river_part.replace(' FK ', ' Fork ')
    if river_part.endswith(' FK'):
        river_part = river_part[:-3] + ' Fork'
    river_part = river_part.replace(' N ', ' North ').replace(' S ', ' South ').replace(' E ', ' East ').replace(' W ', ' West ')
    river_part = river_part.replace(' MF ', ' Middle Fork ').replace(' SF ', ' South Fork ').replace(' NF ', ' North Fork ')
    river_part = river_part.replace(' LF ', ' Left Fork ').replace(' RF ', ' Right Fork ')

    # Title case
    river_name = river_part.title()
    location_part = location_part.title() if location_part else ''

    return river_name, location_part


def determine_type(name: str) -> str:
    """Determine if this is a river or creek based on name."""
    n = name.lower()
    if 'river' in n:
        return 'river'
    if 'creek' in n or 'brook' in n or 'run' in n:
        return 'creek'
    if 'canal' in n or 'ditch' in n:
        return 'canal'
    if 'wash' in n or 'draw' in n:
        return 'stream'
    return 'creek'  # default for streams


@click.command()
@click.option('--state', required=True, help='2-letter state code')
@click.option('--apply', 'do_apply', is_flag=True, default=False, help='Apply changes (default: dry run)')
def build_rivers(state: str, do_apply: bool):
    state = state.upper()
    mode = "APPLY" if do_apply else "DRY RUN"
    print("=" * 60)
    print(f"USGS RIVER BIBLE — {state} ({mode})")
    print("=" * 60)

    gauges = fetch_usgs_gauges(state)

    # Load existing bible rivers
    existing = supabase.table("water_bodies").select(
        "id,name,type,coordinates,coord_source"
    ).eq("state", state).in_("type", ["river", "creek", "stream"]).neq("status", "merged").execute()

    existing_by_name = {}
    for w in existing.data:
        existing_by_name[w['name'].lower().strip()] = w

    # Load existing USGS gauge links
    existing_gauges = supabase.table("data_source_links").select(
        "external_id"
    ).eq("source_type", "usgs_gauge").execute()
    existing_gauge_ids = set(d['external_id'] for d in existing_gauges.data)

    # Load aliases
    alias_wb = supabase.table("water_body_aliases").select("alias,water_body_id").execute()
    alias_to_wb = {a['alias'].lower().strip(): a['water_body_id'] for a in alias_wb.data}

    # Process each gauge
    new_entries = []      # Gauges that need new bible entries
    match_existing = []   # Gauges that match existing entries (just wire)
    already_wired = []    # Gauges already in data_source_links

    for g in gauges:
        if g['gauge_id'] in existing_gauge_ids:
            already_wired.append(g)
            continue

        river_name, location = clean_gauge_name(g['name'], state)
        display_name = f"{river_name} — {location}" if location else river_name
        wtype = determine_type(river_name)

        # Check if this river already exists in bible
        matched_id = None

        # Try exact match on display name or river name
        for try_name in [display_name.lower(), river_name.lower()]:
            if try_name in existing_by_name:
                matched_id = existing_by_name[try_name]['id']
                break
            if try_name in alias_to_wb:
                matched_id = alias_to_wb[try_name]
                break

        # Try partial match — river base name against existing entries
        if not matched_id:
            river_base = river_name.lower()
            for ename, entry in existing_by_name.items():
                if river_base in ename or ename.startswith(river_base.split()[0] if river_base else ''):
                    # Check proximity
                    coords = parse_wkb(entry.get('coordinates'))
                    if coords:
                        d = haversine_km(g['lat'], g['lon'], coords[0], coords[1])
                        if d < 25:
                            matched_id = entry['id']
                            break

        if matched_id:
            match_existing.append((g, matched_id, display_name))
        else:
            new_entries.append((g, display_name, river_name, wtype))

    print(f"\n  Already wired: {len(already_wired)}")
    print(f"  Match existing bible entry: {len(match_existing)} (will wire gauge)")
    print(f"  New entries needed: {len(new_entries)} (will create)")

    # Report
    print(f"\n{'=' * 60}")
    print(f"RIVER REPORT — {state}")
    print(f"{'=' * 60}")

    if new_entries:
        print(f"\n## New River Entries ({len(new_entries)})")
        for g, display, river, wtype in new_entries[:30]:
            print(f"  {display:55s} {wtype:8s} ({g['lat']:.4f}, {g['lon']:.4f})")
        if len(new_entries) > 30:
            print(f"  ... and {len(new_entries) - 30} more")

    if match_existing:
        print(f"\n## Wire Gauge to Existing Entry ({len(match_existing)})")
        for g, wb_id, display in match_existing[:15]:
            print(f"  {g['gauge_id']:15s} → {display[:50]}")

    if not do_apply:
        print(f"\n--- DRY RUN complete. Run with --apply to make changes. ---")
        return

    # Apply
    print(f"\n{'=' * 60}")
    print(f"APPLYING...")
    print(f"{'=' * 60}")

    # Create new river entries
    created = 0
    for g, display_name, river_name, wtype in new_entries:
        try:
            result = supabase.table("water_bodies").insert({
                "name": display_name,
                "state": state,
                "type": wtype,
                "coordinates": f"POINT({g['lon']} {g['lat']})",
                "coord_source": "usgs",
                "has_flow_data": True,
                "has_level_data": False,
                "has_stocking": False,
                "status": "active",
            }).execute()

            if result.data:
                wb_id = result.data[0]["id"]

                # Add aliases
                seen = set()
                for alias in [display_name, river_name, g['name']]:
                    alias_lower = alias.lower().strip()
                    if alias_lower not in seen:
                        seen.add(alias_lower)
                        try:
                            supabase.table("water_body_aliases").insert({
                                "water_body_id": wb_id,
                                "alias": alias,
                                "source": "usgs",
                                "is_primary": (alias == display_name),
                            }).execute()
                        except:
                            pass

                # Wire USGS gauge
                try:
                    supabase.table("data_source_links").insert({
                        "water_body_id": wb_id,
                        "source_type": "usgs_gauge",
                        "external_id": g['gauge_id'],
                        "refresh_frequency_hours": 1,
                        "health_status": "healthy",
                    }).execute()
                except:
                    pass

                # Wire NOAA
                try:
                    supabase.table("data_source_links").insert({
                        "water_body_id": wb_id,
                        "source_type": "noaa_station",
                        "external_id": f"{g['lat']:.4f},{g['lon']:.4f}",
                        "refresh_frequency_hours": 6,
                        "health_status": "healthy",
                    }).execute()
                except:
                    pass

                created += 1
        except Exception as e:
            if 'duplicate' not in str(e).lower():
                print(f"  Error creating {display_name}: {e}")

    print(f"  Created: {created}")

    # Wire gauges to existing entries
    wired = 0
    for g, wb_id, display in match_existing:
        try:
            supabase.table("data_source_links").insert({
                "water_body_id": wb_id,
                "source_type": "usgs_gauge",
                "external_id": g['gauge_id'],
                "refresh_frequency_hours": 1,
                "health_status": "healthy",
            }).execute()
            wired += 1
        except:
            pass

    print(f"  Wired to existing: {wired}")

    # Final count
    total = supabase.table("water_bodies").select("id", count="exact").eq("state", state).in_("type", ["river", "creek", "stream"]).neq("status", "merged").execute()
    print(f"\n  Total river/creek entries: {total.count}")


if __name__ == '__main__':
    build_rivers()
