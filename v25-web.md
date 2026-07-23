---
name: v25-web
description: >
  Run molecule developability/clinical-success evaluations against the V25
  web backend (the "Will Your Drug Succeed in the Clinic?" / CDR scoring
  service). Use this when you need to score one or many molecules by calling
  its HTTP API, batch many evaluations concurrently, and write every returned
  value, rationale, and web-search summary to a CSV file.
---

# V25 Web — Molecule Evaluation via Backend API

This skill lets you (the agent) drive the V25 4-agent developability pipeline
through its HTTP backend, evaluate **many molecules in a batch**, and persist
**all** outputs (scores, probabilities, verdicts, rationales, web-search
summaries, FDA status) into a single CSV.

You do **not** need the model code or the conda environment. You only need
network access to the backend and the API contract below.

---

## 1. Backend endpoint

- **Base URL:** `http://136.119.133.178:8001` (default for this skill — use this
  unless the operator gives you a different one). Override with the
  `V25_BASE_URL` env var if needed.
- **Health check:** `GET {BASE_URL}/api/health` → `{"status":"ok"}`. Call this
  first; abort the run if it does not return 200.
- **Evaluate:** `POST {BASE_URL}/api/analyze` (JSON body, JSON response).

### Request body (`POST /api/analyze`)

```json
{
  "smiles": "CC(=O)Oc1ccccc1C(=O)O",   // required, non-empty
  "target": "COX inhibitor",            // required, non-empty (target class)
  "indication": "Inflammation",         // required, non-empty
  "auxiliary": "",                      // optional free-text context
  "web_search": false                   // optional; true = grounded web search + FDA status
}
```

- All three of `smiles`, `target`, `indication` are **required**; an empty one
  returns HTTP 400.
- `web_search: true` makes the backend run live Google-grounded searches
  (literature summary + current FDA status) and append a validated summary to
  the agents' context. It is **much slower** (~60–120s vs ~20–60s) and consumes
  external API quota. Default to `false` unless web evidence is explicitly
  wanted.

### Response body (HTTP 200)

Top-level keys: `web_search`, `overview`, `medchem`, `biology`, `toxicology`,
`pharmacology`.

```jsonc
{
  "web_search": null,            // null unless web_search:true was sent; see §5
  "overview": {
    "medchem_score": 73,         // 1–100 Clinical Developability Risk (CDR) score (higher = lower risk)
    "tcsp": 0.123456,            // total clinical-success probability (p1*p2*p3)
    "tcsp_pct": 12.35,
    "final_p1": 0.62, "final_p2": 0.41, "final_p3": 0.55,   // consensus phase-transition probs
    "final_p1_rationale": "...", "final_p2_rationale": "...", "final_p3_rationale": "...",
    "rationale": "...",          // overall narrative
    "metabolic_stability": "...",
    "toxic_fragments": "...",
    "structural_assessment": "..."
  },
  "biology": {
    "verdict": "...", "rationale": "...",
    "mechanism_validation": "...", "druggability": "...",
    "bio_p1": 0.7, "bio_p2": 0.5, "bio_p3": 0.6,
    "bio_p1_rationale": "...", "bio_p2_rationale": "...", "bio_p3_rationale": "...",
    "raw": { /* full raw agent JSON */ }
  },
  "toxicology": {
    "verdict": "...", "rationale": "...",
    "therapeutic_window": "...", "primary_concern": "...",
    "on_target_risk": "...", "off_target_risk": "...",
    "tox_p1": 0.8, "tox_p2": 0.6, "tox_p3": 0.7,
    "tox_p1_rationale": "...", "tox_p2_rationale": "...", "tox_p3_rationale": "...",
    "raw": { /* ... */ }
  },
  "pharmacology": {
    "verdict": "...", "rationale": "...",
    "predicted_dose": "...", "oral_feasibility": "...",
    "ddi_risk": "...", "half_life": "...",
    "pk_p1": 0.7, "pk_p2": 0.6, "pk_p3": 0.65,
    "pk_p1_rationale": "...", "pk_p2_rationale": "...", "pk_p3_rationale": "...",
    "raw": { /* ... */ }
  },
  "medchem": {
    "pass1": { /* blind structural assessment */ },
    "pass2": { /* advisory-integrated assessment */ },
    "chem_p1": 0.6, "chem_p2": 0.5, "chem_p3": 0.55
  }
}
```

### Error responses
- `400` — missing/empty required field.
- `429` — **global rate limit hit** (100 predictions/hour across all callers).
  The `detail` message states when it resets. **Back off and retry**, do not
  hammer.
