"""
GNIS Enrichment — Backfill county data and coordinate gap-fill for existing bible entries.

Queries both GNIS layers:
  - Layer 6: Streams (mouth points)
  - Layer 7: Other hydrographic features (lakes, reservoirs, springs, etc.)

Then matches against existing water_bodies to:
  1. Backfill missing county (using proximity to disambiguate duplicate names)
  2. Identify coordinate gaps (waters with no authoritative source)
  3. Report GNIS waters NOT in bible (potential additions)
  4. Report bible waters NOT in GNIS (review needed)

Usage:
    python3 -m pipeline.enrich_gnis --state UT              # Dry run (report only)
    python3 -m pipeline.enrich_gnis --state UT --apply       # Apply changes to DB
"""

import re, click, requests, time, json, math, struct
from collections import defaultdict
from pipeline.config import supabase

STATE_BBOXES = {
    'UT': {'xmin': -114.05, 'ymin': 36.99, 'xmax': -109.04, 'ymax': 42.00},
    'ID': {'xmin': -117.24, 'ymin': 41.99, 'xmax': -111.04, 'ymax': 49.00},
    'MT': {'xmin': -116.05, 'ymin': 44.36, 'xmax': -104.04, 'ymax': 49.00},
    'WY': {'xmin': -111.06, 'ymin': 40.99, 'xmax': -104.05, 'ymax': 45.01},
    'CO': {'xmin': -109.06, 'ymin': 36.99, 'xmax': -102.04, 'ymax': 41.00},
}

WATER_FEATURE_CLASSES = {'lake', 'reservoir', 'stream', 'canal', 'falls', 'rapids', 'spring'}


