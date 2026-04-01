"""
OSM Bible Migration — Replace water body coordinates with OSM source of truth.

Phase 1 (this script): Names and locations only.
- Match OSM features to existing bible entries
- Update coordinates for matches
- Merge duplicates (multiple bible entries → one OSM feature)
- Insert new OSM features not in bible
- Report bible-only entries (community ponds, etc.)

Usage:
    python3 pipeline/osm_migrate.py --state UT              # Dry run
    python3 pipeline/osm_migrate.py --state UT --apply       # Apply changes
"""

import re, json, click
from collections import defaultdict
from pipeline.config import supabase
from pipeline.geo import parse_wkb, haversine_km, STANDING_TYPES, FLOWING_TYPES
from pipeline.names import normalize, base_name
from pipeline.bible import load_water_bodies_with_coords, load_aliases
from pipeline.osm import download_osm_water_features

# ============================================================
# Utilities
# ============================================================


# ============================================================
# Data loading (uses shared modules)
# ============================================================


def count_fks(wb_id: str) -> int:
    """Count total FK references to a water body (for picking merge survivor)."""
    total = 0
    for table in ['stocking_events', 'conditions', 'weather_forecasts', 'water_body_species']:
        try:
            r = supabase.table(table).select("id", count="exact").eq("water_body_id", wb_id).execute()
            total += r.count or 0
        except:
            pass
    return total


# ============================================================
# Matching
# ============================================================

def match_osm_to_bible(osm_features, bible_entries, alias_to_wb, wb_to_aliases, bible_by_id):
    """Match each OSM feature to bible entries.

    Returns:
        matched: [(osm_feature, [bible_ids])]  — one or more bible entries per OSM feature
        osm_only: [osm_feature]  — no bible match
        bible_only: [bible_entry]  — no OSM match
    """
    print(f"\n[MATCH] Matching {len(osm_features)} OSM features to {len(bible_entries)} bible entries...")

    # Build lookup indices
    bible_by_norm = defaultdict(list)  # normalized_name → [bible_entry]
    bible_by_base = defaultdict(list)  # base_name → [bible_entry]

    for b in bible_entries:
        norm = normalize(b['name'])
        bible_by_norm[norm].append(b)
        bn = base_name(b['name'])
        bible_by_base[bn].append(b)

        # Also index by aliases
        for alias in wb_to_aliases.get(b['id'], []):
            norm_a = normalize(alias)
            bible_by_norm[norm_a].append(b)
            bn_a = base_name(alias)
            bible_by_base[bn_a].append(b)

    # Match each OSM feature
    osm_matched = []   # (osm_feature, [matched_bible_ids])
    osm_only = []
    matched_bible_ids = set()

    for osm in osm_features:
        osm_norm = normalize(osm['name'])
        osm_base = base_name(osm['name'])

        # Find candidate bible entries
        candidates = set()

        # Exact normalized match (high confidence)
        for b in bible_by_norm.get(osm_norm, []):
            candidates.add(b['id'])

        # Base name match — only if types are compatible
        # (prevents "Sevier River" matching "Sevier Lake")
        osm_group = 'standing' if osm['type'] in STANDING_TYPES else 'flowing'
        for b in bible_by_base.get(osm_base, []):
            b_group = 'standing' if b.get('type', '') in STANDING_TYPES else 'flowing'
            # Only match across type groups if exact normalized match
            if osm_group == b_group or osm_norm == normalize(b['name']):
                candidates.add(b['id'])

        # Also try OSM name directly against alias index
        osm_lower = osm['name'].lower().strip()
        if osm_lower in alias_to_wb:
            candidates.add(alias_to_wb[osm_lower])

        if not candidates:
            osm_only.append(osm)
            continue

        # Filter by proximity — all candidates must be within 50km
        close_candidates = []
        for cid in candidates:
            b = bible_by_id.get(cid)
            if b and b.get('lat') and osm.get('lat'):
                d = haversine_km(osm['lat'], osm['lon'], b['lat'], b['lon'])
                if d < 50:
                    close_candidates.append(cid)
            else:
                close_candidates.append(cid)  # No coords to check, keep

        if not close_candidates:
            osm_only.append(osm)
            continue

        osm_matched.append((osm, close_candidates))
        matched_bible_ids.update(close_candidates)

    # Bible-only entries (not matched by any OSM feature)
    bible_only = [b for b in bible_entries if b['id'] not in matched_bible_ids]

    print(f"  Matched: {len(osm_matched)} OSM features → {len(matched_bible_ids)} bible entries")
    print(f"  OSM-only (new): {len(osm_only)}")
    print(f"  Bible-only (no OSM match): {len(bible_only)}")

    return osm_matched, osm_only, bible_only


# ============================================================
# Migration
# ============================================================

