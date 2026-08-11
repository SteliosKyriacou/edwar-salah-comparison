# CLAUDE.md

Working guide for Claude Code sessions in this repo. `Agent.md` holds the product/architecture
spec and `README.md` the public documentation — read those for *what* AlphaForge is. This file
covers *how to work on it*: operational reality, conventions, and traps.

## What this is

**AlphaForge** — a multi-agent pipeline that predicts clinical trial success for small-molecule
drug candidates, then seals each prediction on an RFC 3161 cryptographic timestamp registry via
DigiCert's TSA. The trust story is the product: a prediction that cannot be verified later is
worthless, so anything touching manifests, fingerprints, or the `/verify` path deserves extra care.

## Running the app

```bash
bash web/restart.sh    # stop + start, backgrounded, logs to /tmp/web-app.log
bash web/stop.sh       # pkill uvicorn:8001 and vite
bash web/backup.sh     # archive DB/keys/config -> gs://reneu001/timestamps-database-backup/
```

- Backend: FastAPI + uvicorn on **:8001**, run from `web/venv/bin/uvicorn`.
- Frontend: Vite + React 18 on **:4003**, proxying `/api` and `/dashboard` to :8001.

**`restart.sh` prints its success banner unconditionally.** It backgrounds `start.sh` via `nohup`,
sleeps, and echoes URLs whether or not anything came up. Never report the app as running on the
strength of that banner — verify:

```bash
curl -s localhost:8001/api/health          # -> {"status":"ok"}
curl -s -o /dev/null -w '%{http_code}' localhost:4003/
tail -30 /tmp/web-app.log
```

### Environment

- Python deps live in **`web/venv`**, not the conda env `README.md` describes in its Quick Start.
  Use `web/venv/bin/python` / `web/venv/bin/pip`. The conda instructions are stale.
- Vertex AI auth is **Application Default Credentials** — no key file in the repo path.
  Overridable via `GOOGLE_CLOUD_PROJECT` (default `ai-pipeline-461818`) and
  `GOOGLE_CLOUD_LOCATION` (default `global`). `.env` at repo root is loaded and gitignored.

## Architecture map

```
Agents/<agent-name>/INSTRUCTIONS.md   System prompts — the actual scientific IP
web/backend/
  agents.py    (264 L)  Vertex/LangChain orchestration, the 5 agent calls, scoring math
  main.py     (1067 L)  REST API, SQLite, auth/rate limiting, manifest + DigiCert TSA
  web_search.py         Optional web-search enrichment
  visits.py, logger.py  Analytics
web/frontend/src/
  App.jsx               Layout + router (/, /verify, /usage)
  components/           AgentCard, PhaseCards, ScoreCards, MoleculeViewer, ...
web/logs/alphaforge_database.db   SQLite (WAL mode) — gitignored, back it up before migrations
```

Pipeline (`agents.py:run_pipeline`): four experts run **in parallel** in a `ThreadPoolExecutor`
(`run_biology`, `run_toxi`, `run_pharma`, `run_medchem_pass1`), then `run_medchem_pass2` ingests
all four advisories **sequentially** to produce consensus `Final P1/P2/P3`. Model is
`gemini-3.1-pro-preview` at `temperature=0.0` — output is meant to be reproducible; keep it there.

Scoring is **deterministic Python, never model output** (`tcsp_to_score`):

```
TCSP  = P1 * P2 * P3
Score = round(100 * (1 - sqrt(TCSP / 0.40)))     # TCSP_CEIL = 0.40; 1 = best, 100 = worst
```

If a score ever needs changing, change the formula — do not ask an agent to emit a score.

## Traps

**Prompts are read once at import.** `agents.py:29-32` calls `_load_prompt()` at module level.
Editing any `Agents/*/INSTRUCTIONS.md` has **no effect until you restart the backend**. This is the
single most common way to think a prompt change did nothing.

**`/dashboard` and `/usage` are different things.** `/dashboard` is server-rendered HTML from
`main.py:836`, proxied through Vite to the backend. `/usage` is a client-side SPA route. Both
return 200 because the SPA catches everything — a 200 proves nothing about which one is real.
`Agent.md` and the shell banners disagree about which to advertise; they mean different pages.

**The host IP is ephemeral.** This is a GCP instance whose external IP changes on stop/start.
It has already gone stale twice in committed code (`34.82.96.124` in the scripts,
`136.119.133.178` in the verification instructions in `App.jsx`). Never hardcode it:

- Shell: resolve from the metadata server, fall back to `localhost` (see `start.sh`/`restart.sh`).
- Frontend: use `window.location.origin`.

**Rate limiting is effectively off.** Every key in `keys.json` carries `rate_limit: -1`, and
`config.json` sets `concurrency_limit: 5000`. Don't assume throttling protects the Vertex quota.

**`concurrency_limit` is not the real concurrency ceiling.** It resizes the `DynamicSemaphore`,
but every prediction then reaches Vertex through `asyncio.to_thread()`, so the binding limit is
the event loop's default executor — `min(32, cpu_count + 4)`, i.e. 20 on a 16-core box. With
`concurrency_limit: 5000`, 1000 requests pass the semaphore and queue behind those threads;
measured throughput capped at ~36 predictions/min. `THREAD_POOL_SIZE`
(`ALPHAFORGE_THREAD_POOL`, default 128) now sizes that executor at startup. Each prediction
issues 5 model calls, so Vertex request rate is ~5x the prediction rate — past the thread pool,
the next wall is the Vertex per-minute quota, which returns 429s rather than queueing.

## Conventions

- Branch for changes; `main` is the default branch. Commit or push only when asked.
- Match surrounding style: backend is plain functions with `_private` helpers and no framework
  ceremony; frontend uses inline `style={{}}` objects alongside `App.css`, no CSS-in-JS library.
- `App.css` carries a real `@media print` engine for light-theme vector PDF export. Changes to
  result-view markup should be checked in print layout, not just on screen.
- SQLite runs in WAL mode with an index on `tsa_fingerprint`. Preserve both — `/verify` latency
  is a stated product guarantee.

## Known issues

Standing problems; fix on request, don't drive-by.

- **`web/keys.json` is tracked in git** and contains live API keys with owner names and an admin
  flag. It is not in `.gitignore`. This is a **deliberate decision** — keep it tracked; do not
  gitignore it or rotate the keys unless explicitly asked. (Rotation plus a history purge would be
  the fix if that call is ever revisited.)
- `web/Caddyfile` reverse-proxies `localhost:5173`, but the frontend serves on **4003**. The
  public hostname `willyourdrugsucceedinclinic.stylianoskyriacou.ai` is therefore pointed at a
  dead port under this config.
- `agents.py:34` — `ChatVertexAI` is deprecated as of LangChain 3.2.0 and removed in 4.0.0.
  Migration path is `langchain-google-genai`'s `ChatGoogleGenerativeAI`.
- `README.md` Quick Start describes a conda env that isn't what runs.