def haversine_km(lat1, lon1, lat2, lon2):
    """Distance in km between two lat/lon points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def download_gnis_layer(state: str, layer: int) -> list[dict]:
    """Download all water features from a GNIS MapServer layer."""
    url = f"https://carto.nationalmap.gov/arcgis/rest/services/geonames/MapServer/{layer}/query"
    all_features = []
    offset = 0

    while True:
        resp = requests.get(url, params={
            "where": f"state_alpha = '{state}'",
            "outFields": "gaz_id,gaz_name,gaz_featureclass,county_name",
            "returnGeometry": "true", "outSR": "4326", "f": "json",
            "resultRecordCount": "2000", "resultOffset": str(offset)
        }, timeout=60)

        data = resp.json()
        features = data.get('features', [])
        if not features:
            break

        for f in features:
            a = f['attributes']
            geom = f.get('geometry', {})

            # Layer 6 (streams) has multipoint geometry
            if layer == 6:
                points = geom.get('points', [])
                if points and a.get('gaz_name'):
                    lat, lon = points[0][1], points[0][0]
                    all_features.append({
                        'gaz_id': a.get('gaz_id'),
                        'name': a['gaz_name'],
                        'type': (a.get('gaz_featureclass', '') or '').lower(),
                        'county': a.get('county_name', ''),
                        'lat': lat, 'lon': lon,
                    })
            # Layer 7 has point geometry
            elif layer == 7:
                if geom.get('y') and geom.get('x') and a.get('gaz_name'):
                    all_features.append({
                        'gaz_id': a.get('gaz_id'),
                        'name': a['gaz_name'],
                        'type': (a.get('gaz_featureclass', '') or '').lower(),
                        'county': a.get('county_name', ''),
                        'lat': geom['y'], 'lon': geom['x'],
                    })

        offset += 2000
        if len(features) < 2000:
            break
        time.sleep(0.3)

    return all_features


def download_gnis(state: str) -> tuple[dict[str, list[dict]], int]:
    """Download all GNIS water features (both layers).
    Returns ({lowercase_name: [list of features with that name]}, total_unique_count).
    Multiple features can share a name (e.g. "Hidden Lake" in different counties).
    """
    print(f"\n[1] GNIS: Downloading water features for {state}...")

    layer7 = download_gnis_layer(state, 7)
    print(f"  Layer 7 (lakes/reservoirs/etc): {len(layer7)} features")

    layer6 = download_gnis_layer(state, 6)
    print(f"  Layer 6 (streams): {len(layer6)} features")

    all_features = layer7 + layer6
    water_features = [f for f in all_features if f['type'] in WATER_FEATURE_CLASSES]
    print(f"  Water features after filter: {len(water_features)}")

    # Group by name — keep ALL features (don't dedup, same name in different counties)
    by_name = defaultdict(list)
    for f in water_features:
        key = f['name'].lower().strip()
        by_name[key].append(f)

    unique = len(by_name)
    print(f"  Unique names: {unique} (total features: {len(water_features)})")
    return dict(by_name), unique


def download_nhdplus(state: str) -> dict[str, tuple]:
    """Download NHDPlus waterbody centroids. Returns {lowercase_name: (lat, lon)}."""
    print(f"\n[2] NHDPlus: Downloading polygon centroids for {state}...")
    bbox = STATE_BBOXES.get(state)
    if not bbox:
        return {}

    url = "https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer/9/query"
    resp = requests.get(url, params={
        "where": "gnis_name IS NOT NULL AND gnis_name <> ''",
        "geometry": f"{bbox['xmin']},{bbox['ymin']},{bbox['xmax']},{bbox['ymax']}",
        "geometryType": "esriGeometryEnvelope", "inSR": "4326",
        "outFields": "gnis_name,areasqkm", "returnGeometry": "true",
        "outSR": "4326", "f": "json", "resultRecordCount": "2000"
    }, timeout=60)

    features = resp.json().get('features', [])
    centroids = {}
    for f in features:
        name = f['attributes']['gnis_name'].lower().strip()
        rings = f.get('geometry', {}).get('rings', [[]])
        all_x = [p[0] for ring in rings for p in ring]
        all_y = [p[1] for ring in rings for p in ring]
        if all_x:
            area = f['attributes'].get('areasqkm', 0) or 0
            if name not in centroids or area > centroids[name][2]:
                centroids[name] = (sum(all_y)/len(all_y), sum(all_x)/len(all_x), area)

    result = {name: (lat, lon) for name, (lat, lon, _) in centroids.items()}
    print(f"  NHDPlus centroids: {len(result)}")
    return result


def normalize_name(name: str) -> str:
    """Normalize water body name for matching."""
    n = name.lower().strip()
    # Remove parenthetical qualifiers: "(Blue Ribbon)", "(North Slope)", etc.
    n = re.sub(r'\s*\(.*?\)\s*', ' ', n)
    # Remove comma-separated qualifiers: ", Deep Creek Mtns."
    n = re.sub(r',\s*.*$', '', n)
    # Remove "- " prefixed qualifiers: "First Dam - Logan River" → "First Dam"
    # But keep the full name as a variant too
    n = re.sub(r'\s+', ' ', n)
    return n.strip()


def name_variants(name: str) -> list[str]:
    """Generate matching variants of a water body name."""
    base = normalize_name(name)
    variants = [base]

    # Also try the part after " - " (e.g. "First Dam - Logan River" → "Logan River")
    if ' - ' in name.lower():
        parts = name.lower().split(' - ')
        for p in parts:
            p = p.strip()
            if p and p not in variants:
                variants.append(p)

    # Strip common suffixes and try alternatives
    suffixes = [' reservoir', ' lake', ' creek', ' pond', ' river', ' stream']
    for s in suffixes:
        if base.endswith(s):
            stripped = base[:-len(s)].strip()
            if stripped:
                variants.append(stripped)
                for add in suffixes:
                    if add != s:
                        candidate = stripped + add
                        if candidate not in variants:
                            variants.append(candidate)
            break

    # Try without "state park", "golf course ponds", regional qualifiers
    for qual in [' state park', ' golf course ponds', ' golf course pond',
                 ', southeastern utah', ', northern utah',
                 ', north slope', ', south slope']:
        if qual in base:
            cleaned = base.replace(qual, '').strip()
            if cleaned and cleaned not in variants:
                variants.append(cleaned)

    return variants


def parse_coordinates(coords_value) -> tuple[float, float] | None:
    """Parse coordinates from Supabase PostGIS response.
    PostgREST returns geography as WKB hex: '0101000020E6100000...'
    """
    if not coords_value:
        return None

    if isinstance(coords_value, dict):
        c = coords_value.get('coordinates')
        if c and len(c) >= 2:
            return (c[1], c[0])

    if isinstance(coords_value, str):
        # WKT format
        m = re.match(r'POINT\(([-\d.]+)\s+([-\d.]+)\)', coords_value)
        if m:
            return (float(m.group(2)), float(m.group(1)))

        # PostGIS WKB hex format (most common from Supabase)
        if re.match(r'^[0-9a-fA-F]+$', coords_value) and len(coords_value) >= 50:
            try:
                raw = bytes.fromhex(coords_value)
                if len(raw) >= 25:
                    byte_order = raw[0]
                    fmt = '<' if byte_order == 1 else '>'
                    # Skip: byte_order(1) + type(4) + srid(4) = 9 bytes
                    lon = struct.unpack(fmt + 'd', raw[9:17])[0]
                    lat = struct.unpack(fmt + 'd', raw[17:25])[0]
                    if -180 <= lon <= 180 and -90 <= lat <= 90:
                        return (lat, lon)
            except (ValueError, struct.error):
                pass

    return None


def find_closest_gnis(bible_lat, bible_lon, gnis_candidates: list[dict]) -> dict:
    """Given bible coordinates and multiple GNIS features with the same name,
    return the one closest to the bible entry."""
    if len(gnis_candidates) == 1:
        return gnis_candidates[0]

    best = None
    best_dist = float('inf')
    for g in gnis_candidates:
        d = haversine_km(bible_lat, bible_lon, g['lat'], g['lon'])
        if d < best_dist:
            best_dist = d
            best = g

    return best


def fetch_bible_waters(state: str) -> list[dict]:
    """Fetch all existing water bodies for a state from Supabase."""
    print(f"\n[3] Fetching existing bible entries for {state}...")
    result = supabase.table("water_bodies").select(
        "id,name,state,county,type,coordinates"
    ).eq("state", state).execute()
    print(f"  Bible entries: {len(result.data)}")
    return result.data


def fetch_aliases(state: str) -> dict[str, list[str]]:
    """Fetch all aliases for a state's water bodies. Returns {water_body_id: [aliases]}."""
    wb_ids = supabase.table("water_bodies").select("id").eq("state", state).execute()
    ids = [w["id"] for w in wb_ids.data]

    by_wb = defaultdict(list)
    alias_to_wb = {}
    batch_size = 50
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        aliases = supabase.table("water_body_aliases").select(
            "alias,water_body_id"
        ).in_("water_body_id", batch).execute()
        for a in aliases.data:
            by_wb[a["water_body_id"]].append(a["alias"])
            alias_to_wb[a["alias"].lower().strip()] = a["water_body_id"]

    return by_wb, alias_to_wb


