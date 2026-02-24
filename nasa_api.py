import json
import requests
from datetime import datetime, timedelta
from django.conf import settings

NASA_NEOWS_URL = "https://api.nasa.gov/neo/rest/v1/feed"


def fetch_asteroids_from_nasa():
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=7)
    params = {
        "start_date": today.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "api_key": settings.NASA_API_KEY,
    }
    response = requests.get(NASA_NEOWS_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    asteroids = []
    for date_str, neo_list in data.get("near_earth_objects", {}).items():
        for neo in neo_list:
            asteroids.append(neo)
    return asteroids


def parse_asteroid(neo):
    close_approaches = neo.get("close_approach_data", [])
    if not close_approaches:
        return None
    approach = close_approaches[0]
    miss_km = float(approach.get("miss_distance", {}).get("kilometers", 9e9))
    velocity_kms = float(approach.get("relative_velocity", {}).get("kilometers_per_second", 0))
    diam_data = neo.get("estimated_diameter", {}).get("meters", {})
    diam_min = float(diam_data.get("estimated_diameter_min", 0))
    diam_max = float(diam_data.get("estimated_diameter_max", 0))
    diam_avg = (diam_min + diam_max) / 2
    return {
        "id": neo.get("id"),
        "name": neo.get("name", "Unknown"),
        "nasa_jpl_url": neo.get("nasa_jpl_url", "#"),
        "miss_distance_km": miss_km,
        "miss_distance_lunar": float(approach.get("miss_distance", {}).get("lunar", 0)),
        "velocity_kms": velocity_kms,
        "diameter_min_m": diam_min,
        "diameter_max_m": diam_max,
        "diameter_avg_m": diam_avg,
        "is_hazardous": neo.get("is_potentially_hazardous_asteroid", False),
        "approach_date": approach.get("close_approach_date", "Unknown"),
        "approach_datetime": approach.get("close_approach_date_full", "Unknown"),
        "orbiting_body": approach.get("orbiting_body", "Earth"),
    }


def compute_threat_score(asteroid):
    MAX_DIST = 10_000_000
    miss_km = min(asteroid["miss_distance_km"], MAX_DIST)
    proximity_score = (1 - (miss_km / MAX_DIST)) * 50
    MAX_DIAM = 1000
    diam = min(asteroid["diameter_avg_m"], MAX_DIAM)
    size_score = (diam / MAX_DIAM) * 30
    hazard_bonus = 20 if asteroid["is_hazardous"] else 0
    return round(proximity_score + size_score + hazard_bonus, 2)


def get_top5_asteroids(force_refresh=False):
    cache_path = settings.CACHE_FILE
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    if not force_refresh:
        try:
            with open(cache_path, "r") as f:
                cached = json.load(f)
            if cached.get("date") == today_str:
                return cached
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass

    raw = fetch_asteroids_from_nasa()
    parsed = [parse_asteroid(neo) for neo in raw]
    parsed = [a for a in parsed if a is not None]

    for a in parsed:
        a["threat_score"] = compute_threat_score(a)

    parsed.sort(key=lambda x: x["threat_score"], reverse=True)
    top5 = parsed[:5]

    result = {
        "date": today_str,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "total_neos_scanned": len(parsed),
        "asteroids": top5,
    }

    with open(cache_path, "w") as f:
        json.dump(result, f, indent=2)

    return result
