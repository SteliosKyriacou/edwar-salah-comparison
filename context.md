# Project Context — Drug Success Predictor / CDR Web App

This document captures everything an agent needs to continue working on this codebase. It is kept up to date intentionally; if you change behavior, update this file.

## 1. What this project is

A **multi-agent LLM pipeline** that predicts clinical trial success for small-molecule drugs, exposed via:

- A **CLI** (`src/main.py`) — batch CSV processing
- A **web app** (`web/`) — single-molecule interactive UI + REST API

The pipeline produces a **Developability Risk Score (DRS)**, formerly called CDR Score / MedChem Score — 1 (lowest risk) to 100 (highest risk).

### The four agents (LLM-powered, run via Google Gemini)

| Agent | Role | Outputs |
|---|---|---|
| **Biological-Rationalist** (Salah) | Target biology, mechanism, druggability | `bio_p1/p2/p3`, verdict ELITE/CAUTION/TERMINATE |
| **Toxi-Predictive-Toxicologist** | Safety, structural alerts, therapeutic window | `tox_p1/p2/p3`, verdict CLEAN/MANAGEABLE/NARROW/TOXIC |
| **Pharma-Clinical-Pharmacologist** | PK/PD, dose, oral bioavailability, DDI | `pk_p1/p2/p3`, verdict FAVORABLE/ADEQUATE/CHALLENGING/IMPRACTICAL |
| **MedChem-Rationalist** (Edward) | Structural critique (Pass 1) + advisory integration (Pass 2) | `chem_p1/p2/p3`, `final_p1/p2/p3`, MedChem/CDR Score |

Pipeline:
1. Bio + Toxi + Pharma + MedChem Pass 1 run **in parallel** (4 concurrent LLM calls)
2. MedChem Pass 2 integrates all advisories sequentially → `final_p1/p2/p3`
3. Server-side scoring: `TCSP = final_p1 × final_p2 × final_p3`, `Score = round(100 × (1 - √(TCSP / 0.40)))`

Agent instruction prompts live in `Agents/<agent-name>/INSTRUCTIONS.md`.

## 2. Current branch & repo state

- **Current working branch**: `v25-clean-web-no-proba` (frontend hides per-phase probability numbers; the score is the only quantitative output shown)
- **Last stable tag**: `last-stable` (on `v25-clean-web-live`)
- **Branches of interest**:
  - `main` — base
  - `v25-clean-web` — original web app
  - `v25-clean-web-live` — live deployment fixes (rate limiting, HTTPS/Caddy, IP geolocation)
  - `v25-clean-web-no-proba` — current; rebranded to CDR/DRS, probabilities removed from UI

## 3. Web app architecture

```
web/
├── backend/                  # FastAPI, Python 3.11+ (conda env: edwar-salah)
│   ├── main.py               # FastAPI app, routes, rate limit, IP exemption, dashboard HTML
│   ├── agents.py             # LLM pipeline — Gemini calls, parses JSON, computes scores
│   ├── logger.py             # Append-only prediction log (no SMILES stored)
│   ├── visits.py             # IP geolocation (via ip-api.com) + visit log + dashboard summary
│   └── molecule.py           # (helper; check before editing)
├── frontend/                 # React + Vite
│   ├── src/
│   │   ├── App.jsx           # Main layout; calibration image; disclaimer; contact footer
│   │   ├── App.css           # All styles
│   │   └── components/
│   │       ├── Header.jsx        # Title + subtitle describing CDR
│   │       ├── InputForm.jsx     # SMILES/Target/Indication/Aux + Example buttons
│   │       ├── ScoreCards.jsx    # CDR Score | Consensus | Consensus Rationale
│   │       ├── PhaseCards.jsx    # Phase 1/2/3 Rationale (no numbers)
│   │       ├── AgentCard.jsx     # Per-agent expandable panel with phase rationales
│   │       ├── StructuralFlags.jsx
│   │       ├── MoleculeViewer.jsx
│   │       └── LoadingCountdown.jsx  # 79-second timer + per-agent stages
│   ├── public/calibration.png    # Historical calibration chart (sourced from Validation/Salah_calibration.png)
│   └── vite.config.js            # Proxies /api and /dashboard to backend:8000, forwards X-Forwarded-For
├── logs/                     # Created at runtime
│   ├── predictions.jsonl     # Per-prediction scores/verdicts (no SMILES)
│   └── visits.jsonl          # IP, geo, path, timestamp, UA
├── Caddyfile                 # HTTPS reverse proxy (production)
├── start.sh                  # Foreground: starts backend (uvicorn) + frontend (vite)
├── stop.sh                   # Kills processes on :5173 and :8000
└── restart.sh                # stop.sh + start.sh in background via nohup
```

