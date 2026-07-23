"""FastAPI backend — Will Your Drug Succeed in the Clinic?"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import os
import time
import math

from agents import run_pipeline
from logger import log_prediction
from visits import log_visit, get_visits_summary

app = FastAPI(title="Drug Success Predictor", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_client_ip(request: Request) -> str:
    """Extract real client IP from proxy headers or direct connection."""
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip:
        ip = request.headers.get("x-real-ip", "").strip()
    if not ip:
        ip = request.client.host if request.client else "unknown"
    return ip


"""FastAPI backend — Will Your Drug Succeed in the Clinic?"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import os
import time
import math
import json

from agents import run_pipeline
from logger import log_prediction
from visits import log_visit, get_visits_summary

app = FastAPI(title="Drug Success Predictor", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_client_ip(request: Request) -> str:
    """Extract real client IP from proxy headers or direct connection."""
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip:
        ip = request.headers.get("x-real-ip", "").strip()
    if not ip:
        ip = request.client.host if request.client else "unknown"
    return ip


KEYS_FILE = os.path.join(os.path.dirname(__file__), "..", "keys.json")

# Dynamic key-specific sliding window tracking
_key_usage_timestamps = {}  # { "api_key": [timestamp1, timestamp2, ...] }

import asyncio

# Concurrency Semaphore (max 100 concurrent pipeline runs across all API keys)
CONCURRENCY_LIMIT = 100
_concurrency_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

_evaluating_count = 0
_queued_count = 0


def _authenticate_and_rate_limit(request: Request) -> dict:
    """Authenticate request using X-API-Key header or query parameter.

    Returns key configuration dict if successful, otherwise raises HTTPException.
    """
    api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
    if not api_key:
        raise HTTPException(
            401,
            "API Key is required. Please provide a valid X-API-Key header or api_key query parameter."
        )

    if not os.path.exists(KEYS_FILE):
        raise HTTPException(500, "API Keys storage not found.")

    try:
        with open(KEYS_FILE, "r") as f:
            keys = json.load(f)
    except Exception as e:
        raise HTTPException(500, f"Error reading API Keys storage: {e}")

    if api_key not in keys:
        raise HTTPException(403, "Invalid API Key. Please verify your credentials.")

    key_info = keys[api_key]
    owner = key_info.get("owner", "Unknown")
    rate_limit = key_info.get("rate_limit", 0)  # default to 0 (no usage allowed)
    rate_window = key_info.get("rate_window", 3600)

    # Check rate limit
    if rate_limit == 0:
        raise HTTPException(403, f"API Key for {owner} is deactivated or has a zero usage limit.")

    if rate_limit > 0:
        now = time.time()
        cutoff = now - rate_window

        # Initialize list of timestamps if not present
        if api_key not in _key_usage_timestamps:
            _key_usage_timestamps[api_key] = []

        timestamps = _key_usage_timestamps[api_key]
        # Prune old timestamps
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)

        if len(timestamps) >= rate_limit:
            oldest = timestamps[0]
            reset_in = math.ceil(oldest + rate_window - now)
            minutes = math.ceil(reset_in / 60)
            raise HTTPException(
                429,
                f"API Key limit of {rate_limit} predictions per hour has been reached. "
                f"More predictions will be available in {minutes} minute{'s' if minutes != 1 else ''}."
            )

    return {
        "key": api_key,
        "owner": owner,
        "rate_limit": rate_limit,
        "rate_window": rate_window
    }


def _record_key_usage(api_key: str, rate_limit: int):
    """Record a successful usage of the API Key."""
    if rate_limit > 0:
        if api_key not in _key_usage_timestamps:
            _key_usage_timestamps[api_key] = []
        _key_usage_timestamps[api_key].append(time.time())


class AnalyzeRequest(BaseModel):
    smiles: str
    target: str
    indication: str
    auxiliary: str = ""
    web_search: bool = False


@app.get("/api/health")
def health():
    return {"status": "ok"}


STATS_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
STATS_LOG_FILE = os.path.join(STATS_LOG_DIR, "api_key_stats.jsonl")


