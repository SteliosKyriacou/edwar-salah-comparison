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
import uuid
import hashlib
from datetime import datetime

from agents import run_pipeline
from deep_analysis import aggregate as deep_aggregate
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

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.json")


class DynamicSemaphore:

    def __init__(self, limit=100):
        self.limit = limit
        self.current = 0
        self.queue = []

    def resize(self, new_limit):
        self.limit = new_limit
        # Wake up as many queued requests as possible if limit increased
        while self.current < self.limit and self.queue:
            fut = self.queue.pop(0)
            if not fut.done():
                try:
                    fut.set_result(True)
                except Exception:
                    pass

    async def acquire(self):
        if self.current < self.limit:
            self.current += 1
            return True

        # Wait in line
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self.queue.append(fut)
        try:
            await fut
        except Exception:
            # If wait is cancelled, remove future from queue and reraise
            if fut in self.queue:
                self.queue.remove(fut)
            raise
        self.current += 1
        return True

    def release(self):
        self.current = max(0, self.current - 1)
        # Wake up next in line
        while self.current < self.limit and self.queue:
            fut = self.queue.pop(0)
            if not fut.done():
                try:
                    fut.set_result(True)
                    break
                except Exception:
                    pass

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()


# Load dynamic concurrency limit from file on startup
def _load_concurrency_limit():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return max(1, int(config.get("concurrency_limit", 100)))
        except Exception:
            pass
    return 100


CONCURRENCY_LIMIT = _load_concurrency_limit()
_concurrency_semaphore = DynamicSemaphore(CONCURRENCY_LIMIT)

_evaluating_count = 0
_queued_count = 0

_key_evaluating_counts = {}  # { api_key: count }
_key_queued_counts = {}      # { api_key: count }

_queue_snapshots = []  # list of { timestamp, api_key, evaluating, queued, global_evaluating, global_queued }

def _add_queue_snapshot(api_key: str):
    _queue_snapshots.append({
        "timestamp": datetime.utcnow().isoformat(),
        "api_key": api_key,
        "evaluating": _key_evaluating_counts.get(api_key, 0),
        "queued": _key_queued_counts.get(api_key, 0),
        "global_evaluating": _evaluating_count,
        "global_queued": _queued_count
    })
    # Limit to last 2000 entries to prevent memory growth
    if len(_queue_snapshots) > 2000:
        _queue_snapshots.pop(0)


# --- Deep analysis ---------------------------------------------------------
# How many simulations one deep analysis runs by default.
DEEP_DEFAULT_SIMULATIONS = 100
DEEP_MAX_SIMULATIONS = 200

# How many of those simulations may be in flight at once. Each simulation is a
# full pipeline run (5 Gemini calls) plus a DigiCert TSA round-trip, so this is
# deliberately far below the global concurrency_limit — that limit is 5000 in
# config.json and every API key has rate_limit -1, so nothing else throttles a
# deep run away from exhausting the Vertex quota.
DEEP_FANOUT = int(os.environ.get("ALPHAFORGE_DEEP_FANOUT", "10"))

# job_id -> job state. In-memory by design: a deep run is a foreground activity
# and every individual simulation is already persisted in SQLite, so the
# aggregate can be recomputed from the database if a job record is lost.
_deep_jobs = {}
DEEP_JOB_RETENTION = 20


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


class AdminKeyRequest(BaseModel):
    key: str = ""
    owner: str
    rate_limit: int = -1
    rate_window: int = 3600
    admin: bool = False


class AdminDeleteKeyRequest(BaseModel):
    key: str


class AdminConfigRequest(BaseModel):
    concurrency_limit: int


class AnalyzeRequest(BaseModel):
    smiles: str
    target: str
    indication: str
    auxiliary: str = ""
    web_search: bool = False
    mock: bool = False


class DeepAnalyzeRequest(AnalyzeRequest):
    """Deep analysis — N repeated simulations of the same molecule.

    n_simulations defaults to 100. Each simulation is a normal prediction: it is
    manifested, RFC 3161 timestamped and written to the database, so deep runs
    appear in monitoring and are individually verifiable via /verify.
    """
    n_simulations: int = DEEP_DEFAULT_SIMULATIONS


@app.get("/api/health")
def health():
    return {"status": "ok"}


import sqlite3

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
DB_FILE = os.path.join(DB_DIR, "alphaforge_database.db")