@click.command()
@click.option('--state', required=True, help='2-letter state code')
@click.option('--apply', 'do_apply', is_flag=True, default=False, help='Apply changes to DB (default: dry run)')
def enrich(state: str, do_apply: bool):
    state = state.upper()
    bbox = STATE_BBOXES.get(state)
    if not bbox:
        print(f"No bounding box for {state}")
        return

    mode = "APPLY" if do_apply else "DRY RUN"
    print("=" * 60)
    print(f"GNIS ENRICHMENT — {state} ({mode})")
    print("=" * 60)

    # Download sources
    gnis, gnis_unique = download_gnis(state)
    nhd = download_nhdplus(state)
    bible = fetch_bible_waters(state)
    aliases_by_wb, alias_to_wb = fetch_aliases(state)

    # Build bible lookup
    bible_by_id = {w['id']: w for w in bible}
    bible_by_name = {}
    for w in bible:
        key = w['name'].lower().strip()
        bible_by_name[key] = w

    # Parse bible coordinates
    bible_coords = {}  # wb_id → (lat, lon)
    coords_missing = 0
    for w in bible:
        c = parse_coordinates(w.get('coordinates'))
        if c:
            bible_coords[w['id']] = c
        else:
            coords_missing += 1
    print(f"\n  Bible coords parsed: {len(bible_coords)}, missing: {coords_missing}")

    # ========================================
    # Match bible entries to GNIS (proximity-aware)
    # ========================================
    print(f"\n[4] Matching bible entries to GNIS (proximity-aware)...")

    matched = []       # (bible_entry, gnis_entry, distance_km)
    unmatched = []     # bible entries with no GNIS match

    for w in bible:
        name = w['name']
        wb_coords = bible_coords.get(w['id'])

        # Generate all name variants to try
        all_variants = name_variants(name)

        # Also try variants from aliases
        for alias in aliases_by_wb.get(w['id'], []):
            for v in name_variants(alias):
                if v not in all_variants:
                    all_variants.append(v)

        # Find all GNIS candidates across all variants
        candidates = []
        for v in all_variants:
            if v in gnis:
                candidates.extend(gnis[v])

        if not candidates:
            unmatched.append(w)
            continue

        # Pick the closest one if we have bible coordinates
        if wb_coords and len(candidates) > 1:
            best = find_closest_gnis(wb_coords[0], wb_coords[1], candidates)
            dist = haversine_km(wb_coords[0], wb_coords[1], best['lat'], best['lon'])
        elif wb_coords:
            best = candidates[0]
            dist = haversine_km(wb_coords[0], wb_coords[1], best['lat'], best['lon'])
        else:
            best = candidates[0]
            dist = -1  # unknown

        matched.append((w, best, dist))

    print(f"  Matched: {len(matched)} / {len(bible)}")
    print(f"  Unmatched: {len(unmatched)} / {len(bible)}")

    # Distance stats for matches
    dists = [d for _, _, d in matched if d >= 0]
    if dists:
        close = sum(1 for d in dists if d < 5)
        medium = sum(1 for d in dists if 5 <= d < 25)
        far = sum(1 for d in dists if d >= 25)
        print(f"  Distance: <5km={close}, 5-25km={medium}, >25km={far}")

    # Flag suspicious matches (>50km apart — likely wrong match)
    suspicious = [(w, g, d) for w, g, d in matched if d > 50]
    if suspicious:
        print(f"  SUSPICIOUS (>50km): {len(suspicious)} — likely wrong GNIS match")

    # ========================================
    # Analyze: county backfill
    # ========================================
    county_backfill = []   # (bible_entry, gnis_county, distance)
    county_already = 0
    county_mismatch = []   # (bible_entry, bible_county, gnis_county, distance)

    for bible_w, gnis_w, dist in matched:
        # Skip suspicious far matches for county assignment
        if dist > 50:
            continue

        gnis_county = (gnis_w.get('county', '') or '').strip()
        bible_county = (bible_w.get('county', '') or '').strip()

        if not bible_county and gnis_county:
            county_backfill.append((bible_w, gnis_county, dist))
        elif bible_county and gnis_county:
            # Normalize county comparison (strip " County" suffix if present)
            bc = bible_county.lower().replace(' county', '').strip()
            gc = gnis_county.lower().replace(' county', '').strip()
            if bc != gc:
                county_mismatch.append((bible_w, bible_county, gnis_county, dist))
            else:
                county_already += 1

    print(f"\n[5] County analysis:")
    print(f"  Already correct: {county_already}")
    print(f"  Need backfill: {len(county_backfill)}")
    print(f"  Mismatches: {len(county_mismatch)}")

    # ========================================
    # Analyze: GNIS-only waters (not in bible)
    # ========================================
    print(f"\n[6] GNIS waters not in bible...")

    # Build set of all matched GNIS names
    matched_gnis_names = set()
    for _, gnis_w, _ in matched:
        matched_gnis_names.add(gnis_w['name'].lower().strip())

    gnis_only = []
    gnis_only_by_type = defaultdict(list)
    for gnis_name, gnis_list in gnis.items():
        if gnis_name in matched_gnis_names:
            continue
        # Check name variants against bible
        found = False
        for v in name_variants(gnis_name):
            if v in bible_by_name or v in alias_to_wb:
                found = True
                break
        if not found:
            # Use first feature as representative
            g = gnis_list[0]
            gnis_only.append(g)
            gnis_only_by_type[g['type']].append(g)

    print(f"  GNIS-only waters: {len(gnis_only)}")

    # ========================================
    # Report
    # ========================================
    print(f"\n{'=' * 60}")
    print(f"ENRICHMENT REPORT — {state}")
    print(f"{'=' * 60}")

    print(f"\n## Summary")
    print(f"  Bible entries:        {len(bible)}")
    print(f"  GNIS unique names:    {gnis_unique}")
    print(f"  NHDPlus centroids:    {len(nhd)}")
    print(f"  Match rate:           {len(matched)}/{len(bible)} ({100*len(matched)/max(len(bible),1):.1f}%)")
    print(f"  Unmatched bible:      {len(unmatched)}")

    print(f"\n## County Backfill ({len(county_backfill)} waters)")
    for w, county, dist in county_backfill[:25]:
        print(f"  {w['name']:45s} <- {county:15s} ({dist:.1f}km)")
    if len(county_backfill) > 25:
        print(f"  ... and {len(county_backfill) - 25} more")

    if county_mismatch:
        print(f"\n## County Mismatches ({len(county_mismatch)}) — GNIS says different county")
        for w, old, new, dist in county_mismatch[:15]:
            print(f"  {w['name']:40s} bible={old:15s} gnis={new:15s} ({dist:.1f}km)")
        if len(county_mismatch) > 15:
            print(f"  ... and {len(county_mismatch) - 15} more")

    if suspicious:
        print(f"\n## Suspicious Matches ({len(suspicious)}) — >50km from bible coords")
        for w, g, d in suspicious:
            print(f"  {w['name']:40s} → GNIS '{g['name']}' in {g.get('county','')} ({d:.0f}km away)")

    print(f"\n## Unmatched Bible Entries ({len(unmatched)})")
    for w in unmatched[:25]:
        print(f"  {w['name']:45s} type={w.get('type', '?')}")
    if len(unmatched) > 25:
        print(f"  ... and {len(unmatched) - 25} more")

    print(f"\n## GNIS-Only Waters — By Type ({len(gnis_only)} total)")
    for t in sorted(gnis_only_by_type.keys()):
        waters = gnis_only_by_type[t]
        print(f"  {t}: {len(waters)}")
        for g in waters[:3]:
            print(f"    {g['name']:40s} {g.get('county', '')}")
        if len(waters) > 3:
            print(f"    ... and {len(waters) - 3} more")

    # Fishable GNIS-only (lakes + reservoirs only — most relevant)
    fishable_only = [g for g in gnis_only if g['type'] in ('lake', 'reservoir')]
    print(f"\n## Fishable GNIS-Only (lakes + reservoirs): {len(fishable_only)}")
    for g in fishable_only[:20]:
        print(f"  {g['name']:45s} {g['type']:12s} {g.get('county', '')}")
    if len(fishable_only) > 20:
        print(f"  ... and {len(fishable_only) - 20} more")

    # ========================================
    # Apply changes if requested
    # ========================================
    if do_apply:
        print(f"\n{'=' * 60}")
        print(f"APPLYING CHANGES...")
        print(f"{'=' * 60}")

        updated = 0
        for w, county, dist in county_backfill:
            try:
                supabase.table("water_bodies").update({
                    "county": county
                }).eq("id", w['id']).execute()
                updated += 1
            except Exception as e:
                print(f"  Error updating {w['name']}: {e}")

        print(f"  Counties backfilled: {updated}")
    else:
        print(f"\n--- DRY RUN complete. Run with --apply to make changes. ---")

    # Save report
    report_path = f"/Users/taylorwall/Library/Mobile Documents/com~apple~CloudDocs/dev/fish/.claude/states/{state.lower()}/gnis_enrichment_report.json"
    report = {
        "state": state,
        "mode": mode,
        "bible_count": len(bible),
        "gnis_unique_names": gnis_unique,
        "nhd_count": len(nhd),
        "matched": len(matched),
        "match_rate_pct": round(100 * len(matched) / max(len(bible), 1), 1),
        "unmatched_count": len(unmatched),
        "unmatched_names": [w['name'] for w in unmatched],
        "county_backfill_count": len(county_backfill),
        "county_backfill": [{"name": w['name'], "id": w['id'], "county": c, "dist_km": round(d, 1)} for w, c, d in county_backfill],
        "county_mismatches": [{"name": w['name'], "bible": old, "gnis": new, "dist_km": round(d, 1)} for w, old, new, d in county_mismatch],
        "suspicious_matches": [{"name": w['name'], "gnis_name": g['name'], "gnis_county": g.get('county', ''), "dist_km": round(d, 0)} for w, g, d in suspicious],
        "gnis_only_count": len(gnis_only),
        "gnis_only_by_type": {t: len(ws) for t, ws in gnis_only_by_type.items()},
        "fishable_only_count": len(fishable_only),
        "fishable_only": [{"name": g['name'], "type": g['type'], "county": g.get('county', ''), "lat": g['lat'], "lon": g['lon']} for g in fishable_only],
    }
    try:
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved: {report_path}")
    except Exception as e:
        print(f"\nCould not save report: {e}")


if __name__ == '__main__':
    enrich()
