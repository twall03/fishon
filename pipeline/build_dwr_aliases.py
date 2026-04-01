"""
build_dwr_aliases.py — Build DWR stocking name → OSM bible alias mappings for Utah.

Fetches all unique water body names from the Utah DWR stocking report (2024–2026),
expands DWR abbreviations, matches against the water_bodies bible, then inserts
aliases into water_body_aliases so stocking events can be matched.

Usage:
    python -m pipeline.build_dwr_aliases            # dry-run, no inserts
    python -m pipeline.build_dwr_aliases --insert   # insert matched aliases
"""

import re
import sys
import unicodedata
import requests
from bs4 import BeautifulSoup
from pipeline.config import supabase

# ---------------------------------------------------------------------------
# Abbreviation expansion table — DWR → standard English
# ---------------------------------------------------------------------------
ABBREV = {
    # Water body type suffixes
    r'\bRES\b': 'Reservoir',
    r'\bL\b': 'Lake',
    r'\bR\b': 'River',
    r'\bCR\b': 'Creek',
    r'\bP\b': 'Pond',
    r'\bSP\b': 'Springs',
    r'\bSPRINGS\b': 'Springs',
    r'\bFK\b': 'Fork',
    r'\bCYN\b': 'Canyon',
    r'\bMTN\b': 'Mountain',
    r'\bMT\b': 'Mount',
    # Directional prefixes / qualifiers
    r'\bN\b': 'North',
    r'\bS\b': 'South',
    r'\bE\b': 'East',
    r'\bW\b': 'West',
    r'\bN FK\b': 'North Fork',
    r'\bS FK\b': 'South Fork',
    r'\bE FK\b': 'East Fork',
    r'\bW FK\b': 'West Fork',
    r'\bLWR\b': 'Lower',
    r'\bUPR\b': 'Upper',
    # Misc
    r'\bSLC\b': 'Salt Lake City',
    r'\bCNTY\b': 'County',
    r'\bCOMM\b': 'Community',
    r'\bSTK\b': 'Stocking',
    r'\bNBS\b': '',   # "North Book Cliffs" tag — strip it
    r'\bBTS\b': '',   # Basin tag — strip
    r'\bBTN\b': '',
    r'\bTLM\b': '',
    r'\bEBS\b': '',
    r'\bEMW\b': '',
    r'\bNCL\b': '',
    r'\bGT\b': '',
    r'\bRC\b': '',
    r'\bLF\b': '',
    r'\bSCB\b': '',
    r'\bFL\b': '',
}

# Patterns that are alphanumeric codes like "GR-104", "X- 22", "BR-35"
# These are wilderness lake codes — OSM may have them verbatim or not at all.
CODE_PATTERN = re.compile(
    r'^(G|GR|BR|DG|DF|LF|RC|U|W|X|WR|A|Z|BT|P|Y)-?\s*\d+$', re.IGNORECASE
)