def _get_db_conn():
    """Get a thread-safe connection to the SQLite database with WAL mode enabled."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    # Enable WAL mode for excellent concurrent read/write performance
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def _init_db():
    """Initialize the SQLite database and create tables/indexes if not exist."""
    conn = _get_db_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_key_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                api_key TEXT NOT NULL,
                owner TEXT,
                smiles TEXT,
                target TEXT,
                indication TEXT,
                tsa_fingerprint TEXT,
                tsa_timestamp TEXT,
                tsa_signature_b64 TEXT,
                tsa_manifest TEXT,
                prediction_json TEXT,
                username TEXT
            );
        """)
        # Additive column migrations. CREATE TABLE IF NOT EXISTS never alters an
        # existing table, so a column added to the schema above is invisible on
        # any database created before it. /api/monitoring selects `username`, so
        # without this the Real-Time Pipeline Monitor fails with
        # "no such column: username" on every pre-existing database.
        existing = {row[1] for row in conn.execute("PRAGMA table_info(api_key_stats)")}
        for column, ddl in (("username", "TEXT"),):
            if column not in existing:
                conn.execute(f"ALTER TABLE api_key_stats ADD COLUMN {column} {ddl};")

        # Create an index on the fingerprint for O(1) verification lookups
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tsa_fingerprint ON api_key_stats(tsa_fingerprint);")
        # Create an index on api_key for fast stats queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_api_key ON api_key_stats(api_key);")
        # /api/monitoring and the stats queries filter and sort on timestamp
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON api_key_stats(timestamp);")
        conn.commit()
    finally:
        conn.close()


def _prime_rate_limiter_cache():
    """Prime the in-memory rate limiter cache from the SQLite log database."""
    _init_db()  # Make sure DB and tables are initialized first
    if not os.path.exists(DB_FILE):
        return

    conn = _get_db_conn()
    try:
        from datetime import datetime, timedelta
        cutoff = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        # Query the latest 5000 rows using indexed primary key (under 1ms, zero table scan!)
        cursor = conn.execute("SELECT api_key, timestamp FROM api_key_stats ORDER BY id DESC LIMIT 5000")
        rows = list(cursor)
        rows.reverse() # Restore chronological ascending order

        for api_key, ts_str in rows:
            if ts_str >= cutoff:
                try:
                    dt = datetime.fromisoformat(ts_str)
                    epoch = dt.timestamp()
                    if api_key not in _key_usage_timestamps:
                        _key_usage_timestamps[api_key] = []
                    _key_usage_timestamps[api_key].append(epoch)
                except Exception:
                    pass
    except Exception:
        pass
    finally:
        conn.close()


@app.on_event("startup")
def startup_event():
    _prime_rate_limiter_cache()


