"""
State Onboarding v2 — One pass. No patches.

The process:
1. GNIS → foundation (name, county, coordinates, type) for ALL named water features in the state
2. State planner → filter to fishable waters + add survey-confirmed species
3. Stocking reports → add stocked waters not in planner + stocking-confirmed species + alias mapping
4. NHDPlus → upgrade coordinates for big lakes (polygon centroid > point)
5. USGS/NOAA → wire by coordinates
6. Import stocking events → exact alias match only

Usage:
    python -m pipeline.onboard_v2 --state UT
"""

import json, re, os, click, requests, time
from collections import defaultdict
from difflib import SequenceMatcher
from pipeline.config import supabase
from pipeline.fetcher import fetch
from pipeline.parsers.haiku import parse_stocking


# ============================================================
# GNIS: Download all named water features for a state
# ============================================================

STATE_BBOXES = {
    'UT': {'xmin': -114.05, 'ymin': 36.99, 'xmax': -109.04, 'ymax': 42.00},
    'ID': {'xmin': -117.24, 'ymin': 41.99, 'xmax': -111.04, 'ymax': 49.00},
    'MT': {'xmin': -116.05, 'ymin': 44.36, 'xmax': -104.04, 'ymax': 49.00},
    'WY': {'xmin': -111.06, 'ymin': 40.99, 'xmax': -104.05, 'ymax': 45.01},
    'CO': {'xmin': -109.06, 'ymin': 36.99, 'xmax': -102.04, 'ymax': 41.00},
}

def _download_gnis_layer(state: str, layer: int) -> list[dict]:
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

        features = resp.json().get('features', [])
        if not features:
            break

        for f in features:
            a = f['attributes']
            geom = f.get('geometry', {})

            if layer == 6:
                # Layer 6 (streams) — multipoint geometry
                points = geom.get('points', [])
                if points and a.get('gaz_name'):
                    ftype = (a.get('gaz_featureclass', '') or '').lower()
                    if ftype in ('lake', 'reservoir', 'stream', 'canal', 'falls', 'rapids', 'spring'):
                        all_features.append({
                            'name': a['gaz_name'],
                            'type': ftype,
                            'county': a.get('county_name', ''),
                            'lat': points[0][1], 'lon': points[0][0],
                        })
            elif layer == 7:
                # Layer 7 — point geometry
                if geom.get('y') and geom.get('x') and a.get('gaz_name'):
                    ftype = (a.get('gaz_featureclass', '') or '').lower()
                    if ftype in ('lake', 'reservoir', 'stream', 'canal', 'falls', 'rapids', 'spring'):
                        all_features.append({
                            'name': a['gaz_name'],
                            'type': ftype,
                            'county': a.get('county_name', ''),
                            'lat': geom['y'], 'lon': geom['x'],
                        })

        offset += 2000
        if len(features) < 2000:
            break
        time.sleep(0.3)

    return all_features


def download_gnis(state: str) -> dict[str, dict]:
    """Download GNIS water features from both layers (streams + hydro).
    Returns {lowercase_name: {name, type, county, lat, lon}}.
    For duplicate names, keeps first occurrence (layer 7 before layer 6).
    """
    print(f"\n[1/6] GNIS: Downloading water features for {state}...")

    layer7 = _download_gnis_layer(state, 7)
    print(f"  Layer 7 (lakes/reservoirs/etc): {len(layer7)}")
    layer6 = _download_gnis_layer(state, 6)
    print(f"  Layer 6 (streams): {len(layer6)}")

    all_features = layer7 + layer6

    # Deduplicate by name (keep first occurrence)
    by_name = {}
    for f in all_features:
        key = f['name'].lower().strip()
        if key not in by_name:
            by_name[key] = f

    print(f"  GNIS total: {len(all_features)}, unique names: {len(by_name)}")
    return by_name


# ============================================================
# NHDPlus: Get polygon centroids for coordinate upgrades
# ============================================================

def download_nhdplus(state: str) -> dict[str, tuple]:
    """Download NHDPlus waterbody centroids. Returns {lowercase_name: (lat, lon)}"""
    print(f"\n[4/6] NHDPlus: Downloading polygon centroids for {state}...")

    bbox = STATE_BBOXES.get(state)
    if not bbox:
        print(f"  No bbox for {state}, skipping NHDPlus")
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


# ============================================================
# DWR abbreviation expander
# ============================================================

