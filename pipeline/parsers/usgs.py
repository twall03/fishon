"""USGS Water Services — fetch real-time flow, level, and temperature data."""

from dataclasses import dataclass
from datetime import datetime, timezone
import requests


@dataclass
class Condition:
    gauge_id: str
    flow_cfs: float = None
    level_ft: float = None
    temp_f: float = None
    timestamp: str = None


# USGS parameter codes
PARAM_DISCHARGE = "00060"  # Discharge (CFS)
PARAM_GAGE_HEIGHT = "00065"  # Gauge height (ft)
PARAM_TEMPERATURE = "00010"  # Water temperature (°C)


def fetch_conditions(gauge_ids: list[str]) -> list[Condition]:
    """Query USGS for latest instantaneous values on given gauges."""
    if not gauge_ids:
        return []

    # Strip "USGS-" prefix for API
    site_nums = [g.replace("USGS-", "") for g in gauge_ids]

    # Batch in groups of 100 (USGS limit)
    all_conditions = []
    for i in range(0, len(site_nums), 100):
        batch = site_nums[i:i+100]
        sites = ",".join(batch)

        url = (
            f"https://waterservices.usgs.gov/nwis/iv/"
            f"?format=json&sites={sites}"
            f"&parameterCd={PARAM_DISCHARGE},{PARAM_GAGE_HEIGHT},{PARAM_TEMPERATURE}"
            f"&siteStatus=active"
        )

        try:
            resp = requests.get(url, timeout=30, headers={
                "User-Agent": "FishOn/1.0 (fishing data aggregator)"
            })
            if resp.status_code != 200:
                continue

            data = resp.json()
            ts_list = data.get("value", {}).get("timeSeries", [])

            # Group by site
            site_data = {}
            for ts in ts_list:
                site_code = ts["sourceInfo"]["siteCode"][0]["value"]
                param_code = ts["variable"]["variableCode"][0]["value"]
                values = ts.get("values", [{}])[0].get("value", [])
                if not values:
                    continue
                latest = values[-1]
                val = float(latest["value"]) if latest["value"] != "-999999" else None

                if site_code not in site_data:
                    site_data[site_code] = {
                        "gauge_id": f"USGS-{site_code}",
                        "timestamp": latest["dateTime"]
                    }

                if param_code == PARAM_DISCHARGE:
                    site_data[site_code]["flow_cfs"] = val
                elif param_code == PARAM_GAGE_HEIGHT:
                    site_data[site_code]["level_ft"] = val
                elif param_code == PARAM_TEMPERATURE and val is not None:
                    site_data[site_code]["temp_f"] = round(val * 9/5 + 32, 1)  # C to F

            for sd in site_data.values():
                all_conditions.append(Condition(**sd))

        except Exception as e:
            print(f"  USGS batch error: {e}")
            continue

    return all_conditions