def normalize(s: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation for comparison."""
    s = unicodedata.normalize('NFKD', s)
    s = s.lower().strip()
    s = re.sub(r'[.,\'"`]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s


def expand_dwr_name(dwr: str) -> str:
    """
    Expand DWR abbreviations into a readable form suitable for bible matching.

    e.g.  "DEER CR RES"    → "Deer Creek Reservoir"
          "UTAH L"         → "Utah Lake"
          "PROVO R"        → "Provo River"
          "STRAWBERRY RES" → "Strawberry Reservoir"
    """
    # Work on the all-caps version for expansion so word boundaries are clean.
    name = dwr.strip().upper()

    # Strip trailing alphanumeric catalog codes like "BR-10", "GR-104", "X-22", "A-17",
    # "W66", "D47" — single or double letter prefix followed by digits.
    # These appear after the meaningful name: "BEAVER L BR-10" → "BEAVER L"
    name = re.sub(r'\s+[A-Z]{1,4}-?\s*\d+$', '', name)

    # Strip trailing region/basin tags that have no geographic meaning in OSM
    STRIP_TAGS = {'NBS', 'BTS', 'BTN', 'TLM', 'EBS', 'EMW', 'NCL', 'GT', 'SCB', 'FL'}
    name = re.sub(
        r'\s+([A-Z]{2,4})$',
        lambda m: '' if m.group(1) in STRIP_TAGS else m.group(),
        name
    )

    # Expand multi-word abbreviations BEFORE single-letter ones to avoid
    # partial matches (e.g. "N FK" must expand before "N" does).
    MULTI_ABBREV = [
        (r'(?<!\w)N\s+FK(?!\w)', 'NORTH FORK'),
        (r'(?<!\w)S\s+FK(?!\w)', 'SOUTH FORK'),
        (r'(?<!\w)E\s+FK(?!\w)', 'EAST FORK'),
        (r'(?<!\w)W\s+FK(?!\w)', 'WEST FORK'),
    ]
    for pattern, replacement in MULTI_ABBREV:
        name = re.sub(pattern, replacement, name)

    # Expand single-word abbreviations. Use a space-or-start/end boundary so
    # that possessive 'S (e.g. "AMBER'S") is not matched by the S → SOUTH rule.
    # The pattern (?:^|(?<=\s)) ... (?=\s|,|$) requires the token to be
    # surrounded by whitespace, commas, or string boundaries.
    SINGLE_ABBREV = [
        (r'(?:^|(?<=\s))RES(?=\s|,|$)', 'RESERVOIR'),
        (r'(?:^|(?<=\s))CR(?=\s|,|$)', 'CREEK'),
        (r'(?:^|(?<=\s))FK(?=\s|,|$)', 'FORK'),
        (r'(?:^|(?<=\s))SP(?=\s|,|$)', 'SPRINGS'),
        (r'(?:^|(?<=\s))CYN(?=\s|,|$)', 'CANYON'),
        (r'(?:^|(?<=\s))MTN(?=\s|,|$)', 'MOUNTAIN'),
        (r'(?:^|(?<=\s))MT(?=\s|,|$)', 'MOUNT'),
        (r'(?:^|(?<=\s))PND(?=\s|,|$)', 'POND'),
        (r'(?:^|(?<=\s))P(?=\s|,|$)', 'POND'),
        (r'(?:^|(?<=\s))L(?=\s|,|$)', 'LAKE'),
        (r'(?:^|(?<=\s))R(?=\s|,|$)', 'RIVER'),
        # Directionals — only standalone tokens, never after apostrophe
        (r'(?:^|(?<=\s))N(?=\s|,|$)', 'NORTH'),
        (r'(?:^|(?<=\s))S(?=\s|,|$)', 'SOUTH'),
        (r'(?:^|(?<=\s))E(?=\s|,|$)', 'EAST'),
        (r'(?:^|(?<=\s))W(?=\s|,|$)', 'WEST'),
        # Misc
        (r'(?:^|(?<=\s))LWR(?=\s|,|$)', 'LOWER'),
        (r'(?:^|(?<=\s))UPR(?=\s|,|$)', 'UPPER'),
        (r'(?:^|(?<=\s))SLC(?=\s|,|$)', 'SALT LAKE CITY'),
        (r'(?:^|(?<=\s))CNTY(?=\s|,|$)', 'COUNTY'),
        (r'(?:^|(?<=\s))COMM(?=\s|,|$)', 'COMMUNITY'),
    ]
    for pattern, replacement in SINGLE_ABBREV:
        name = re.sub(pattern, replacement, name)

    # Strip remaining basin tags that may now be interior (e.g. empty after stripping)
    # Apply again in case stripping tags left artifacts
    name = re.sub(
        r'\s+([A-Z]{2,4})$',
        lambda m: '' if m.group(1) in STRIP_TAGS else m.group(),
        name
    )

    # Title-case and clean whitespace
    name = name.title()
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def fetch_dwr_names(years=(2024, 2025, 2026)) -> set:
    """Fetch all unique water body names from DWR stocking pages."""
    all_names: set[str] = set()
    for year in years:
        url = (
            f'https://dwrapps.utah.gov/fishstocking/FishAjax'
            f'?y={year}&sort=stockdate&sortorder=DESC&sortspecific=ALL'
        )
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            print(f'  WARNING: could not fetch {year}: {e}')
            continue
        soup = BeautifulSoup(resp.content, 'html.parser')
        cells = soup.find_all('td', class_='watername')
        names = {c.get_text(strip=True) for c in cells}
        print(f'  {year}: {len(names)} unique names ({len(cells)} total rows)')
        all_names.update(names)
    return all_names


def load_ut_water_bodies() -> list[dict]:
    """Return all UT water bodies from the bible, paginated."""
    all_wb = []
    offset = 0
    while True:
        result = (
            supabase.table('water_bodies')
            .select('id,name')
            .eq('state', 'UT')
            .range(offset, offset + 999)
            .execute()
        )
        all_wb.extend(result.data)
        if len(result.data) < 1000:
            break
        offset += 1000
    return all_wb


def load_existing_aliases() -> set[str]:
    """Return set of existing alias_lower values (global, for dedup)."""
    existing: set[str] = set()
    offset = 0
    while True:
        result = (
            supabase.table('water_body_aliases')
            .select('alias_lower')
            .range(offset, offset + 999)
            .execute()
        )
        for row in result.data:
            existing.add(row['alias_lower'])
        if len(result.data) < 1000:
            break
        offset += 1000
    return existing


def build_bible_index(water_bodies: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    """
    Build two lookup dicts:
    1. primary_index: normalized full name → water_body_id
    2. stripped_index: normalized name with parenthetical qualifiers removed → water_body_id
       (e.g. "willard bay reservoir (blue ribbon)" → "willard bay reservoir")
       Only used when primary doesn't match.
    """
    primary_index: dict[str, str] = {}
    stripped_index: dict[str, str] = {}
    for wb in water_bodies:
        full_key = normalize(wb['name'])
        primary_index[full_key] = wb['id']

        # Build stripped version — remove anything in parentheses
        stripped_name = re.sub(r'\s*\(.*?\)', '', wb['name']).strip()
        stripped_key = normalize(stripped_name)
        # Only add to stripped_index if it differs from the full name
        # and doesn't already point to a different water body
        if stripped_key != full_key and stripped_key not in stripped_index:
            stripped_index[stripped_key] = wb['id']

    return primary_index, stripped_index


def _dedup_trailing_s(key: str) -> str:
    """
    Strip a trailing 's' from the last word to handle plural mismatches.
    e.g. "yankee meadows reservoir" → "yankee meadow reservoir"
    Only strips if the last real word (before type suffix) ends in 's'.
    """
    # Match: "yankee meadows reservoir" — last word before optional type suffix
    m = re.match(
        r'^(.*\w)(s)\s+(reservoir|lake|river|creek|pond|canyon|fork|springs|spring)$',
        key
    )
    if m:
        return m.group(1) + ' ' + m.group(3)
    return key


def try_match(
    dwr_name: str,
    primary_index: dict[str, str],
    stripped_index: dict[str, str],
) -> tuple[str | None, str, str]:
    """
    Try to match a DWR name to a bible entry.

    Returns (water_body_id | None, matched_name, match_type)
    match_types: 'exact_dwr', 'exact_expanded', 'base_match',
                 'code_verbatim', 'stripped_paren', 'plural_fix', 'unmatched'
    """
    # 1. Exact match on the raw DWR name (e.g. bible might have "UTAH L" as its name)
    key = normalize(dwr_name)
    if key in primary_index:
        return primary_index[key], dwr_name, 'exact_dwr'

    # 2. Try matching the verbatim code (e.g. "BR-44" → OSM has "BR-44")
    dwr_stripped = re.sub(r'\s+', '', dwr_name)  # "BR- 34" → "BR-34"
    code_key = normalize(dwr_stripped)
    if code_key in primary_index:
        return primary_index[code_key], dwr_stripped, 'code_verbatim'

    # 3. Expand abbreviations and try exact match
    expanded = expand_dwr_name(dwr_name)
    exp_key = normalize(expanded)
    if exp_key in primary_index:
        return primary_index[exp_key], expanded, 'exact_expanded'

    # 4. Try against stripped_index (handles "Willard Bay Reservoir (Blue Ribbon)" etc.)
    if exp_key in stripped_index:
        return stripped_index[exp_key], expanded, 'stripped_paren'

    # 5. Strip trailing qualifier words (", UPPER", ", LOWER", ", NORTH", etc.)
    #    and try again — helps "ENTERPRISE RES,UPPER" → "Enterprise Reservoir"
    base = re.sub(
        r'[,\s]+(Upper|Lower|North|South|East|West|No\.?\s*\d+|#\d+|\d+)$',
        '', expanded, flags=re.IGNORECASE
    ).strip()
    base_key = normalize(base)
    if base_key != exp_key:
        if base_key in primary_index:
            return primary_index[base_key], expanded, 'base_match'
        if base_key in stripped_index:
            return stripped_index[base_key], expanded, 'base_stripped'

    # 6. Try fixing plural mismatch on the expanded name
    plural_key = _dedup_trailing_s(exp_key)
    if plural_key != exp_key:
        if plural_key in primary_index:
            return primary_index[plural_key], expanded, 'plural_fix'
        if plural_key in stripped_index:
            return stripped_index[plural_key], expanded, 'plural_stripped'

    return None, expanded, 'unmatched'


def insert_aliases(to_insert: list[dict]) -> int:
    """Batch-insert aliases. Returns count inserted."""
    inserted = 0
    batch_size = 100
    for i in range(0, len(to_insert), batch_size):
        batch = to_insert[i: i + batch_size]
        result = supabase.table('water_body_aliases').insert(batch).execute()
        inserted += len(result.data)
    return inserted


def run(do_insert: bool = False) -> None:
    print('=== DWR Alias Builder ===')
    print()

    print('Step 1: Fetching DWR stocking names (2024–2026)...')
    dwr_names = fetch_dwr_names()
    print(f'  Total unique DWR names: {len(dwr_names)}')
    print()

    print('Step 2: Loading UT water bodies from bible...')
    water_bodies = load_ut_water_bodies()
    print(f'  Loaded {len(water_bodies)} UT water bodies')
    primary_index, stripped_index = build_bible_index(water_bodies)
    print(f'  Bible primary index entries: {len(primary_index)}')
    print(f'  Bible stripped-paren index entries: {len(stripped_index)}')
    print()

    print('Step 3: Loading existing aliases for dedup...')
    existing_aliases = load_existing_aliases()
    print(f'  Existing alias_lower values: {len(existing_aliases)}')
    print()

    print('Step 4: Matching DWR names to bible...')
    matched = []     # (dwr_name, water_body_id, expanded_name, match_type)
    unmatched = []   # dwr_name strings

    for dwr_name in sorted(dwr_names):
        wb_id, expanded, match_type = try_match(dwr_name, primary_index, stripped_index)
        if wb_id:
            matched.append((dwr_name, wb_id, expanded, match_type))
        else:
            unmatched.append((dwr_name, expanded))

    print(f'  Matched:   {len(matched)}')
    print(f'  Unmatched: {len(unmatched)}')
    print()

    # Build list of aliases to insert
    to_insert = []
    skipped_existing = 0

    for dwr_name, wb_id, expanded, match_type in matched:
        # Always add the raw DWR abbreviated form
        dwr_key = normalize(dwr_name)
        if dwr_key not in existing_aliases:
            to_insert.append({
                'water_body_id': wb_id,
                'alias': dwr_name,
                'source': 'state_dwr',
                'is_primary': False,
            })
            existing_aliases.add(dwr_key)  # prevent re-insertion within this run
        else:
            skipped_existing += 1

        # Also add the expanded form if it differs from the DWR name
        if expanded and normalize(expanded) != dwr_key:
            exp_key = normalize(expanded)
            if exp_key not in existing_aliases:
                to_insert.append({
                    'water_body_id': wb_id,
                    'alias': expanded,
                    'source': 'state_dwr',
                    'is_primary': False,
                })
                existing_aliases.add(exp_key)
            else:
                skipped_existing += 1

    print(f'Step 5: Alias insertion plan')
    print(f'  Aliases to insert:   {len(to_insert)}')
    print(f'  Skipped (existing):  {skipped_existing}')
    print()

    # --- Summary of matched entries ---
    print('=== MATCHED ENTRIES ===')
    for dwr_name, wb_id, expanded, match_type in sorted(matched):
        print(f'  [{match_type}] "{dwr_name}" → "{expanded}" ({wb_id[:8]}...)')
    print()

    # --- Summary of unmatched entries ---
    print('=== UNMATCHED ENTRIES ===')
    for dwr_name, expanded in sorted(unmatched):
        print(f'  "{dwr_name}" (expanded: "{expanded}")')
    print()

    print(f'Summary: {len(dwr_names)} DWR names | {len(matched)} matched | '
          f'{len(unmatched)} unmatched | {len(to_insert)} aliases to insert')
    print()

    if do_insert:
        if not to_insert:
            print('Nothing to insert.')
            return
        print(f'Inserting {len(to_insert)} aliases...')
        inserted = insert_aliases(to_insert)
        print(f'Inserted {inserted} aliases.')
    else:
        print('DRY RUN — pass --insert to write aliases to the database.')


if __name__ == '__main__':
    do_insert = '--insert' in sys.argv
    run(do_insert=do_insert)
