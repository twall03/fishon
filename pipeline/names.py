"""Shared name normalization utilities — single source of truth for name matching."""

import re


def normalize(name: str) -> str:
    """Normalize water body name for matching."""
    n = name.lower().strip()
    n = re.sub(r'\s*\(.*?\)\s*', ' ', n)       # strip parentheticals
    n = re.sub(r',\s*.*$', '', n)                # strip comma qualifiers
    n = re.sub(r'\s*<[^>]+>\s*', ' ', n)         # strip HTML tags
    n = re.sub(r'\s+', ' ', n).strip()
    for q in [' - ', ' below ', ' above ', ' from ', ' upstream ', ' downstream ']:
        if q in n:
            n = n[:n.index(q)].strip()
    return n


def base_name(name: str) -> str:
    """Extract base name without type suffix."""
    n = normalize(name)
    for s in [' reservoir', ' lake', ' creek', ' river', ' pond', ' stream',
              ' marina', ' state park', ' canal']:
        if n.endswith(s):
            return n[:-len(s)].strip()
    return n


def name_variants(name: str) -> list[str]:
    """Generate matching variants of a water body name."""
    base = normalize(name)
    variants = [base]

    if ' - ' in name.lower():
        for p in name.lower().split(' - '):
            p = p.strip()
            if p and p not in variants:
                variants.append(p)

    suffixes = [' reservoir', ' lake', ' creek', ' river', ' pond', ' stream']
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

    for qual in [' state park', ' golf course ponds', ' golf course pond']:
        if qual in base:
            cleaned = base.replace(qual, '').strip()
            if cleaned and cleaned not in variants:
                variants.append(cleaned)

    return variants