### Ports

| Port | Service | Bound to |
|---|---|---|
| 8000 | FastAPI (uvicorn) | `0.0.0.0` |
| 5173 | Vite dev server | `0.0.0.0` (was `127.0.0.1` for HTTPS-only mode) |
| 80/443 | Caddy reverse proxy → 5173 | `0.0.0.0` (when DNS+ports configured) |

External users hit **port 5173** directly OR **HTTPS via Caddy** (when DNS is correctly set up).

## 4. Running the app

```bash
# Activate the conda env
conda activate edwar-salah

# Background (persists after terminal close)
bash web/restart.sh

# Or foreground
bash web/start.sh

# Stop
bash web/stop.sh

# Logs
tail -f /tmp/web-app.log
```

`restart.sh` writes to `/tmp/web-app.log`. To inspect status:

```bash
ss -tlnp | grep -E ':5173|:8000'
curl -s http://localhost:8000/api/health
```

## 5. LLM model configuration

Located in `web/backend/agents.py`:

```python
llm = ChatGoogleGenerativeAI(model="gemini-3.1-pro-preview", temperature=0.0)
```

Change the model string, then `bash web/restart.sh`.

Requires `GOOGLE_API_KEY` in `.env` at the repo root.

## 6. Rate limiting & IP exemptions

In `web/backend/main.py`:

```python
# IPs exempt from rate limiting and logging
EXEMPT_IPS = {"136.119.133.178", "172.59.211.68", "172.59.214.44"}

# Global rate limiter
RATE_LIMIT = 100      # predictions per hour
RATE_WINDOW = 3600    # seconds
```

**To add an IP** to exemptions (no rate limit, no visit/prediction logging):

1. Edit `EXEMPT_IPS` in `web/backend/main.py` — add the IP string to the set
2. `bash web/restart.sh`

**To change the rate limit**: edit `RATE_LIMIT` (predictions allowed per `RATE_WINDOW` seconds), then restart.

When exceeded, users see a 429 with a polite countdown message:
> "We've reached the limit of 100 predictions per hour. Predictions will be available again in X minutes. Thank you for your patience!"

## 7. REST API

Base URL (external): `http://136.119.133.178:5173` (proxied to backend via Vite)
Base URL (local): `http://localhost:8000`

### `POST /api/analyze`
**Body:**
```json
{
  "smiles": "CCOC(=O)[C@H](CCC1=CC=CC=C1)N[C@@H](C)C(=O)N2[C@H]3CCC[C@H]3C[C@H]2C(=O)O",
  "target": "ACE inhibitor",
  "indication": "Cardiovascular",
  "auxiliary": ""   // optional free-text context
}
```
**Response (truncated):**
```json
{
  "overview": {
    "medchem_score": 21,          // CDR/DRS score, 1-100 (lower = lower risk)
    "tcsp": 0.2475,
    "final_p1": 0.75, "final_p2": 0.55, "final_p3": 0.60,
    "final_p1_rationale": "...", "final_p2_rationale": "...", "final_p3_rationale": "...",
    "rationale": "...",           // consensus rationale
    "metabolic_stability": "Medium",
    "toxic_fragments": "...",
    "structural_assessment": "..."
  },
  "biology": { "verdict": "ELITE", "rationale": "...", "bio_p1": ..., ... },
  "toxicology": { "verdict": "MANAGEABLE", ... },
  "pharmacology": { "verdict": "ADEQUATE", ... },
  "medchem": { "pass1": {...}, "pass2": {...} }
}
```
Typical latency: **60–80 seconds** (4 parallel LLM calls + 1 sequential integration).

### `GET /api/health`
Returns `{"status": "ok"}`.

### `GET /api/visits`
JSON summary of prediction logs (total, by country, recent visits with geo). Used by the dashboard.

### `GET /dashboard`
HTML dashboard with Leaflet world map of prediction locations, country breakdown, recent visits table. Auto-refreshes every 30s.

## 8. Logging & privacy

- **Predictions log** (`web/logs/predictions.jsonl`): scores, verdicts, probabilities, metabolic stability. **No SMILES, target, or indication stored**.
- **Visits log** (`web/logs/visits.jsonl`): IP, geo coords + city + country, path, timestamp, user-agent. Only logged on successful `/api/analyze`, not on every page load.
- **Exempt IPs**: not logged at all.
- **Geolocation**: every IP is queried via `ip-api.com` (free, no key, 45 rpm). **Never short-circuit "Local" or "Private IP" — always query the geo API.** Carrier IPs like `172.59.x.x` are public T-Mobile, not RFC1918. Past mistake: misclassified an Indian visitor as "Local".

## 9. HTTPS / DNS