def _build_complete_manifest(owner: str, smiles: str, target: str, indication: str, timestamp: str, result: dict) -> str:
    ov = result.get("overview", {})
    bio = result.get("biology", {})
    tox = result.get("toxicology", {})
    ph = result.get("pharmacology", {})
    mc = result.get("medchem", {})

    # Helper to format percentage values safely
    def _pct(val):
        if val is None:
            return "N/A"
        try:
            return f"{float(val) * 100:.2f}%" if float(val) <= 1.0 else f"{float(val):.2f}%"
        except Exception:
            return str(val)

    manifest_lines = [
        "AlphaForge Clinical Attrition Prediction Manifest",
        "==========================================",
        f"Authorized Owner: {owner}",
        f"SMILES: {smiles.strip()}",
        f"Target Class: {target.strip()}",
        f"Therapeutic Indication: {indication.strip()}",
        f"Certified Timestamp: {timestamp}",
        "",
        "Consensus Overview",
        "------------------",
        f"MedChem Score AlphaForge: {ov.get('medchem_score', 'N/A')}",
        f"TCSP (Total Clinical Success Probability): {_pct(ov.get('tcsp'))}",
        f"Phase 1 Transition Probability: {_pct(ov.get('final_p1'))}",
        f"Phase 2 Transition Probability: {_pct(ov.get('final_p2'))}",
        f"Phase 3 Transition Probability: {_pct(ov.get('final_p3'))}",
        f"Consensus Rationale:\n{ov.get('rationale', 'N/A')}",
        "",
        "Biological-Rationalist Assessment",
        "---------------------------------",
        f"Verdict: {bio.get('verdict', 'N/A')}",
        f"Mechanism Validation: {bio.get('mechanism_validation', 'N/A')}",
        f"Druggability Assessment: {bio.get('druggability', 'N/A')}",
        f"Phase 1 Probability: {_pct(bio.get('bio_p1'))}",
        f"Phase 2 Probability: {_pct(bio.get('bio_p2'))}",
        f"Phase 3 Probability: {_pct(bio.get('bio_p3'))}",
        f"Rationale:\n{bio.get('rationale', 'N/A')}",
        "",
        "Toxi-Predictive-Toxicologist Assessment",
        "---------------------------------------",
        f"Verdict: {tox.get('verdict', 'N/A')}",
        f"Therapeutic Window: {tox.get('therapeutic_window', 'N/A')}",
        f"Primary Concern: {tox.get('primary_concern', 'N/A')}",
        f"On-Target Risk: {tox.get('on_target_risk', 'N/A')}",
        f"Off-Target Risk: {tox.get('off_target_risk', 'N/A')}",
        f"Phase 1 Probability: {_pct(tox.get('tox_p1'))}",
        f"Phase 2 Probability: {_pct(tox.get('tox_p2'))}",
        f"Phase 3 Probability: {_pct(tox.get('tox_p3'))}",
        f"Rationale:\n{tox.get('rationale', 'N/A')}",
        "",
        "Pharma-Clinical-Pharmacologist Assessment",
        "-----------------------------------------",
        f"Verdict: {ph.get('verdict', 'N/A')}",
        f"Predicted Dose: {ph.get('predicted_dose', 'N/A')}",
        f"Oral Feasibility: {ph.get('oral_feasibility', 'N/A')}",
        f"DDI Risk: {ph.get('ddi_risk', 'N/A')}",
        f"Half-Life: {ph.get('half_life', 'N/A')}",
        f"Phase 1 Probability: {_pct(ph.get('pk_p1'))}",
        f"Phase 2 Probability: {_pct(ph.get('pk_p2'))}",
        f"Phase 3 Probability: {_pct(ph.get('pk_p3'))}",
        f"Rationale:\n{ph.get('rationale', 'N/A')}",
        "",
        "MedChem-Rationalist Assessment (Pass 1)",
        "---------------------------------------",
        f"Metabolic Stability: {ov.get('metabolic_stability', 'N/A')}",
        f"Toxic Fragments: {ov.get('toxic_fragments', 'N/A')}",
        f"Phase 1 Probability: {_pct(mc.get('chem_p1'))}",
        f"Phase 2 Probability: {_pct(mc.get('chem_p2'))}",
        f"Phase 3 Probability: {_pct(mc.get('chem_p3'))}",
        f"Structural Assessment:\n{ov.get('structural_assessment', 'N/A')}"
    ]
    return "\n".join(manifest_lines) + "\n"


def _get_rfc3161_timestamp(data_to_hash: bytes) -> str:
    """Make a live RFC 3161 request to DigiCert's public TSA server.

    Returns the base64-encoded TSR (Time-Stamp Response) signature.
    """
    import hashlib
    import random
    import urllib.request
    import base64

    sha256_hash = hashlib.sha256(data_to_hash).digest()
    # 4-byte random nonce
    nonce = bytes([random.randint(0, 255) for _ in range(4)])

    # Construct the binary RFC 3161 request structure
    req = bytearray([
        0x30, 0x3f,        # Sequence, length 63
        0x02, 0x01, 0x01,  # Version: 1
        0x30, 0x31,        # MessageImprint Sequence, length 49
        0x30, 0x0d,        # AlgorithmIdentifier Sequence, length 13
        0x06, 0x09, 0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01,  # OID (SHA-256)
        0x05, 0x00,        # NULL parameter
        0x04, 0x20         # Octet String, length 32
    ])
    req.extend(sha256_hash)
    req.extend([0x02, 0x04])
    req.extend(nonce)
    req.extend([0x01, 0x01, 0xff])

    tsa_url = "http://timestamp.digicert.com"
    headers = {
        "Content-Type": "application/timestamp-query",
        "User-Agent": "DrugSuccessPredictor/1.0"
    }

    try:
        url_req = urllib.request.Request(tsa_url, data=bytes(req), headers=headers, method="POST")
        with urllib.request.urlopen(url_req, timeout=10) as resp:
            resp_data = resp.read()
        if resp_data and resp_data[0] == 0x30:
            return base64.b64encode(resp_data).decode("utf-8")
    except Exception:
        pass
    return ""


