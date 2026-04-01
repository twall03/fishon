"""NOAA NWS Weather — fetch 7-day forecasts for water body coordinates."""

import time
from dataclasses import dataclass
import requests


@dataclass
class WeatherForecast:
    forecast_date: str  # YYYY-MM-DD
    temp_high_f: int = None
    temp_low_f: int = None
    wind_mph: int = None
    precip_chance: float = None
    summary: str = None


HEADERS = {
    "User-Agent": "FishOn/1.0 (fishing data aggregator; contact@fishon.app)",
    "Accept": "application/json"
}


def fetch_forecast(lat: float, lon: float) -> list[WeatherForecast]:
    """Fetch 7-day forecast from NOAA for given coordinates."""
    # Step 1: Get grid point
    points_url = f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}"
    try:
        resp = requests.get(points_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        forecast_url = resp.json()["properties"]["forecast"]
    except Exception:
        return []

    # Step 2: Get forecast
    time.sleep(0.2)  # be nice to NOAA
    try:
        resp = requests.get(forecast_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        periods = resp.json()["properties"]["periods"]
    except Exception:
        return []

    # Step 3: Parse into day forecasts
    # NOAA returns 12-hour periods (day/night). Combine into daily.
    daily = {}
    for p in periods:
        date_str = p["startTime"][:10]  # YYYY-MM-DD
        if date_str not in daily:
            daily[date_str] = WeatherForecast(forecast_date=date_str)

        f = daily[date_str]
        if p["isDaytime"]:
            f.temp_high_f = p["temperature"]
            f.summary = p["shortForecast"]
            wind_str = p.get("windSpeed", "")
            if wind_str:
                # Parse "10 mph" or "10 to 15 mph"
                parts = wind_str.replace(" mph", "").split(" to ")
                try:
                    f.wind_mph = int(parts[-1])
                except (ValueError, IndexError):
                    pass
        else:
            f.temp_low_f = p["temperature"]

        # Precipitation
        pop = p.get("probabilityOfPrecipitation", {}).get("value")
        if pop is not None:
            current = f.precip_chance or 0
            f.precip_chance = max(current, pop / 100.0)

    return list(daily.values())[:7]  # Max 7 days