def expand_dwr(abbr: str) -> str:
    """Expand DWR abbreviated name to full name."""
    r = ' ' + abbr.strip() + ' '
    subs = [
        (' CR ', ' Creek '), (' RES ', ' Reservoir '), (' L ', ' Lake '),
        (' R ', ' River '), (' P ', ' Pond '), (' FK ', ' Fork '),
        (' MTN ', ' Mountain '), (' MTNS ', ' Mountains '),
        (' N ', ' North '), (' S ', ' South '), (' E ', ' East '), (' W ', ' West '),
        (' SP ', ' Springs '), (' CYN ', ' Canyon '), (' ST ', ' State '),
    ]
    for old, new in subs:
        r = r.replace(old, new)
    r = r.strip()
    for old, new in [(' CR', ' Creek'), (' RES', ' Reservoir'), (' L', ' Lake'),
                      (' R', ' River'), (' P', ' Pond'), (' FK', ' Fork'),
                      (' SP', ' Springs'), (' CYN', ' Canyon')]:
        if r.endswith(old):
            r = r[:-len(old)] + new
    # Strip alphanumeric codes like "W-30", "A-1"
    r = re.sub(r'\s+[A-Z]+-\d+$', '', r).strip()
    r = re.sub(r'\s+#\d+$', '', r).strip()
    return r.title()


# ============================================================
# Main onboarding pipeline
# ============================================================

