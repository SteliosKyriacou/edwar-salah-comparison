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


# --- Global rate limiter: 100 predictions per hour ---
RATE_LIMIT = 100
RATE_WINDOW = 3600  # seconds
_prediction_timestamps: list = []


def _check_rate_limit():
    """Enforce global rate limit. Raises HTTPException if exceeded."""
    now = time.time()
    cutoff = now - RATE_WINDOW
    # Prune old timestamps
    while _prediction_timestamps and _prediction_timestamps[0] < cutoff:
        _prediction_timestamps.pop(0)
    if len(_prediction_timestamps) >= RATE_LIMIT:
        oldest = _prediction_timestamps[0]
        reset_in = math.ceil(oldest + RATE_WINDOW - now)
        minutes = math.ceil(reset_in / 60)
        raise HTTPException(
            429,
            f"We've reached the limit of {RATE_LIMIT} predictions per hour. "
            f"Predictions will be available again in {minutes} minute{'s' if minutes != 1 else ''}. "
            f"Thank you for your patience!",
        )
    _prediction_timestamps.append(now)


class AnalyzeRequest(BaseModel):
    smiles: str
    target: str
    indication: str
    auxiliary: str = ""


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/visits")
def visits():
    return get_visits_summary()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest, request: Request):
    _check_rate_limit()
    if not req.smiles.strip():
        raise HTTPException(400, "SMILES is required")
    if not req.target.strip():
        raise HTTPException(400, "Target is required")
    if not req.indication.strip():
        raise HTTPException(400, "Indication is required")

    try:
        result = run_pipeline(
            req.smiles.strip(),
            req.target.strip(),
            req.indication.strip(),
            req.auxiliary.strip(),
        )
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {e}")

    ip = _get_client_ip(request)
    ua = request.headers.get("user-agent", "")
    log_visit(ip, "/api/analyze", ua)
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