@click.command()
@click.option('--state', required=True, help='2-letter state code')
@click.option('--apply', 'do_apply', is_flag=True, default=False, help='Apply changes (default: dry run)')
@click.option('--no-insert', 'skip_insert', is_flag=True, default=False, help='Skip inserting new OSM-only waters')
def migrate(state: str, do_apply: bool, skip_insert: bool):
    state = state.upper()
    mode = "APPLY" if do_apply else "DRY RUN"
    print("=" * 60)
    print(f"OSM BIBLE MIGRATION — {state} ({mode})")
    print("=" * 60)

    # Load OSM data (use cached file if available to avoid rate limits)
    cache_path = f".claude/states/{state.lower()}/osm_water_features.json"
    try:
        with open(cache_path) as f:
            osm_features = json.load(f)
        print(f"  Loaded {len(osm_features)} OSM features from cache: {cache_path}")
    except FileNotFoundError:
        osm_features = download_osm_water_features(state)
    bible = load_water_bodies_with_coords(state)
    alias_to_wb, wb_to_aliases = load_aliases(state)
    bible_by_id = {b['id']: b for b in bible}

    # Match
    osm_matched, osm_only, bible_only = match_osm_to_bible(
        osm_features, bible, alias_to_wb, wb_to_aliases, bible_by_id
    )

    # Categorize matches
    single_matches = []   # (osm, [single_bible_id])
    multi_matches = []    # (osm, [multiple_bible_ids]) — duplicates to merge

    for osm, bible_ids in osm_matched:
        if len(bible_ids) == 1:
            single_matches.append((osm, bible_ids[0]))
        else:
            multi_matches.append((osm, bible_ids))

    print(f"\n  1:1 matches: {len(single_matches)}")
    print(f"  Duplicates to merge: {len(multi_matches)} OSM features → {sum(len(bids) for _, bids in multi_matches)} bible entries")

    # ========================================
    # Report
    # ========================================
    print(f"\n{'=' * 60}")
    print(f"MIGRATION REPORT — {state}")
    print(f"{'=' * 60}")

    print(f"\n## Summary")
    print(f"  OSM features:     {len(osm_features)}")
    print(f"  Bible entries:    {len(bible)}")
    print(f"  1:1 matches:      {len(single_matches)} (will update coords)")
    print(f"  Duplicates:       {len(multi_matches)} groups (will merge)")
    print(f"  OSM-only (new):   {len(osm_only)} (will insert)")
    print(f"  Bible-only:       {len(bible_only)} (will keep as-is)")

    if multi_matches:
        print(f"\n## Duplicate Groups (top 20)")
        for osm, bids in multi_matches[:20]:
            names = [bible_by_id[bid]['name'] for bid in bids if bid in bible_by_id]
            print(f"  OSM '{osm['name']}' ({osm['type']}) merges:")
            for n in names:
                print(f"    - {n}")

    print(f"\n## OSM-Only — New Waters (sample 20 of {len(osm_only)})")
    by_type = defaultdict(int)
    for o in osm_only:
        by_type[o['type']] += 1
    for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")
    for o in osm_only[:20]:
        print(f"  {o['name']:45s} {o['type']:12s} ({o['lat']:.4f}, {o['lon']:.4f})")

    print(f"\n## Bible-Only — No OSM Match (sample 20 of {len(bible_only)})")
    for b in bible_only[:20]:
        print(f"  {b['name']:45s} {b.get('type','?'):12s}")
    if len(bible_only) > 20:
        print(f"  ... and {len(bible_only) - 20} more")

    # ========================================
    # Apply
    # ========================================
    if not do_apply:
        print(f"\n--- DRY RUN complete. Run with --apply to make changes. ---")
        # Save report
        report = {
            "state": state,
            "osm_count": len(osm_features),
            "bible_count": len(bible),
            "single_matches": len(single_matches),
            "multi_matches": len(multi_matches),
            "osm_only": len(osm_only),
            "bible_only": len(bible_only),
            "bible_only_names": [b['name'] for b in bible_only],
            "osm_only_sample": [{"name": o['name'], "type": o['type']} for o in osm_only[:50]],
            "duplicate_groups": [
                {"osm_name": osm['name'], "bible_names": [bible_by_id[bid]['name'] for bid in bids if bid in bible_by_id]}
                for osm, bids in multi_matches
            ],
        }
        report_path = f".claude/states/{state.lower()}/osm_migration_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved: {report_path}")
        return

    print(f"\n{'=' * 60}")
    print(f"APPLYING CHANGES...")
    print(f"{'=' * 60}")

    # --- Phase 1: Update 1:1 matches (coordinates + OSM ID) ---
    print(f"\n[1] Updating {len(single_matches)} matched entries...")
    updated = 0
    for osm, bible_id in single_matches:
        try:
            supabase.table("water_bodies").update({
                "coordinates": f"POINT({osm['lon']} {osm['lat']})",
                "osm_id": osm['osm_id'],
                "osm_type": osm['osm_type'],
                "coord_source": "osm",
            }).eq("id", bible_id).execute()
            updated += 1

            # Add OSM name as alias if not already present
            osm_lower = osm['name'].lower().strip()
            if osm_lower not in alias_to_wb:
                try:
                    supabase.table("water_body_aliases").insert({
                        "water_body_id": bible_id,
                        "alias": osm['name'],
                        "source": "osm",
                        "is_primary": False,
                    }).execute()
                except:
                    pass  # duplicate alias
        except Exception as e:
            print(f"  Error updating {bible_by_id.get(bible_id, {}).get('name', '?')}: {e}")

    print(f"  Updated: {updated}")

    # --- Phase 2: Merge duplicates ---
    print(f"\n[2] Merging {len(multi_matches)} duplicate groups...")
    merged = 0
    for osm, bible_ids in multi_matches:
        # Pick survivor (most FK references)
        fk_counts = {bid: count_fks(bid) for bid in bible_ids}
        survivor_id = max(fk_counts, key=fk_counts.get)
        losers = [bid for bid in bible_ids if bid != survivor_id]

        # Update survivor with OSM data
        try:
            supabase.table("water_bodies").update({
                "coordinates": f"POINT({osm['lon']} {osm['lat']})",
                "osm_id": osm['osm_id'],
                "osm_type": osm['osm_type'],
                "coord_source": "osm",
            }).eq("id", survivor_id).execute()
        except Exception as e:
            print(f"  Error updating survivor {bible_by_id.get(survivor_id, {}).get('name', '?')}: {e}")
            continue

        # Reassign FKs from losers to survivor
        fk_tables = ['stocking_events', 'conditions', 'weather_forecasts',
                      'ice_reports', 'water_body_species', 'user_favorites',
                      'waypoints', 'notes', 'photos']

        for loser_id in losers:
            for table in fk_tables:
                try:
                    supabase.table(table).update({
                        "water_body_id": survivor_id
                    }).eq("water_body_id", loser_id).execute()
                except:
                    pass  # unique constraint or table doesn't exist

            # Move aliases
            for alias in wb_to_aliases.get(loser_id, []):
                try:
                    supabase.table("water_body_aliases").update({
                        "water_body_id": survivor_id
                    }).eq("water_body_id", loser_id).eq("alias", alias).execute()
                except:
                    pass

            # Move data_source_links
            try:
                supabase.table("data_source_links").update({
                    "water_body_id": survivor_id
                }).eq("water_body_id", loser_id).execute()
            except:
                pass

            # Soft-delete loser
            try:
                supabase.table("water_bodies").update({
                    "status": "merged",
                    "parent_id": survivor_id,
                }).eq("id", loser_id).execute()
            except Exception as e:
                print(f"  Error merging {bible_by_id.get(loser_id, {}).get('name', '?')}: {e}")

        merged += 1

        # Add OSM name as alias
        try:
            supabase.table("water_body_aliases").insert({
                "water_body_id": survivor_id,
                "alias": osm['name'],
                "source": "osm",
                "is_primary": False,
            }).execute()
        except:
            pass

    print(f"  Merged: {merged} groups")

    # --- Phase 3: Insert new OSM-only waters ---
    INSERT_TYPES = {'lake', 'reservoir', 'pond', 'river'}
    insertable = [o for o in osm_only if o['type'] in INSERT_TYPES]
    if skip_insert:
        print(f"\n[3] Skipping {len(insertable)} new water insertions (--no-insert)")
        inserted = 0
    else:
        print(f"\n[3] Inserting {len(insertable)} new waters (lakes/reservoirs/ponds/rivers only, skipping {len(osm_only) - len(insertable)} creeks/streams)...")
    inserted = 0
    for osm in ([] if skip_insert else insertable):
        wtype = osm['type']
        try:
            result = supabase.table("water_bodies").insert({
                "name": osm['name'],
                "state": state,
                "type": wtype,
                "coordinates": f"POINT({osm['lon']} {osm['lat']})",
                "osm_id": osm['osm_id'],
                "osm_type": osm['osm_type'],
                "coord_source": "osm",
                "has_stocking": False,
                "has_flow_data": wtype in ('river', 'creek', 'stream'),
                "has_level_data": wtype in ('lake', 'reservoir', 'pond'),
                "status": "active",
            }).execute()

            if result.data:
                wb_id = result.data[0]["id"]
                # Add primary alias
                try:
                    supabase.table("water_body_aliases").insert({
                        "water_body_id": wb_id,
                        "alias": osm['name'],
                        "source": "osm",
                        "is_primary": True,
                    }).execute()
                except:
                    pass
                inserted += 1
        except Exception as e:
            if 'duplicate' not in str(e).lower() and '23505' not in str(e):
                print(f"  Error inserting {osm['name']}: {e}")

    print(f"  Inserted: {inserted}")

    # --- Final count ---
    print(f"\n{'=' * 60}")
    print(f"MIGRATION COMPLETE — {state}")
    print(f"{'=' * 60}")
    wb_count = supabase.table("water_bodies").select("id", count="exact").eq("state", state).neq("status", "merged").execute()
    print(f"  Active water bodies: {wb_count.count}")
    print(f"  Updated: {updated}")
    print(f"  Merged: {merged} groups")
    print(f"  New from OSM: {inserted}")


if __name__ == '__main__':
    migrate()