@click.command()
@click.option('--state', required=True, help='2-letter state code')
@click.option('--planner-file', default=None, help='Path to state planner species JSON')
@click.option('--stocking-urls', default=None, help='Comma-separated stocking report URLs')
def onboard(state: str, planner_file: str, stocking_urls: str):
    state = state.upper()
    bbox = STATE_BBOXES.get(state)
    if not bbox:
        print(f"No bounding box configured for {state}")
        return

    print("=" * 60)
    print(f"ONBOARDING {state} — v2 (one pass, no patches)")
    print("=" * 60)

    # ========================================
    # Step 1: GNIS foundation
    # ========================================
    gnis = download_gnis(state)

    # ========================================
    # Step 2: State planner species
    # ========================================
    planner_species = {}
    if planner_file and os.path.exists(planner_file):
        print(f"\n[2/6] Planner: Loading species from {planner_file}...")
        with open(planner_file) as f:
            planner_species = json.load(f)
        print(f"  Planner waters with species: {len(planner_species)}")
    else:
        print(f"\n[2/6] Planner: No planner file provided, skipping")

    # ========================================
    # Step 3: Stocking reports
    # ========================================
    stocking_events = []
    stocking_species = defaultdict(set)  # water_name → {species}
    stocking_names = set()

    if stocking_urls:
        print(f"\n[3/6] Stocking: Scraping reports...")

        # Get or create prompt template
        pt = supabase.table("prompt_templates").select("system_prompt").eq("state", state).eq("is_active", True).execute()
        if pt.data:
            system_prompt = pt.data[0]["system_prompt"]
        else:
            system_prompt = f"Extract fish stocking events. Normalize species names to canonical form (Rainbow Trout, Brown Trout, etc). Dates: MM/DD/YYYY→YYYY-MM-DD. Quantity: integer."
            supabase.table("prompt_templates").insert({
                "name": f"{state.lower()}_stocking_v1", "state": state,
                "source_type": "stocking", "version": 1,
                "system_prompt": system_prompt, "schema_json": {}, "is_active": True
            }).execute()

        for url in stocking_urls.split(','):
            url = url.strip()
            print(f"  Fetching {url}...")
            result = fetch(url)
            if not result.success:
                print(f"    FAILED: {result.status_code}")
                continue
            print(f"    {result.response_size:,} bytes")

            events = parse_stocking(result.html, system_prompt)
            print(f"    Parsed: {len(events)} events")
            stocking_events.extend(events)

            for e in events:
                if e.water_body_name:
                    stocking_names.add(e.water_body_name)
                    if e.species:
                        stocking_species[e.water_body_name].add(e.species)

        print(f"  Total events: {len(stocking_events)}")
        print(f"  Unique water names: {len(stocking_names)}")
    else:
        print(f"\n[3/6] Stocking: No URLs provided, skipping")

    # ========================================
    # Step 4: NHDPlus coordinate upgrades
    # ========================================
    nhd_centroids = download_nhdplus(state)

    # ========================================
    # Step 5: Build the bible — ONE PASS
    # ========================================
    print(f"\n[5/6] Building bible...")

    # Species lookup
    sp_list = supabase.table("species").select("id, common_name").execute()
    sp_map = {s["common_name"].lower(): s["id"] for s in sp_list.data}
    sp_aliases = supabase.table("species_aliases").select("alias, species_id").limit(500).execute()
    for a in sp_aliases.data:
        sp_map[a["alias"].lower()] = a["species_id"]

    def find_sp(name):
        n = name.lower().strip()
        if n in sp_map: return sp_map[n]
        for key, sid in sp_map.items():
            if n in key or key in n: return sid
        return None

    # Determine which waters to include:
    # 1. Waters in the planner (fishable, has species)
    # 2. Waters in stocking reports (fishable, has been stocked)

    waters_to_import = {}  # canonical_name → {name, county, lat, lon, type, species, stocking_species, source}

    # Pass A: Planner waters
    for planner_name, species_list in planner_species.items():
        canonical = planner_name.lower().strip()
        # Also try without parenthetical qualifiers for GNIS matching
        clean = re.sub(r'\s*\(.*?\)\s*', '', planner_name).strip().lower()

        # Find in GNIS
        gnis_match = gnis.get(canonical) or gnis.get(clean)

        # Try suffix swaps
        if not gnis_match:
            for strip in [' reservoir', ' lake', ' creek', ' pond', ' river']:
                base = clean.replace(strip, '').strip()
                for add in [' reservoir', ' lake', ' creek', ' pond', ' river', '']:
                    gnis_match = gnis.get(base + add)
                    if gnis_match: break
                if gnis_match: break

        if gnis_match:
            lat, lon = gnis_match['lat'], gnis_match['lon']
        else:
            # Try NHDPlus
            nhd = nhd_centroids.get(canonical) or nhd_centroids.get(clean)
            if not nhd:
                for strip in [' reservoir', ' lake', ' creek', ' pond']:
                    base = clean.replace(strip, '').strip()
                    for add in [' reservoir', ' lake', ' creek', ' pond', '']:
                        nhd = nhd_centroids.get(base + add)
                        if nhd: break
                    if nhd: break
            if nhd:
                lat, lon = nhd
            else:
                continue  # No coordinates, skip

        # Validate coords
        if not (bbox['ymin'] <= lat <= bbox['ymax'] and bbox['xmin'] <= lon <= bbox['xmax']):
            continue

        # NHDPlus upgrade for big lakes
        nhd_upgrade = nhd_centroids.get(canonical) or nhd_centroids.get(clean)
        if nhd_upgrade:
            lat, lon = nhd_upgrade

        county = gnis_match['county'] if gnis_match else ''
        wtype = gnis_match['type'] if gnis_match else 'lake'

        # Normalize type
        if wtype == 'stream': wtype = 'creek'
        if wtype not in ('lake', 'reservoir', 'creek', 'river', 'pond', 'stream'):
            n = planner_name.lower()
            if 'reservoir' in n: wtype = 'reservoir'
            elif 'lake' in n: wtype = 'lake'
            elif 'river' in n: wtype = 'river'
            elif 'creek' in n: wtype = 'creek'
            elif 'pond' in n: wtype = 'pond'
            else: wtype = 'lake'

        waters_to_import[canonical] = {
            'name': planner_name,
            'county': county,
            'lat': lat,
            'lon': lon,
            'type': wtype,
            'species': species_list,  # From planner — authoritative
            'stocking_species': set(),
            'source': 'planner',
            'aliases': [planner_name],
        }

    print(f"  Planner waters with coords: {len(waters_to_import)}")

    # Pass B: Stocking-only waters (not already in from planner)
    stocking_added = 0
    for dwr_name in stocking_names:
        expanded = expand_dwr(dwr_name)
        canonical = expanded.lower().strip()

        # Skip if already imported from planner
        if canonical in waters_to_import:
            # Just add the DWR name as an alias and stocking species
            waters_to_import[canonical]['aliases'].append(dwr_name)
            waters_to_import[canonical]['stocking_species'].update(stocking_species.get(dwr_name, set()))
            continue

        # Check if planner has it under a different key
        found = False
        for key in waters_to_import:
            if canonical in key or key in canonical:
                waters_to_import[key]['aliases'].append(dwr_name)
                waters_to_import[key]['stocking_species'].update(stocking_species.get(dwr_name, set()))
                found = True
                break
        if found:
            continue

        # New water — find in GNIS
        gnis_match = gnis.get(canonical)
        if not gnis_match:
            # Try without trailing qualifiers
            clean = re.sub(r',\s*.*$', '', canonical).strip()
            gnis_match = gnis.get(clean)

        if not gnis_match:
            continue  # No GNIS entry, skip

        lat, lon = gnis_match['lat'], gnis_match['lon']
        if not (bbox['ymin'] <= lat <= bbox['ymax'] and bbox['xmin'] <= lon <= bbox['xmax']):
            continue

        # NHDPlus upgrade
        nhd = nhd_centroids.get(canonical)
        if nhd:
            lat, lon = nhd

        county = gnis_match['county']
        wtype = gnis_match['type']
        if wtype == 'stream': wtype = 'creek'
        if wtype not in ('lake', 'reservoir', 'creek', 'river', 'pond', 'stream'):
            wtype = 'lake'

        waters_to_import[canonical] = {
            'name': expanded,
            'county': county,
            'lat': lat,
            'lon': lon,
            'type': wtype,
            'species': [],  # No planner data
            'stocking_species': stocking_species.get(dwr_name, set()),
            'source': 'stocking',
            'aliases': [expanded, dwr_name],
        }
        stocking_added += 1

    print(f"  Stocking-only waters added: {stocking_added}")
    print(f"  Total waters to import: {len(waters_to_import)}")

    # ========================================
    # Step 6: Import to database
    # ========================================
    print(f"\n[6/6] Importing to Supabase...")

    imported = 0
    alias_count = 0
    species_count = 0
    wb_id_map = {}  # canonical → id
    alias_to_wb = {}  # alias_lower → id

    for canonical, w in waters_to_import.items():
        try:
            result = supabase.table("water_bodies").insert({
                "name": w['name'],
                "state": state,
                "county": w['county'],
                "type": w['type'],
                "coordinates": f"POINT({w['lon']} {w['lat']})",
                "has_stocking": bool(w['stocking_species']),
                "has_flow_data": w['type'] in ('creek', 'river', 'stream'),
                "has_level_data": w['type'] in ('lake', 'reservoir'),
                "status": "active",
            }).execute()

            if not result.data:
                continue

            wb_id = result.data[0]["id"]
            wb_id_map[canonical] = wb_id
            imported += 1

            # Aliases (deduplicated)
            seen_aliases = set()
            for i, alias in enumerate(w['aliases']):
                if alias.lower() in seen_aliases:
                    continue
                seen_aliases.add(alias.lower())
                try:
                    supabase.table("water_body_aliases").insert({
                        "water_body_id": wb_id,
                        "alias": alias,
                        "source": "state_dwr" if i == 0 else "state_dwr_stocking",
                        "is_primary": (i == 0)
                    }).execute()
                    alias_to_wb[alias.lower()] = wb_id
                    alias_count += 1
                except:
                    pass

            # Species from planner (authoritative)
            seen_species = set()
            for sp_name in w['species']:
                sp_id = find_sp(sp_name)
                if sp_id and sp_id not in seen_species:
                    seen_species.add(sp_id)
                    try:
                        supabase.table("water_body_species").insert({
                            "water_body_id": wb_id,
                            "species_id": sp_id,
                            "is_stocked": False,
                            "data_source": f"{state.lower()}_agency_planner",
                            "confidence": 1.0
                        }).execute()
                        species_count += 1
                    except:
                        pass

            # Species from stocking (additional — not duplicating planner species)
            for sp_name in w['stocking_species']:
                sp_id = find_sp(sp_name)
                if sp_id and sp_id not in seen_species:
                    seen_species.add(sp_id)
                    try:
                        supabase.table("water_body_species").insert({
                            "water_body_id": wb_id,
                            "species_id": sp_id,
                            "is_stocked": True,
                            "data_source": "stocking_records",
                            "confidence": 1.0
                        }).execute()
                        species_count += 1
                    except:
                        pass

            # NOAA data source link
            try:
                supabase.table("data_source_links").insert({
                    "water_body_id": wb_id,
                    "source_type": "noaa_station",
                    "external_id": f"{w['lat']:.4f},{w['lon']:.4f}",
                    "refresh_frequency_hours": 6,
                    "health_status": "healthy"
                }).execute()
            except:
                pass

        except Exception as e:
            if 'duplicate' not in str(e).lower():
                print(f"  Error: {w['name']}: {e}")

    print(f"  Waters imported: {imported}")
    print(f"  Aliases: {alias_count}")
    print(f"  Species entries: {species_count}")

    # ========================================
    # Import stocking events
    # ========================================
    if stocking_events:
        print(f"\n  Importing {len(stocking_events)} stocking events (exact match only)...")
        stored = 0
        skipped = 0

        for e in stocking_events:
            name = (e.water_body_name or "").strip()

            # Exact alias lookup
            wb_id = alias_to_wb.get(name.lower())
            if not wb_id:
                expanded = expand_dwr(name)
                wb_id = alias_to_wb.get(expanded.lower())
            if not wb_id:
                skipped += 1
                continue

            sp_id = find_sp(e.species) if e.species else None

            date = e.date or ""
            if re.match(r'\d{2}/\d{2}/\d{4}', date):
                p = date.split('/')
                date = f"{p[2]}-{p[0]}-{p[1]}"
            if not re.match(r'\d{4}-\d{2}-\d{2}', date):
                skipped += 1
                continue

            try:
                supabase.table("stocking_events").insert({
                    "water_body_id": wb_id,
                    "species_id": sp_id,
                    "species_raw": e.species or "",
                    "quantity": e.quantity or 0,
                    "date": date,
                    "source_agency": f"{state} Fish & Wildlife",
                    "source_url": stocking_urls.split(',')[0].strip() if stocking_urls else "",
                    "confidence_score": 1.0,
                }).execute()
                stored += 1
            except:
                pass

        print(f"  Stocking: {stored} stored, {skipped} skipped")

    # ========================================
    # Wire USGS gauges
    # ========================================
    print(f"\n  Wiring USGS gauges...")
    try:
        resp = requests.get(
            f"https://waterservices.usgs.gov/nwis/site/?format=rdb&stateCd={state}&siteType=ST&siteStatus=active&hasDataTypeCd=iv",
            timeout=30, headers={"User-Agent": "FishOn/1.0"}
        )
        lines = [l for l in resp.text.split('\n') if l and not l.startswith('#')]
        gauges_wired = 0
        for line in lines[2:]:
            parts = line.strip().split('\t')
            if len(parts) >= 6:
                gauge_id = f"USGS-{parts[1]}"
                gauge_name = parts[2].lower()
                try:
                    lat = float(parts[4])
                    lon = float(parts[5])
                except:
                    continue

                # Match to a bible water by name overlap
                for canonical, wb_id in wb_id_map.items():
                    c_words = set(canonical.replace(',', '').split()) - {'river', 'creek', 'the', 'fork', 'near', 'at', 'of', 'lake'}
                    g_words = set(gauge_name.replace(',', '').split()) - {'river', 'creek', 'the', 'fork', 'near', 'at', state.lower(), 'ut'}
                    if c_words and g_words and len(c_words & g_words) >= 1:
                        try:
                            supabase.table("data_source_links").insert({
                                "water_body_id": wb_id,
                                "source_type": "usgs_gauge",
                                "external_id": gauge_id,
                                "refresh_frequency_hours": 1,
                                "health_status": "healthy"
                            }).execute()
                            gauges_wired += 1
                        except:
                            pass
                        break

        print(f"  USGS gauges wired: {gauges_wired}")
    except Exception as e:
        print(f"  USGS error: {e}")

    # ========================================
    # Final report
    # ========================================
    wb_c = supabase.table("water_bodies").select("id", count="exact").eq("state", state).execute()
    sp_c = supabase.table("water_body_species").select("id", count="exact").execute()
    se_c = supabase.table("stocking_events").select("id", count="exact").execute()
    al_c = supabase.table("water_body_aliases").select("id", count="exact").execute()
    dsl_c = supabase.table("data_source_links").select("id", count="exact").execute()

    print(f"\n{'=' * 60}")
    print(f"{state} ONBOARDING COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Waters: {wb_c.count}")
    print(f"  Aliases: {al_c.count}")
    print(f"  Species: {sp_c.count}")
    print(f"  Stocking events: {se_c.count}")
    print(f"  Data source links: {dsl_c.count}")
    print(f"  Coordinates: GNIS + NHDPlus (authoritative)")
    print(f"  Species: planner (survey) + stocking records")
    print(f"  Counties: GNIS (authoritative)")
    print(f"  Stocking: exact alias match only")


if __name__ == '__main__':
    onboard()