def _log_api_key_stats(api_key: str, smiles: str, target: str, indication: str):
    """Log prediction details for API Key statistics."""
    from datetime import datetime
    os.makedirs(STATS_LOG_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "api_key": api_key,
        "smiles": smiles.strip(),
        "target": target.strip(),
        "indication": indication.strip()
    }
    with open(STATS_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _get_api_key_stats(api_key: str) -> dict:
    """Read stats log file and compute metrics for a specific API Key."""
    total_predictions = 0
    unique_smiles = set()
    unique_targets = set()
    unique_indications = set()
    by_indication = {}
    by_target = {}

    if os.path.exists(STATS_LOG_FILE):
        try:
            with open(STATS_LOG_FILE, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("api_key") == api_key:
                            total_predictions += 1

                            smiles = entry.get("smiles", "").strip()
                            if smiles:
                                unique_smiles.add(smiles)

                            target = entry.get("target", "").strip()
                            if target:
                                unique_targets.add(target)
                                by_target[target] = by_target.get(target, 0) + 1

                            indication = entry.get("indication", "").strip()
                            if indication:
                                unique_indications.add(indication)
                                by_indication[indication] = by_indication.get(indication, 0) + 1
                    except Exception:
                        pass
        except Exception:
            pass

    return {
        "total_predictions": total_predictions,
        "unique_molecules": len(unique_smiles),
        "unique_targets": len(unique_targets),
        "unique_indications": len(unique_indications),
        "predictions_per_indication": by_indication,
        "predictions_per_target": by_target
    }


@app.get("/api/usage")
def get_usage(request: Request):
    api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
    if not api_key:
        raise HTTPException(401, "API Key is required")

    if not os.path.exists(KEYS_FILE):
        raise HTTPException(500, "API Keys storage not found.")

    try:
        with open(KEYS_FILE, "r") as f:
            keys = json.load(f)
    except Exception as e:
        raise HTTPException(500, f"Error reading API Keys storage: {e}")

    if api_key not in keys:
        raise HTTPException(403, "Invalid API Key")

    key_info = keys[api_key]
    owner = key_info.get("owner", "Unknown")
    rate_limit = key_info.get("rate_limit", 0)
    rate_window = key_info.get("rate_window", 3600)

    # Calculate active usage
    usage_count = 0
    if rate_limit > 0:
        now = time.time()
        cutoff = now - rate_window
        timestamps = _key_usage_timestamps.get(api_key, [])
        # Count timestamps within window
        usage_count = sum(1 for ts in timestamps if ts >= cutoff)
        remaining = max(0, rate_limit - usage_count)
    else:
        # Unlimited usage
        remaining = "unlimited"

    # Get cumulative stats
    stats = _get_api_key_stats(api_key)

    return {
        "valid": True,
        "owner": owner,
        "rate_limit": rate_limit,
        "usage": usage_count,
        "remaining": remaining,
        "window": rate_window,
        "evaluating_now": _evaluating_count,
        "queued_now": _queued_count,
        "stats": stats
    }


@app.get("/api/visits")
def visits():
    return get_visits_summary()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest, request: Request):
    global _evaluating_count, _queued_count
    # Authenticate and rate limit via API Key
    key_info = _authenticate_and_rate_limit(request)

    ip = _get_client_ip(request)

    if not req.smiles.strip():
        raise HTTPException(400, "SMILES is required")
    if not req.target.strip():
        raise HTTPException(400, "Target is required")
    if not req.indication.strip():
        raise HTTPException(400, "Indication is required")

    # Tracking queued and evaluating states with cancellation safety
    _queued_count += 1
    queued_decremented = False
    try:
        async with _concurrency_semaphore:
            _queued_count -= 1
            queued_decremented = True
            _evaluating_count += 1
            try:
                # Run the CPU/network-bound pipeline in a threadpool
                result = await asyncio.to_thread(
                    run_pipeline,
                    req.smiles.strip(),
                    req.target.strip(),
                    req.indication.strip(),
                    req.auxiliary.strip(),
                    web_search=req.web_search,
                )
            finally:
                _evaluating_count -= 1
    finally:
        if not queued_decremented:
            _queued_count -= 1

    # Record successful usage
    _record_key_usage(key_info["key"], key_info["rate_limit"])
    _log_api_key_stats(key_info["key"], req.smiles, req.target, req.indication)

    ua = request.headers.get("user-agent", "")
    log_visit(ip, f"/api/analyze?owner={key_info['owner']}", ua)
    log_prediction(result)
    return result


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prediction Dashboard</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0a0e17; color: #e0e6ed; }
  .header { padding: 20px 30px; background: #111827;
            border-bottom: 1px solid #1e293b; display:flex; align-items:center; gap:16px; }
  .header h1 { font-size: 1.3rem; color: #4a9eff; }
  .header a { color: #64748b; text-decoration: none; font-size: 0.85rem; }
  .header a:hover { color: #4a9eff; }
  .stats { display:flex; gap:16px; padding:20px 30px; flex-wrap:wrap; }
  .stat-card { background:#111827; border:1px solid #1e293b; border-radius:10px;
               padding:16px 24px; min-width:160px; }
  .stat-card .num { font-size:2rem; font-weight:700; color:#4a9eff; }
  .stat-card .lbl { font-size:0.8rem; color:#64748b; margin-top:4px; }
  #map { height: 50vh; margin: 0 30px; border-radius: 10px; border:1px solid #1e293b; }
  .tables { display:flex; gap:20px; padding:20px 30px; flex-wrap:wrap; }
  .tbl { background:#111827; border:1px solid #1e293b; border-radius:10px;
         padding:16px; flex:1; min-width:280px; max-height:300px; overflow-y:auto; }
  .tbl h3 { font-size:0.9rem; color:#4a9eff; margin-bottom:10px; }
  .tbl table { width:100%; border-collapse:collapse; font-size:0.8rem; }
  .tbl td, .tbl th { padding:6px 10px; border-bottom:1px solid #1e293b; text-align:left; }
  .tbl th { color:#64748b; font-weight:600; }
  .leaflet-popup-content-wrapper { background:#1e293b; color:#e0e6ed; border-radius:8px; }
  .leaflet-popup-tip { background:#1e293b; }
  .leaflet-popup-content { font-size:0.85rem; }
</style>
</head>
<body>
<div class="header">
  <h1>Prediction Dashboard</h1>
  <a href="/">&larr; Back to App</a>
  <span id="refresh-info" style="margin-left:auto;font-size:0.75rem;color:#64748b;"></span>
</div>
<div class="stats" id="stats"></div>
<div id="map"></div>
<div class="tables" id="tables"></div>

<script>
const map = L.map('map').setView([30, 0], 2);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  maxZoom: 18
}).addTo(map);

let markers = [];

async function load() {
  const res = await fetch('/api/visits');
  const d = await res.json();

  document.getElementById('stats').innerHTML = `
    <div class="stat-card"><div class="num">${d.total}</div><div class="lbl">Total Predictions</div></div>
    <div class="stat-card"><div class="num">${d.unique_ips}</div><div class="lbl">Unique Users (IPs)</div></div>
    <div class="stat-card"><div class="num">${d.locations.length}</div><div class="lbl">Locations</div></div>
    <div class="stat-card"><div class="num">${Object.keys(d.by_country).length}</div><div class="lbl">Countries</div></div>
  `;

  markers.forEach(m => map.removeLayer(m));
  markers = [];
  d.locations.forEach(loc => {
    if (loc.lat === 0 && loc.lon === 0) return;
    const radius = Math.max(6, Math.min(30, Math.sqrt(loc.count) * 6));
    const m = L.circleMarker([loc.lat, loc.lon], {
      radius, fillColor: '#4a9eff', color: '#4a9eff',
      weight: 1, opacity: 0.8, fillOpacity: 0.5
    }).addTo(map);
    m.bindPopup(`<b>${loc.city}, ${loc.country}</b><br>${loc.count} prediction${loc.count>1?'s':''}`);
    markers.push(m);
  });

  // Country table
  const countries = Object.entries(d.by_country).sort((a,b) => b[1]-a[1]);
  const countryRows = countries.map(([c,n]) => `<tr><td>${c}</td><td>${n}</td></tr>`).join('');

  // Recent visits table
  const recentRows = d.recent.map(v =>
    `<tr><td>${v.timestamp.replace('T',' ').slice(0,19)}</td><td>${v.ip}</td><td>${v.city}, ${v.country}</td><td>${v.path}</td></tr>`
  ).join('');

  document.getElementById('tables').innerHTML = `
    <div class="tbl"><h3>By Country</h3><table><th>Country</th><th>Predictions</th>${countryRows}</table></div>
    <div class="tbl"><h3>Recent Predictions</h3><table><th>Time</th><th>IP</th><th>Location</th><th>Path</th>${recentRows}</table></div>
  `;
  document.getElementById('refresh-info').textContent = 'Last refresh: ' + new Date().toLocaleTimeString();
}

load();
setInterval(load, 30000);
</script>
</body>
</html>
"""


# Serve frontend static build in production
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
