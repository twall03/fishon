"""Shared geographic utilities — single source of truth for geo operations."""

import math
import struct

STATE_BBOXES = {
    'UT': {'xmin': -114.05, 'ymin': 36.99, 'xmax': -109.04, 'ymax': 42.00},
    'ID': {'xmin': -117.24, 'ymin': 41.99, 'xmax': -111.04, 'ymax': 49.00},
    'MT': {'xmin': -116.05, 'ymin': 44.36, 'xmax': -104.04, 'ymax': 49.00},
    'WY': {'xmin': -111.06, 'ymin': 40.99, 'xmax': -104.05, 'ymax': 45.01},
    'CO': {'xmin': -109.06, 'ymin': 36.99, 'xmax': -102.04, 'ymax': 41.00},
    'OR': {'xmin': -124.57, 'ymin': 41.99, 'xmax': -116.46, 'ymax': 46.29},
    'WA': {'xmin': -124.85, 'ymin': 45.54, 'xmax': -116.92, 'ymax': 49.00},
}

# For Overpass API (ymin, xmin, ymax, xmax tuple format)
STATE_BBOXES_TUPLE = {
    k: (v['ymin'], v['xmin'], v['ymax'], v['xmax'])
    for k, v in STATE_BBOXES.items()
}

STANDING_TYPES = {'lake', 'reservoir', 'pond'}
FLOWING_TYPES = {'river', 'creek', 'stream', 'canal'}
WATER_TYPES = STANDING_TYPES | FLOWING_TYPES


def parse_wkb(hex_str: str) -> tuple[float, float] | None:
    """Parse PostGIS WKB hex to (lat, lon). Returns None on failure."""
    if not hex_str or not isinstance(hex_str, str):
        return None
    try:
        raw = bytes.fromhex(hex_str)
        if len(raw) >= 25:
            byte_order = raw[0]
            fmt = '<' if byte_order == 1 else '>'
            lon = struct.unpack(fmt + 'd', raw[9:17])[0]
            lat = struct.unpack(fmt + 'd', raw[17:25])[0]
            if -180 <= lon <= 180 and -90 <= lat <= 90:
                return (lat, lon)
    except (ValueError, struct.error):
        pass
    return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in km between two lat/lon points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))
