"""
OSM Water Features — Download named water bodies from OpenStreetMap via Overpass API.

This is the source Mapbox uses to render water features on the map.
Names and locations from OSM match what users see.

Usage:
    from pipeline.osm import download_osm_water_features
    features = download_osm_water_features('UT')
"""

import requests, time
from collections import defaultdict
from pipeline.geo import STATE_BBOXES_TUPLE

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _query_overpass(query: str, timeout: int = 120) -> list[dict]:
    """Execute an Overpass API query, return elements."""
    resp = requests.post(OVERPASS_URL, data={'data': query}, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data.get('elements', [])


def _map_type(tags: dict) -> str:
    """Map OSM tags to FishOn water body type."""
    water = tags.get('water', '')
    waterway = tags.get('waterway', '')

    if water == 'lake':
        return 'lake'
    if water == 'reservoir':
        return 'reservoir'
    if water == 'pond':
        return 'pond'
    if waterway == 'river':
        return 'river'
    if waterway in ('stream', 'creek'):
        return 'creek'
    if waterway == 'canal':
        return 'canal'
    if water:
        return 'lake'  # default for natural=water without specific type
    return 'stream'


def download_osm_water_features(state: str) -> list[dict]:
    """Download all named water features for a state from OSM.

    Returns deduplicated list of:
    {
        'osm_id': int,
        'osm_type': 'way' | 'relation',
        'name': str,
        'type': str,  # lake/reservoir/pond/river/creek
        'lat': float,
        'lon': float,
    }
    """
    bbox = STATE_BBOXES_TUPLE.get(state.upper())
    if not bbox:
        raise ValueError(f"No bounding box for state: {state}")

    ymin, xmin, ymax, xmax = bbox
    bbox_str = f"{ymin},{xmin},{ymax},{xmax}"

    print(f"[OSM] Downloading water features for {state}...")

    # Query 1: Standing water (lakes, reservoirs, ponds)
    # Includes natural=water AND landuse=reservoir (some reservoirs tagged differently)
    q_standing = f"""
    [out:json][timeout:90];
    (
      way["natural"="water"]["name"]({bbox_str});
      relation["natural"="water"]["name"]({bbox_str});
      way["landuse"="reservoir"]["name"]({bbox_str});
      relation["landuse"="reservoir"]["name"]({bbox_str});
    );
    out center;
    """

    print("  Querying standing water (lakes/reservoirs/ponds)...")
    standing = _query_overpass(q_standing)
    print(f"  Standing water elements: {len(standing)}")

    time.sleep(2)  # Rate limit courtesy

    # Query 2: Flowing water (rivers, streams)
    q_flowing = f"""
    [out:json][timeout:90];
    (
      way["waterway"~"river|stream|creek"]["name"]({bbox_str});
      relation["waterway"~"river|stream|creek"]["name"]({bbox_str});
    );
    out center;
    """

    print("  Querying flowing water (rivers/streams)...")
    flowing = _query_overpass(q_flowing)
    print(f"  Flowing water elements: {len(flowing)}")

    # Parse all elements
    raw_features = []
    for el in standing + flowing:
        name = el.get('tags', {}).get('name')
        center = el.get('center', {})
        lat = center.get('lat')
        lon = center.get('lon')

        if not name or not lat or not lon:
            continue

        # Skip if outside state bbox (Overpass bbox can include edge cases)
        if not (ymin <= lat <= ymax and xmin <= lon <= xmax):
            continue

        raw_features.append({
            'osm_id': el['id'],
            'osm_type': el['type'],
            'name': name.strip(),
            'type': _map_type(el.get('tags', {})),
            'lat': lat,
            'lon': lon,
        })

    print(f"  Raw features with names: {len(raw_features)}")

    # Deduplicate:
    # - Lakes/reservoirs/ponds: keep the relation over way (relations are more authoritative)
    # - Rivers/streams: group segments by name, take centroid of all centers

    standing_types = {'lake', 'reservoir', 'pond'}
    flowing_types = {'river', 'creek', 'canal', 'stream'}

    # Standing water: keep ALL features (same name in different locations = different water)
    # Only deduplicate by osm_id (exact same feature appearing twice)
    standing_by_id = {}
    for f in raw_features:
        if f['type'] not in standing_types:
            continue
        if f['osm_id'] not in standing_by_id:
            standing_by_id[f['osm_id']] = f

    # Flowing water: group by name, centroid of all segment centers
    flowing_groups = defaultdict(list)
    for f in raw_features:
        if f['type'] not in flowing_types:
            continue
        key = f['name'].lower().strip()
        flowing_groups[key].append(f)

    flowing_by_name = {}
    for key, segments in flowing_groups.items():
        avg_lat = sum(s['lat'] for s in segments) / len(segments)
        avg_lon = sum(s['lon'] for s in segments) / len(segments)
        # Use the relation if one exists, otherwise the first way
        representative = next((s for s in segments if s['osm_type'] == 'relation'), segments[0])
        flowing_by_name[key] = {
            'osm_id': representative['osm_id'],
            'osm_type': representative['osm_type'],
            'name': representative['name'],
            'type': representative['type'],
            'lat': avg_lat,
            'lon': avg_lon,
        }

    # Combine
    result = list(standing_by_id.values()) + list(flowing_by_name.values())
    print(f"  Deduplicated: {len(standing_by_id)} standing + {len(flowing_by_name)} flowing = {len(result)} total")

    return result


if __name__ == '__main__':
    import json, sys
    state = sys.argv[1] if len(sys.argv) > 1 else 'UT'
    features = download_osm_water_features(state)
    print(f"\nTotal: {len(features)} water features")
    # Save to file for inspection
    outfile = f".claude/states/{state.lower()}/osm_water_features.json"
    with open(outfile, 'w') as f:
        json.dump(features, f, indent=2)
    print(f"Saved to {outfile}")