Target domain: **willyourdrugsucceedinclinic.stylianoskyriacou.ai**

- **Caddy** runs as a systemd service (`systemctl status caddy`), config at `/etc/caddy/Caddyfile`. Source-of-truth Caddyfile is `web/Caddyfile`.
- Caddy reverse-proxies port 443 → `localhost:5173`. Let's Encrypt is automatic.
- **Requirements** for HTTPS to work:
  - DNS A record `willyourdrugsucceedinclinic.stylianoskyriacou.ai → 136.119.133.178` (Squarespace DNS)
  - **Delete the Squarespace forwarding rule** for that subdomain — it conflicts with A records
  - Router port forwarding for **80** and **443** to the server's LAN IP (`192.168.1.69`)
- Currently the public-facing URL is `http://136.119.133.178:5173/` because DNS/ports are not yet fully configured. To re-enable Caddy mode: set Vite back to `host: '127.0.0.1'` in `vite.config.js`, ensure ports 80/443 are forwarded, and update the contact/footer URL in `start.sh`.

## 10. Frontend layout (current)

Top → bottom:
1. **Header** — title "Will Your Drug Succeed in the Clinic?" + subtitle describing CDR + privacy banner
2. **InputForm** — SMILES, Target, Indication, Auxiliary + Example buttons (Success = Ramipril, Failure = a CNS molecule)
3. **LoadingCountdown** — 79-second timer with rotating stage labels while waiting
4. **ScoreCards** — three boxes: **CDR Score** | **Consensus** (PROCEED/OPTIMIZE/RECONSIDER) | **Consensus Rationale** (truncated, click to expand)
5. **PhaseCards** — three boxes: **Phase 1/2/3 Rationale** (text only, no probability numbers)
6. **StructuralFlags**
7. **Agent Assessments** — four expandable AgentCards (Biology, Toxicology, Pharmacology, MedChem)
8. **Calibration section** — `/calibration.png` (sourced from `Validation/Salah_calibration.png`), 630px max
9. **Disclaimer** — not investment/regulatory advice, no liability
10. **Contact footer** (fixed bottom-right) — `stelios@reneubio.com`

## 11. Common tasks

| Task | Command / location |
|---|---|
| Restart app | `bash web/restart.sh` |
| View live logs | `tail -f /tmp/web-app.log` |
| Add an exempt IP | Edit `EXEMPT_IPS` in `web/backend/main.py`, restart |
| Change rate limit | Edit `RATE_LIMIT` in `web/backend/main.py`, restart |
| Change LLM model | Edit the `model=` arg in `web/backend/agents.py`, restart |
| Update example molecules | `web/frontend/src/components/InputForm.jsx`, `EXAMPLES` const |
| Update calibration chart | Replace `web/frontend/public/calibration.png` |
| Update Caddy config | Edit `web/Caddyfile`, then `sudo cp web/Caddyfile /etc/caddy/Caddyfile && sudo systemctl restart caddy` |
| Inspect prediction history | `cat web/logs/predictions.jsonl` |
| Inspect visit history | `cat web/logs/visits.jsonl` or visit `/dashboard` |

## 12. Important behaviors / lessons learned

- **Never skip IP geolocation by IP range heuristics**. Always query the geo API. (Saved as a persistent memory: `feedback_no_local_ip_skip.md`.)
- **Vite proxy must forward `X-Forwarded-For`** — Vite doesn't do this by default; `vite.config.js` has a `configure` callback that sets it from `req.socket.remoteAddress` so the backend sees the real client IP.
- **The `172.x.x.x` range is mostly public** — only `172.16.0.0–172.31.255.255` is private. Don't broad-match `172.`.
- **Prediction logger stores no SMILES**, by design.
- **Visit logging happens only on successful `/api/analyze`**, not on every page load (moved out of middleware).
- **DNS forwarding rules and DNS A records conflict in Squarespace**. The forwarding rule must be deleted before the A record will take effect.

## 13. Repository hygiene

- Don't commit `node_modules/`, `.env`, `logs/`, `__pycache__/`.
- `Validation/` contains historical data and figures — read-only for the web app, write only when regenerating calibration.
- Test changes locally with `bash web/restart.sh` and verify both `curl http://localhost:8000/api/health` and the dashboard before claiming done.

## 14. Open / known issues

- DNS for `willyourdrugsucceedinclinic.stylianoskyriacou.ai` still being routed via Squarespace last time it was checked. Caddy is installed and configured but blocked on DNS + router port forwarding for 80/443.
- The conda env `edwar-salah` must exist locally (`conda env list`); `start.sh` references it explicitly.
- `gemini-3.1-pro-preview` is the current model — confirm via the Google AI Studio model list before changing.