def _log_api_key_stats(api_key: str, smiles: str, target: str, indication: str, owner: str = "", tsa_fingerprint: str = "", tsa_timestamp: str = "", tsa_signature_b64: str = "", tsa_manifest: str = "", prediction_json: dict = None):
    """Log prediction details into the SQLite database."""
    from datetime import datetime
    conn = _get_db_conn()
    try:
        pred_str = json.dumps(prediction_json) if prediction_json else None
        conn.execute(
            """
            INSERT INTO api_key_stats (
                timestamp, api_key, owner, smiles, target, indication, 
                tsa_fingerprint, tsa_timestamp, tsa_signature_b64, tsa_manifest, prediction_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                api_key,
                owner,
                smiles.strip(),
                target.strip(),
                indication.strip(),
                tsa_fingerprint,
                tsa_timestamp,
                tsa_signature_b64,
                tsa_manifest,
                pred_str
            )
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _get_api_key_stats(api_key: str) -> dict:
    """Compute statistics and breakdowns for a specific API Key from the SQLite database."""
    if not os.path.exists(DB_FILE):
        return {
            "total_predictions": 0,
            "unique_molecules": 0,
            "unique_targets": 0,
            "unique_indications": 0,
            "predictions_per_indication": {},
            "predictions_per_target": {}
        }

    conn = _get_db_conn()
    try:
        # Get total predictions
        cursor = conn.execute("SELECT COUNT(*) FROM api_key_stats WHERE api_key = ?", (api_key,))
        total_predictions = cursor.fetchone()[0] or 0

        # Get unique molecules
        cursor = conn.execute("SELECT COUNT(DISTINCT smiles) FROM api_key_stats WHERE api_key = ?", (api_key,))
        unique_molecules = cursor.fetchone()[0] or 0

        # Get unique targets
        cursor = conn.execute("SELECT COUNT(DISTINCT target) FROM api_key_stats WHERE api_key = ?", (api_key,))
        unique_targets = cursor.fetchone()[0] or 0

        # Get unique indications
        cursor = conn.execute("SELECT COUNT(DISTINCT indication) FROM api_key_stats WHERE api_key = ?", (api_key,))
        unique_indications = cursor.fetchone()[0] or 0

        # Get predictions per target
        cursor = conn.execute(
            "SELECT target, COUNT(*) FROM api_key_stats WHERE api_key = ? AND target IS NOT NULL AND target != '' GROUP BY target", 
            (api_key,)
        )
        by_target = {row[0].strip(): row[1] for row in cursor}

        # Get predictions per indication
        cursor = conn.execute(
            "SELECT indication, COUNT(*) FROM api_key_stats WHERE api_key = ? AND indication IS NOT NULL AND indication != '' GROUP BY indication", 
            (api_key,)
        )
        by_indication = {row[0].strip(): row[1] for row in cursor}

    except Exception:
        total_predictions = 0
        unique_molecules = 0
        unique_targets = 0
        unique_indications = 0
        by_target = {}
        by_indication = {}
    finally:
        conn.close()

    return {
        "total_predictions": total_predictions,
        "unique_molecules": unique_molecules,
        "unique_targets": unique_targets,
        "unique_indications": unique_indications,
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
    is_admin = key_info.get("admin", False)

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

    response_data = {
        "valid": True,
        "owner": owner,
        "rate_limit": rate_limit,
        "usage": usage_count,
        "remaining": remaining,
        "window": rate_window,
        "admin": is_admin,
        "evaluating_now": _key_evaluating_counts.get(api_key, 0),
        "queued_now": _key_queued_counts.get(api_key, 0),
        "stats": stats
    }

    if is_admin:
        all_keys = []
        for k, info in keys.items():
            k_stats = _get_api_key_stats(k)
            all_keys.append({
                "key": k,
                "owner": info.get("owner", "Unknown"),
                "rate_limit": info.get("rate_limit", 0),
                "rate_window": info.get("rate_window", 3600),
                "admin": info.get("admin", False),
                "stats": k_stats
            })
        response_data["all_keys"] = all_keys

    return response_data


@app.post("/api/admin/keys")
def add_or_edit_key(req: AdminKeyRequest, request: Request):
    # Verify the requester is an admin
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

    if api_key not in keys or not keys[api_key].get("admin"):
        raise HTTPException(403, "Access denied. Admin privileges required.")

    # Create or edit
    target_key = req.key.strip()
    if not target_key:
        import secrets
        # Generate a high-entropy hex secure key
        random_hex = secrets.token_hex(8)
        limit_suffix = "unlimited" if req.rate_limit < 0 else f"limit{req.rate_limit}"
        target_key = f"alphaforge_{req.owner.lower().replace(' ', '_')}_{limit_suffix}_{random_hex}"

    # Check if target key is Stelios's key and we are trying to demote him (prevent self-lockout)
    if target_key == "alphaforge_stelios_unlimited_a28b6d39c04f5e71" and not req.admin:
        raise HTTPException(400, "Cannot remove admin privilege from the main administrator.")

    keys[target_key] = {
        "owner": req.owner.strip(),
        "rate_limit": req.rate_limit,
        "rate_window": req.rate_window,
        "admin": req.admin
    }

    try:
        with open(KEYS_FILE, "w") as f:
            json.dump(keys, f, indent=2)
    except Exception as e:
        raise HTTPException(500, f"Failed to save API Keys: {e}")

    return {"status": "success", "key": target_key, "owner": req.owner.strip()}


@app.post("/api/admin/keys/delete")
def delete_key(req: AdminDeleteKeyRequest, request: Request):
    # Verify the requester is an admin
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

    if api_key not in keys or not keys[api_key].get("admin"):
        raise HTTPException(403, "Access denied. Admin privileges required.")

    target_key = req.key.strip()
    if target_key not in keys:
        raise HTTPException(404, "Target API Key not found.")

    if target_key == "alphaforge_stelios_unlimited_a28b6d39c04f5e71":
        raise HTTPException(400, "Cannot delete the main administrator key.")

    del keys[target_key]

    try:
        with open(KEYS_FILE, "w") as f:
            json.dump(keys, f, indent=2)
    except Exception as e:
        raise HTTPException(500, f"Failed to save API Keys: {e}")

    return {"status": "success", "deleted_key": target_key}


@app.get("/api/admin/config")
def get_admin_config(request: Request):
    # Verify the requester is an admin
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

    if api_key not in keys or not keys[api_key].get("admin"):
        raise HTTPException(403, "Access denied. Admin privileges required.")

    # Read config
    limit = _load_concurrency_limit()
    return {"concurrency_limit": limit}


@app.post("/api/admin/config")
def update_admin_config(req: AdminConfigRequest, request: Request):
    # Verify the requester is an admin
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

    if api_key not in keys or not keys[api_key].get("admin"):
        raise HTTPException(403, "Access denied. Admin privileges required.")

    # Update config
    new_limit = max(1, req.concurrency_limit)

    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"concurrency_limit": new_limit}, f, indent=2)
    except Exception as e:
        raise HTTPException(500, f"Failed to save global config: {e}")

    # Resize the semaphore dynamically in memory!
    _concurrency_semaphore.resize(new_limit)

    return {"status": "success", "concurrency_limit": new_limit}


@app.post("/api/admin/backup")
def run_backup(request: Request):
    # Verify the requester is an admin
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

    if api_key not in keys or not keys[api_key].get("admin"):
        raise HTTPException(403, "Access denied. Admin privileges required.")

    # Call backup.sh
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), "..", "backup.sh")
    try:
        proc = subprocess.run([script_path], capture_output=True, text=True, check=True)
        stdout = proc.stdout
        # Check if upload was successful or had warnings (like permission issues)
        if "Warning" in proc.stderr or "Warning" in proc.stdout or "failed" in proc.stdout.lower():
            # Backup succeeded locally but GCS upload failed
            return {
                "status": "warning",
                "message": "Database backup completed locally, but Google Cloud Storage upload failed. Please verify that the Compute Engine Service Account has write access to the bucket.",
                "details": stdout + "\n" + proc.stderr
            }
        return {
            "status": "success",
            "message": "Database backup completed successfully and uploaded to Google Cloud Storage (reneu001/timestamps-database-backup)!",
            "details": stdout
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, f"Backup failed: {e.stderr or e.stdout}")
    except Exception as e:
        raise HTTPException(500, f"Failed to execute backup script: {e}")


@app.get("/api/verify/count")
def get_verify_count():
    if not os.path.exists(DB_FILE):
        return {"total_timestamps": 0}
    conn = _get_db_conn()
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM api_key_stats")
        row = cursor.fetchone()
        return {"total_timestamps": row[0] if row else 0}
    except Exception as e:
        raise HTTPException(500, f"Error counting timestamps: {e}")
    finally:
        conn.close()


@app.get("/api/verify")
def verify_prediction(hash: str):
    target_hash = hash.strip()
    if not target_hash:
        raise HTTPException(400, "Hash parameter is required")

    if not os.path.exists(DB_FILE):
        raise HTTPException(404, "No evaluations recorded on this server.")

    conn = _get_db_conn()
    try:
        cursor = conn.execute("SELECT * FROM api_key_stats WHERE tsa_fingerprint = ?", (target_hash,))
        row = cursor.fetchone()
        if row:
            # Table columns:
            # id, timestamp, api_key, owner, smiles, target, indication, 
            # tsa_fingerprint, tsa_timestamp, tsa_signature_b64, tsa_manifest, prediction_json
            pred_json = None
            if row[11]:
                try:
                    pred_json = json.loads(row[11])
                except Exception:
                    pass
            return {
                "found": True,
                "owner": row[3] or "Registered User",
                "timestamp": row[1],
                "smiles": row[4],
                "target": row[5],
                "indication": row[6],
                "tsa_fingerprint": row[7],
                "tsa_timestamp": row[8],
                "tsa_signature_b64": row[9],
                "tsa_manifest": row[10] or "",
                "prediction_json": pred_json
            }
    except Exception as e:
        raise HTTPException(500, f"Error searching database: {e}")
    finally:
        conn.close()

    raise HTTPException(404, "Evaluation not found. Please verify the SHA-256 fingerprint.")


@app.get("/api/monitoring")
def get_monitoring_data(request: Request, mode: str = "mine", zoom_minutes: int = 60):
    # Authenticate via API Key to ensure they have a valid key
    key_info = _authenticate_and_rate_limit(request)
    api_key = key_info["key"]

    if not os.path.exists(DB_FILE):
        return {"runs": [], "snapshots": []}

    # Calculate cutoff time in UTC
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(minutes=zoom_minutes + 5)).isoformat()

    conn = _get_db_conn()
    try:
        if mode == "mine":
            cursor = conn.execute(
                "SELECT id, timestamp, owner, target, username FROM api_key_stats WHERE api_key = ? AND timestamp >= ? ORDER BY id DESC",
                (api_key, cutoff)
            )
        else:
            cursor = conn.execute(
                "SELECT id, timestamp, owner, target, username FROM api_key_stats WHERE timestamp >= ? ORDER BY id DESC",
                (cutoff,)
            )

        runs = []
        for row in cursor:
            runs.append({
                "id": row[0],
                "timestamp": row[1],
                "owner": row[2] or "Registered User",
                "target": row[3],
                "username": row[4] or row[2] or "Ramil"
            })

        # Downsample the runs if there are too many (e.g. more than 1000) to keep it lightweight and super fast!
        if len(runs) > 1000:
            step = len(runs) // 1000
            runs = runs[::step]

        runs.reverse() # Sort chronologically ascending for charts

        # Filter snapshots based on mode and cutoff time
        filtered_snaps = [
            s for s in _queue_snapshots 
            if (mode == "all" or s["api_key"] == api_key) and s["timestamp"] >= cutoff
        ]

        return {"runs": runs, "snapshots": filtered_snaps}
    except Exception as e:
        raise HTTPException(500, f"Database error: {e}")
    finally:
        conn.close()


@app.get("/api/visits")
def visits():
    return get_visits_summary()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


async def _execute_prediction(
    key_info: dict,
    smiles: str,
    target: str,
    indication: str,
    auxiliary: str = "",
    web_search: bool = False,
    mock: bool = False,
    ip: str = "",
    ua: str = "",
    path_label: str = "/api/analyze",
) -> dict:
    """Run one complete prediction: pipeline -> manifest -> DigiCert TSA -> DB log.

    Shared by /api/analyze and /api/deep-analyze so that every deep-analysis
    simulation is timestamped, fingerprinted and tracked exactly like a normal
    single prediction (and therefore shows up in monitoring and /verify).

    Maintains the queued/evaluating counters the dashboard reads, with the same
    cancellation safety as the original endpoint.
    """
    global _evaluating_count, _queued_count

    # Tracking queued and evaluating states with cancellation safety
    api_key = key_info["key"]
    _queued_count += 1
    _key_queued_counts[api_key] = _key_queued_counts.get(api_key, 0) + 1
    _add_queue_snapshot(api_key)

    queued_decremented = False
    evaluating_incremented = False
    try:
        async with _concurrency_semaphore:
            # We are inside the semaphore, so we transition from queued to evaluating
            _queued_count -= 1
            _key_queued_counts[api_key] = max(0, _key_queued_counts.get(api_key, 0) - 1)
            queued_decremented = True

            _evaluating_count += 1
            _key_evaluating_counts[api_key] = _key_evaluating_counts.get(api_key, 0) + 1
            evaluating_incremented = True
            _add_queue_snapshot(api_key)

            if mock:
                # Simulate a 5-second analysis
                await asyncio.sleep(5)
                result = {
                    "overview": {
                        "medchem_score": 42,
                        "tcsp": 0.15,
                        "final_p1": 0.6, "final_p2": 0.5, "final_p3": 0.5,
                        "rationale": "Mock analysis for testing.",
                        "metabolic_stability": "Medium",
                        "toxic_fragments": "None",
                        "structural_assessment": "Clean"
                    },
                    "biology": {"verdict": "ELITE", "rationale": "Mock bio rationale"},
                    "toxicology": {"verdict": "CLEAN", "rationale": "Mock tox rationale"},
                    "pharmacology": {"verdict": "FAVORABLE", "rationale": "Mock pk rationale"},
                    "medchem": {"chem_p1": 0.6, "chem_p2": 0.5, "chem_p3": 0.5}
                }
            else:
                # Run the CPU/network-bound pipeline in a threadpool
                result = await asyncio.to_thread(
                    run_pipeline,
                    smiles.strip(),
                    target.strip(),
                    indication.strip(),
                    auxiliary.strip(),
                    web_search=web_search,
                )
    finally:
        # Robust cleanup that handles ALL cancellations and edge cases
        if not queued_decremented:
            _queued_count -= 1
            _key_queued_counts[api_key] = max(0, _key_queued_counts.get(api_key, 0) - 1)
        if evaluating_incremented:
            _evaluating_count -= 1
            _key_evaluating_counts[api_key] = max(0, _key_evaluating_counts.get(api_key, 0) - 1)
        _add_queue_snapshot(api_key)

    # Build secure plain-text manifest file content (fully detailed, including all verdicts/rationales!)
    ts_str = datetime.utcnow().isoformat()
    tsa_manifest = _build_complete_manifest(
        key_info["owner"],
        smiles,
        target,
        indication,
        ts_str,
        result
    )

    tsa_fingerprint = hashlib.sha256(tsa_manifest.encode("utf-8")).hexdigest()

    # Make the actual DigiCert trusted timestamp request on the plain-text manifest.
    # Off-loaded to a thread: it is a blocking HTTP call, and deep analysis fires
    # many of these concurrently, so it must not stall the event loop.
    tsa_signature_b64 = await asyncio.to_thread(
        _get_rfc3161_timestamp, tsa_manifest.encode("utf-8")
    )

    # Append TSA verification fields to result response
    result["tsa_fingerprint"] = tsa_fingerprint
    result["tsa_timestamp"] = ts_str
    result["tsa_signature_b64"] = tsa_signature_b64
    result["tsa_manifest"] = tsa_manifest

    # Record successful usage
    _record_key_usage(api_key, key_info["rate_limit"])
    await asyncio.to_thread(
        _log_api_key_stats,
        api_key,
        smiles,
        target,
        indication,
        owner=key_info["owner"],
        tsa_fingerprint=tsa_fingerprint,
        tsa_timestamp=ts_str,
        tsa_signature_b64=tsa_signature_b64,
        tsa_manifest=tsa_manifest,
        prediction_json=result,
    )

    log_visit(ip, f"{path_label}?owner={key_info['owner']}", ua)
    log_prediction(result)
    return result


def _validate_analyze_inputs(req) -> None:
    if not req.smiles.strip():
        raise HTTPException(400, "SMILES is required")
    if not req.target.strip():
        raise HTTPException(400, "Target is required")
    if not req.indication.strip():
        raise HTTPException(400, "Indication is required")


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest, request: Request):
    # Authenticate and rate limit via API Key
    key_info = _authenticate_and_rate_limit(request)

    ip = _get_client_ip(request)
    _validate_analyze_inputs(req)

    return await _execute_prediction(
        key_info,
        req.smiles,
        req.target,
        req.indication,
        auxiliary=req.auxiliary,
        web_search=req.web_search,
        mock=req.mock,
        ip=ip,
        ua=request.headers.get("user-agent", ""),
        path_label="/api/analyze",
    )


def _prune_deep_jobs():
    """Keep only the most recent DEEP_JOB_RETENTION jobs to bound memory."""
    if len(_deep_jobs) <= DEEP_JOB_RETENTION:
        return
    ordered = sorted(_deep_jobs.items(), key=lambda kv: kv[1].get("started_at", ""))
    for job_id, _ in ordered[: len(_deep_jobs) - DEEP_JOB_RETENTION]:
        _deep_jobs.pop(job_id, None)


async def _run_deep_job(job_id: str, key_info: dict, req: "DeepAnalyzeRequest", ip: str, ua: str):
    """Execute N simulations with bounded fan-out, aggregating as they land."""
    job = _deep_jobs[job_id]
    gate = asyncio.Semaphore(DEEP_FANOUT)
    results = []

    async def one(index: int):
        async with gate:
            if job["status"] == "cancelled":
                return None
            try:
                r = await _execute_prediction(
                    key_info,
                    req.smiles,
                    req.target,
                    req.indication,
                    auxiliary=req.auxiliary,
                    web_search=req.web_search,
                    mock=req.mock,
                    ip=ip,
                    ua=ua,
                    path_label="/api/deep-analyze",
                )
                job["completed"] += 1
                return r
            except Exception as e:
                job["failed"] += 1
                # Keep only the first few messages — 100 copies of the same
                # quota error is not useful diagnostics.
                if len(job["errors"]) < 5:
                    job["errors"].append(str(e))
                return None

    try:
        gathered = await asyncio.gather(
            *[one(i) for i in range(req.n_simulations)], return_exceptions=True
        )
        results = [r for r in gathered if r and not isinstance(r, Exception)]

        job["report"] = await asyncio.to_thread(
            deep_aggregate, results, req.n_simulations
        )
        job["status"] = "cancelled" if job["status"] == "cancelled" else "done"
    except Exception as e:
        job["status"] = "error"
        job["errors"].append(str(e))
    finally:
        job["finished_at"] = datetime.utcnow().isoformat()


@app.post("/api/deep-analyze")
async def deep_analyze(req: DeepAnalyzeRequest, request: Request):
    """Kick off a deep analysis and return a job id immediately.

    N simulations cannot finish inside one HTTP request, so the client polls
    GET /api/deep-analyze/{job_id} for progress and the final report.
    """
    key_info = _authenticate_and_rate_limit(request)
    ip = _get_client_ip(request)
    _validate_analyze_inputs(req)

    n = req.n_simulations
    if n < 2:
        raise HTTPException(400, "Deep analysis needs at least 2 simulations.")
    if n > DEEP_MAX_SIMULATIONS:
        raise HTTPException(
            400, f"Deep analysis is capped at {DEEP_MAX_SIMULATIONS} simulations."
        )

    job_id = uuid.uuid4().hex
    _deep_jobs[job_id] = {
        "job_id": job_id,
        "status": "running",
        "owner": key_info["owner"],
        "requested": n,
        "completed": 0,
        "failed": 0,
        "errors": [],
        "report": None,
        "smiles": req.smiles.strip(),
        "target": req.target.strip(),
        "indication": req.indication.strip(),
        "started_at": datetime.utcnow().isoformat(),
        "finished_at": None,
    }
    _prune_deep_jobs()

    asyncio.create_task(
        _run_deep_job(job_id, key_info, req, ip, request.headers.get("user-agent", ""))
    )

    return {
        "job_id": job_id,
        "status": "running",
        "requested": n,
        "fanout": DEEP_FANOUT,
    }


@app.get("/api/deep-analyze/{job_id}")
def deep_analyze_status(job_id: str, request: Request):
    """Progress + final report for a deep-analysis job."""
    _authenticate_and_rate_limit(request)
    job = _deep_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown or expired deep-analysis job.")
    return job


@app.post("/api/deep-analyze/{job_id}/cancel")
def deep_analyze_cancel(job_id: str, request: Request):
    """Stop launching further simulations for a running job."""
    _authenticate_and_rate_limit(request)
    job = _deep_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown or expired deep-analysis job.")
    if job["status"] == "running":
        job["status"] = "cancelled"
    return {"job_id": job_id, "status": job["status"]}


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