- `500` — pipeline error (often an upstream LLM quota/timeout). Retry a couple
  of times with backoff; if it persists, record the error in the CSV and move
  on — do not let one failure abort the batch.

---

## 2. Single-call sanity check (do this first)

```bash
curl -s -X POST "$BASE_URL/api/analyze" \
  -H 'Content-Type: application/json' \
  -d '{"smiles":"CC(=O)Oc1ccccc1C(=O)O","target":"COX inhibitor","indication":"Inflammation"}'
```

Confirm you get a 200 with an `overview.medchem_score` before launching a batch.

---

## 3. Batching rules (READ THIS)

Each evaluation runs 5+ sequential LLM calls server-side and takes tens of
seconds. You **must** parallelize to evaluate many molecules in reasonable time,
but within these constraints:

1. **Concurrency cap: 3–5 simultaneous requests.** More will not help (the
   server itself fans out internally) and risks tripping the rate limit.
2. **Respect the global rate limit: 100 evaluations/hour.** If your batch is
   larger, throttle to stay under it, or coordinate exempt access with the
   operator. On a `429`, sleep until the reset time in the error and resume.
3. **Per-request timeout:** allow at least **180s** per call (`web_search:true`
   needs the full window).
4. **Retries:** retry `429`/`500`/network errors up to 3× with exponential
   backoff (e.g. 5s, 15s, 45s). Never retry a `400` — that's a bad input; log
   it and skip.
5. **Never drop a row silently.** Every input molecule must produce exactly one
   CSV row, even on failure (with the error captured in an `error` column).

---

## 4. REQUIRED output: one CSV with ALL results

After the batch, write a **single CSV file** (default `v25_results.csv`) with
**one row per input molecule** and a column for every value, probability,
verdict, rationale, and summary returned. Do not summarize or omit fields — the
whole point is a complete, machine-readable record.

**Column order (exact):**

```
smiles, target, indication, auxiliary, web_search,
medchem_score, tcsp, tcsp_pct,
final_p1, final_p2, final_p3,
final_p1_rationale, final_p2_rationale, final_p3_rationale,
overall_rationale, metabolic_stability, toxic_fragments, structural_assessment,
bio_verdict, bio_rationale, mechanism_validation, druggability,
bio_p1, bio_p2, bio_p3, bio_p1_rationale, bio_p2_rationale, bio_p3_rationale,
toxi_verdict, toxi_rationale, therapeutic_window, primary_concern,
on_target_risk, off_target_risk,
tox_p1, tox_p2, tox_p3, tox_p1_rationale, tox_p2_rationale, tox_p3_rationale,
pharma_verdict, pharma_rationale, predicted_dose, oral_feasibility, ddi_risk, half_life,
pk_p1, pk_p2, pk_p3, pk_p1_rationale, pk_p2_rationale, pk_p3_rationale,
chem_p1, chem_p2, chem_p3,
ws_validated, ws_summary, ws_references,
fda_overall, fda_drug_name, fda_headline, fda_events, fda_references,
medchem_pass2_json, error
```

- Multi-item fields (`ws_references`, `fda_events`, `fda_references`) are
  flattened to a readable string (one item per line, or ` | `-joined).
- `medchem_pass2_json` holds the full `medchem.pass2` object JSON-dumped, so no
  raw detail is lost.
- `error` is empty on success, or the error message/status on failure.

---

## 5. Web-search fields (only when `web_search:true`)

When enabled, `web_search` is an object:

```jsonc
"web_search": {
  "summary": "validated literature summary prose",
  "references": [{"title": "fda.gov", "uri": "https://..."}],
  "validated": true,
  "fda": {
    "drug_name": "Reproxalap",
    "overall": "negative",          // positive | negative | mixed | none
    "headline": "FDA issued a Complete Response Letter in 2023.",
    "events": [{"sentiment":"negative","date":"2023","title":"Complete Response Letter","detail":"..."}],
    "references": [{"title":"fda.gov","uri":"https://..."}]
  }
}
```

`fda.overall == "none"` means **no formal FDA action on record** (e.g. a drug
discontinued by its sponsor) — that is distinct from the literature summary,
which may still describe trial outcomes. Record both faithfully.

---

## 6. Ready-to-run batch script

Reads molecules from an input CSV (`smiles,target,indication[,auxiliary]`),
evaluates them concurrently, and writes the complete results CSV.

