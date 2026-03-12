"""Visit logger — records IP, geo-location, timestamp, and path."""

import json
import os
import urllib.request
from datetime import datetime
from collections import Counter

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
VISITS_FILE = os.path.join(LOG_DIR, "visits.jsonl")

# In-memory cache so we don't re-query the same IP
_geo_cache: dict = {}


def _geolocate(ip: str) -> dict:
    """Look up IP geolocation via ip-api.com (free, no key needed, 45 rpm)."""
    if ip in _geo_cache:
        return _geo_cache[ip]

    fallback = {"country": "Unknown", "city": "Unknown", "lat": 0, "lon": 0}

    # Skip private / loopback IPs
    if ip.startswith(("127.", "10.", "192.168.", "172.")) or ip == "::1":
        fallback["city"] = "Local"
        fallback["country"] = "Local"
        _geo_cache[ip] = fallback
        return fallback

    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon"
        req = urllib.request.Request(url, headers={"User-Agent": "DrugPredictor/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
        if data.get("status") == "success":
            result = {
                "country": data.get("country", "Unknown"),
                "city": data.get("city", "Unknown"),
                "lat": data.get("lat", 0),
                "lon": data.get("lon", 0),
            }
            _geo_cache[ip] = result
            return result
    except Exception:
        pass

    _geo_cache[ip] = fallback
    return fallback


def log_visit(ip: str, path: str, user_agent: str = ""):
    """Append a visit entry."""
    os.makedirs(LOG_DIR, exist_ok=True)
    geo = _geolocate(ip)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "ip": ip,
        "path": path,
        "user_agent": user_agent,
        **geo,
    }
    with open(VISITS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_visits_summary() -> dict:
    """Read visits log and return summary for the dashboard."""
    if not os.path.isfile(VISITS_FILE):
        return {"total": 0, "locations": [], "by_country": {}, "by_path": {}, "recent": []}

    visits = []
    with open(VISITS_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                visits.append(json.loads(line))

    # Aggregate locations for the map (group by lat/lon)
    loc_counts: dict = {}
    for v in visits:
        key = (round(v.get("lat", 0), 2), round(v.get("lon", 0), 2))
        if key not in loc_counts:
            loc_counts[key] = {
                "lat": v.get("lat", 0),
                "lon": v.get("lon", 0),
                "city": v.get("city", "Unknown"),
                "country": v.get("country", "Unknown"),
                "count": 0,
            }
        loc_counts[key]["count"] += 1

    by_country = dict(Counter(v.get("country", "Unknown") for v in visits))
    by_path = dict(Counter(v.get("path", "/") for v in visits))
    unique_ips = len(set(v.get("ip", "") for v in visits))

    return {
        "total": len(visits),
        "unique_ips": unique_ips,
        "locations": list(loc_counts.values()),
        "by_country": by_country,
        "by_path": by_path,
        "recent": visits[-20:][::-1],  # last 20, newest first
    }