```python
#!/usr/bin/env python3
"""Batch-evaluate molecules against the V25 web backend and write a full CSV."""
import csv, json, os, sys, time, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

BASE_URL = os.environ.get("V25_BASE_URL", "http://136.119.133.178:8001")
MAX_WORKERS = 4          # 3–5; do not exceed
TIMEOUT = 180            # seconds per request
MAX_RETRIES = 3

COLUMNS = [
    "smiles","target","indication","auxiliary","web_search",
    "medchem_score","tcsp","tcsp_pct",
    "final_p1","final_p2","final_p3",
    "final_p1_rationale","final_p2_rationale","final_p3_rationale",
    "overall_rationale","metabolic_stability","toxic_fragments","structural_assessment",
    "bio_verdict","bio_rationale","mechanism_validation","druggability",
    "bio_p1","bio_p2","bio_p3","bio_p1_rationale","bio_p2_rationale","bio_p3_rationale",
    "toxi_verdict","toxi_rationale","therapeutic_window","primary_concern",
    "on_target_risk","off_target_risk",
    "tox_p1","tox_p2","tox_p3","tox_p1_rationale","tox_p2_rationale","tox_p3_rationale",
    "pharma_verdict","pharma_rationale","predicted_dose","oral_feasibility","ddi_risk","half_life",
    "pk_p1","pk_p2","pk_p3","pk_p1_rationale","pk_p2_rationale","pk_p3_rationale",
    "chem_p1","chem_p2","chem_p3",
    "ws_validated","ws_summary","ws_references",
    "fda_overall","fda_drug_name","fda_headline","fda_events","fda_references",
    "medchem_pass2_json","error",
]

def _refs(items):
    return " | ".join(f"{r.get('title','')}: {r.get('uri','')}" for r in (items or []))

def _events(items):
    return " | ".join(
        f"[{e.get('sentiment','')}] {e.get('date','')} {e.get('title','')}: {e.get('detail','')}"
        for e in (items or [])
    )

def evaluate(mol):
    """POST one molecule; return a fully-populated CSV row dict (never raises)."""
    body = {
        "smiles": mol["smiles"], "target": mol["target"],
        "indication": mol["indication"], "auxiliary": mol.get("auxiliary", ""),
        "web_search": str(mol.get("web_search", "")).lower() in ("1","true","yes"),
    }
    row = {c: "" for c in COLUMNS}
    row.update({k: body[k] for k in ("smiles","target","indication","auxiliary")})
    row["web_search"] = body["web_search"]

    last_err = ""
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(f"{BASE_URL}/api/analyze", json=body, timeout=TIMEOUT)
            if r.status_code == 400:
                row["error"] = f"400 bad input: {r.text[:200]}"
                return row                       # do not retry bad input
            if r.status_code == 429:
                last_err = f"429 rate limited: {r.text[:200]}"
                time.sleep(min(60, 5 * (3 ** attempt)))
                continue
            r.raise_for_status()
            d = r.json()
            ov, bio = d.get("overview",{}), d.get("biology",{})
            tox, ph = d.get("toxicology",{}), d.get("pharmacology",{})
            mc, ws = d.get("medchem",{}), d.get("web_search") or {}
            fda = ws.get("fda") or {}
            row.update({
                "medchem_score": ov.get("medchem_score"), "tcsp": ov.get("tcsp"), "tcsp_pct": ov.get("tcsp_pct"),
                "final_p1": ov.get("final_p1"), "final_p2": ov.get("final_p2"), "final_p3": ov.get("final_p3"),
                "final_p1_rationale": ov.get("final_p1_rationale"), "final_p2_rationale": ov.get("final_p2_rationale"),
                "final_p3_rationale": ov.get("final_p3_rationale"), "overall_rationale": ov.get("rationale"),
                "metabolic_stability": ov.get("metabolic_stability"), "toxic_fragments": ov.get("toxic_fragments"),
                "structural_assessment": ov.get("structural_assessment"),
                "bio_verdict": bio.get("verdict"), "bio_rationale": bio.get("rationale"),
                "mechanism_validation": bio.get("mechanism_validation"), "druggability": bio.get("druggability"),
                "bio_p1": bio.get("bio_p1"), "bio_p2": bio.get("bio_p2"), "bio_p3": bio.get("bio_p3"),
                "bio_p1_rationale": bio.get("bio_p1_rationale"), "bio_p2_rationale": bio.get("bio_p2_rationale"),
                "bio_p3_rationale": bio.get("bio_p3_rationale"),
                "toxi_verdict": tox.get("verdict"), "toxi_rationale": tox.get("rationale"),
                "therapeutic_window": tox.get("therapeutic_window"), "primary_concern": tox.get("primary_concern"),
                "on_target_risk": tox.get("on_target_risk"), "off_target_risk": tox.get("off_target_risk"),
                "tox_p1": tox.get("tox_p1"), "tox_p2": tox.get("tox_p2"), "tox_p3": tox.get("tox_p3"),
                "tox_p1_rationale": tox.get("tox_p1_rationale"), "tox_p2_rationale": tox.get("tox_p2_rationale"),
                "tox_p3_rationale": tox.get("tox_p3_rationale"),
                "pharma_verdict": ph.get("verdict"), "pharma_rationale": ph.get("rationale"),
                "predicted_dose": ph.get("predicted_dose"), "oral_feasibility": ph.get("oral_feasibility"),
                "ddi_risk": ph.get("ddi_risk"), "half_life": ph.get("half_life"),
                "pk_p1": ph.get("pk_p1"), "pk_p2": ph.get("pk_p2"), "pk_p3": ph.get("pk_p3"),
                "pk_p1_rationale": ph.get("pk_p1_rationale"), "pk_p2_rationale": ph.get("pk_p2_rationale"),
                "pk_p3_rationale": ph.get("pk_p3_rationale"),
                "chem_p1": mc.get("chem_p1"), "chem_p2": mc.get("chem_p2"), "chem_p3": mc.get("chem_p3"),
                "ws_validated": ws.get("validated"), "ws_summary": ws.get("summary"),
                "ws_references": _refs(ws.get("references")),
                "fda_overall": fda.get("overall"), "fda_drug_name": fda.get("drug_name"),
                "fda_headline": fda.get("headline"), "fda_events": _events(fda.get("events")),
                "fda_references": _refs(fda.get("references")),
                "medchem_pass2_json": json.dumps(mc.get("pass2", {}), ensure_ascii=False),
            })
            return row
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            time.sleep(min(60, 5 * (3 ** attempt)))
    row["error"] = last_err or "failed after retries"
    return row

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_csv", help="CSV with columns: smiles,target,indication[,auxiliary,web_search]")
    ap.add_argument("-o", "--output", default="v25_results.csv")
    args = ap.parse_args()

    # Health check first.
    try:
        h = requests.get(f"{BASE_URL}/api/health", timeout=10)
        h.raise_for_status()
    except Exception as e:
        sys.exit(f"Backend not healthy at {BASE_URL}: {e}")

    with open(args.input_csv, newline="") as f:
        mols = list(csv.DictReader(f))
    if not mols:
        sys.exit("No molecules in input CSV.")
    print(f"Evaluating {len(mols)} molecules at {BASE_URL} (workers={MAX_WORKERS})...")

    rows = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(evaluate, m): i for i, m in enumerate(mols)}
        for fut in as_completed(futs):
            row = fut.result()
            rows.append((futs[fut], row))
            tag = "ERROR" if row["error"] else f"score={row['medchem_score']}"
            print(f"  [{len(rows)}/{len(mols)}] {row['smiles'][:32]}... {tag}")

    rows.sort(key=lambda x: x[0])               # preserve input order
    with open(args.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for _, row in rows:
            w.writerow(row)
    print(f"Wrote {len(rows)} rows to {args.output}")

if __name__ == "__main__":
    main()
```

### Run it

```bash
export V25_BASE_URL="http://136.119.133.178:8001"   # default; override if the operator gives another
python batch_eval.py molecules.csv -o v25_results.csv
```

### Input CSV format (`molecules.csv`)

```csv
smiles,target,indication,auxiliary,web_search
CC(=O)Oc1ccccc1C(=O)O,COX inhibitor,Inflammation,,false
CCOC(=O)[C@H](CCC1=CC=CC=C1)N...,ACE inhibitor,Cardiovascular,,true
```

`auxiliary` and `web_search` columns are optional (default empty / false).

---

## 7. Checklist before you report done

- [ ] Health check passed before the batch started.
- [ ] Concurrency stayed at 3–5; rate limit (100/hr) respected.
- [ ] Every input molecule has exactly one row in the output CSV.
- [ ] Failures are captured in the `error` column, not dropped.
- [ ] All values, probabilities, verdicts, rationales, and (if `web_search`)
      summaries + FDA status are present in the CSV.
- [ ] Report the output CSV path and a one-line summary (n succeeded / n failed).
```
