"""Aggregation for deep analysis — statistics over N repeated simulations.

Gemini is not bit-reproducible even at temperature 0.0 (no seed parameter, and
MoE routing plus batching make identical inputs drift), so running the same
molecule N times yields a genuine sampling distribution. This module turns those
N raw pipeline results into:

  * CDR score statistics + histogram          (overview.medchem_score, 1-100)
  * per-phase probability distributions       (final_p1/p2/p3)
  * per-phase agent maxima for comparison     (max of bio/tox/pk/chem per phase)
  * risk appearance frequency, bucketed       (0-25 / 25-50 / 50-75 / 75-100 %)

Risks are extracted from the fields the agents ALREADY emit — no changes to the
prompts in Agents/*/INSTRUCTIONS.md, which are the scientific IP. Two sources:

  1. Categorical fields with an explicit severity scale (on/off-target tox risk,
     DDI risk) and the three agent verdicts. A risk "appears" in a simulation
     when the field lands on an adverse value.
  2. Free-prose fields (primary tox concern, toxic fragments, structural
     assessment, therapeutic window), matched against a canonical vocabulary of
     named liabilities so the same concern is counted under one stable name
     across simulations.

Extraction is deterministic Python — no extra LLM call, so the frequencies are
reproducible from the stored predictions.
"""

import math
import re

# ---------------------------------------------------------------------------
# Risk vocabulary
# ---------------------------------------------------------------------------

# Canonical risk name -> regex matched against the pooled free text of a run.
# Ordered roughly by how often these dominate small-molecule attrition.
RISK_PATTERNS = [
    ("hERG / QT prolongation", r"\bherg\b|\bqt\b|\btorsade|\bqtc\b"),
    ("Hepatotoxicity (DILI)", r"\bdili\b|hepatotox|liver (injury|toxicity|burden)|transaminase"),
    ("Reactive metabolite / bioactivation", r"reactive metabolit|bioactivat|quinone imine|nitroso|acyl glucuronide|hapten"),
    ("CYP inhibition / mechanism-based inactivation", r"\bcyp\b|mechanism[- ]based inactivat|\bmbi\b|time[- ]dependent inhibition"),
    ("Drug-drug interaction liability", r"\bddi\b|drug[- ]drug interaction|oatp|\bp-?gp\b|transporter inhibition"),
    ("Genotoxicity / mutagenicity", r"genotox|mutagen|\bames\b|clastogen|dna damage"),
    ("Cardiotoxicity (non-hERG)", r"cardiotox|myocard|cardiac (toxicity|failure)|heart failure"),
    ("Nephrotoxicity", r"nephrotox|renal (injury|toxicity|impairment)|kidney (injury|toxicity)"),
    ("Metabolic instability / high clearance", r"metabolic instab|high clearance|rapid (metabolism|clearance)|short half[- ]life|soft spot"),
    ("Poor oral bioavailability", r"poor (oral )?bioavailab|low bioavailab|poor absorption|low oral exposure|not orally"),
    ("Low solubility", r"low solubilit|poor solubilit|insoluble|solubility[- ]limited"),
    ("High lipophilicity", r"high (lipophilic|logp|clogp)|lipophilicity[- ]driven|greasy"),
    ("Narrow therapeutic window", r"narrow (therapeutic )?(window|index|margin)|thin margin|limited margin"),
    ("Off-target polypharmacology", r"off[- ]target|polypharmacolog|promiscuo|selectivity (issue|concern|liability)"),
    ("Immunogenicity", r"immunogenic|\bada\b|anti[- ]drug antibod|infusion reaction"),
    ("Aggregation / developability", r"aggregat|\bpsh\b|hydrophobic patch|viscosit|colloidal"),
    ("Phospholipidosis", r"phospholipidos"),
    ("Myelosuppression / haematotoxicity", r"myelosuppress|haematotox|hematotox|neutropen|thrombocytopen"),
    ("Unvalidated target biology", r"unvalidated target|novel target|no clinical precedent|unprecedented target|target validation (risk|gap)"),
    ("CNS penetration shortfall", r"cns penetration|blood[- ]brain|\bbbb\b|brain exposure"),
]

_COMPILED_RISKS = [(name, re.compile(pattern, re.I)) for name, pattern in RISK_PATTERNS]

# Categorical severity fields: a risk is counted as "appearing" when the value
# is one of the adverse levels below.
_ADVERSE_SEVERITIES = {"moderate", "high"}

_ADVERSE_VERDICTS = {
    "biology": {"caution", "terminate"},
    "toxicology": {"narrow", "toxic"},
    "pharmacology": {"challenging", "impractical"},
}

# Free-text fields pooled per simulation for vocabulary matching.
_TEXT_FIELDS = [
    ("overview", "toxic_fragments"),
    ("overview", "structural_assessment"),
    ("overview", "metabolic_stability"),
    ("overview", "rationale"),
    ("toxicology", "primary_concern"),
    ("toxicology", "therapeutic_window"),
    ("toxicology", "rationale"),
    ("pharmacology", "oral_feasibility"),
    ("pharmacology", "ddi_risk"),
    ("pharmacology", "rationale"),
    ("biology", "druggability"),
    ("biology", "rationale"),
]


def extract_risks(result: dict) -> set:
    """Return the set of canonical risk names present in one simulation."""
    risks = set()

    tox = result.get("toxicology") or {}
    pharma = result.get("pharmacology") or {}
    bio = result.get("biology") or {}

    # 1) Explicit categorical severity fields
    if str(tox.get("on_target_risk", "")).strip().lower() in _ADVERSE_SEVERITIES:
        risks.add("On-target toxicity")
    if str(tox.get("off_target_risk", "")).strip().lower() in _ADVERSE_SEVERITIES:
        risks.add("Off-target polypharmacology")
    if str(pharma.get("ddi_risk", "")).strip().lower() in _ADVERSE_SEVERITIES:
        risks.add("Drug-drug interaction liability")

    # 2) Adverse agent verdicts
    for section, adverse in _ADVERSE_VERDICTS.items():
        verdict = str((result.get(section) or {}).get("verdict", "")).strip().lower()
        if verdict in adverse:
            risks.add(f"Adverse {section} verdict ({verdict.upper()})")

    # 3) Canonical vocabulary over pooled free prose
    chunks = []
    for section, field in _TEXT_FIELDS:
        val = (result.get(section) or {}).get(field, "")
        if isinstance(val, str) and val:
            chunks.append(val)
    blob = "\n".join(chunks)
    if blob:
        for name, rx in _COMPILED_RISKS:
            if rx.search(blob):
                risks.add(name)

    return risks


# ---------------------------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------------------------

def _percentile(sorted_vals, q):
    """Linear-interpolation percentile (q in 0..1) over a pre-sorted list."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_vals[int(pos)]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def describe(values, digits=4):
    """Summary statistics for a list of numbers."""
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return {"n": 0}
    s = sorted(vals)
    n = len(s)
    mean = sum(s) / n
    # Sample standard deviation (n-1) — these are draws from the model's output
    # distribution, not an exhaustive population.
    var = sum((v - mean) ** 2 for v in s) / (n - 1) if n > 1 else 0.0
    sd = math.sqrt(var)
    stderr = sd / math.sqrt(n) if n else 0.0
    r = lambda x: None if x is None else round(x, digits)
    return {
        "n": n,
        "mean": r(mean),
        "median": r(_percentile(s, 0.5)),
        "sd": r(sd),
        "min": r(s[0]),
        "max": r(s[-1]),
        "p05": r(_percentile(s, 0.05)),
        "p25": r(_percentile(s, 0.25)),
        "p75": r(_percentile(s, 0.75)),
        "p95": r(_percentile(s, 0.95)),
        "iqr": r(_percentile(s, 0.75) - _percentile(s, 0.25)),
        "range": r(s[-1] - s[0]),
        # 95% normal-approximation CI of the mean
        "ci95_low": r(mean - 1.96 * stderr),
        "ci95_high": r(mean + 1.96 * stderr),
        "cv_pct": r(100 * sd / mean) if mean else None,
    }


def histogram(values, lo, hi, bins):
    """Fixed-range histogram. Returns bins with edges, counts and percentages."""
    vals = [float(v) for v in values if v is not None]
    width = (hi - lo) / bins
    counts = [0] * bins
    for v in vals:
        if v < lo or v > hi:
            continue
        idx = int((v - lo) / width)
        if idx >= bins:      # right edge is inclusive in the final bin
            idx = bins - 1
        counts[idx] += 1
    total = len(vals) or 1
    return [
        {
            "lo": round(lo + i * width, 4),
            "hi": round(lo + (i + 1) * width, 4),
            "count": c,
            "pct": round(100 * c / total, 2),
        }
        for i, c in enumerate(counts)
    ]


# ---------------------------------------------------------------------------
# Risk frequency bucketing
# ---------------------------------------------------------------------------

# Boundaries are half-open on the low side so a bucket label is unambiguous:
# (0,25] low, (25,50] mid-low, (50,75] mid-high, (75,100] high.
RISK_BUCKETS = [
    ("low", "Low", 0, 25),
    ("mid_low", "Mid-Low", 25, 50),
    ("mid_high", "Mid-High", 50, 75),
    ("high", "High", 75, 100),
]


def bucket_for(pct):
    for key, label, lo, hi in RISK_BUCKETS:
        if pct <= hi:
            return key, label
    return "high", "High"


def aggregate(results, n_requested):
    """Aggregate N raw pipeline results into the deep-analysis report."""
    ok = [r for r in results if r]
    n = len(ok)
    if n == 0:
        return {"n_completed": 0, "n_requested": n_requested}

    # --- CDR score ---------------------------------------------------------
    scores = [(r.get("overview") or {}).get("medchem_score") for r in ok]
    scores = [s for s in scores if s is not None]

    # --- per-phase consensus probabilities and agent maxima ----------------
    # "the max probability of success the agents have" — per simulation, the most
    # optimistic individual agent for that phase, so the consensus can be read
    # against the ceiling the panel offered.
    agent_keys = {
        1: [("biology", "bio_p1"), ("toxicology", "tox_p1"),
            ("pharmacology", "pk_p1"), ("medchem", "chem_p1")],
        2: [("biology", "bio_p2"), ("toxicology", "tox_p2"),
            ("pharmacology", "pk_p2"), ("medchem", "chem_p2")],
        3: [("biology", "bio_p3"), ("toxicology", "tox_p3"),
            ("pharmacology", "pk_p3"), ("medchem", "chem_p3")],
    }

    phases = {}
    for phase in (1, 2, 3):
        consensus = []
        agent_max = []
        per_agent = {}
        for r in ok:
            cv = (r.get("overview") or {}).get(f"final_p{phase}")
            if cv is not None:
                consensus.append(cv)
            vals = []
            for section, field in agent_keys[phase]:
                v = (r.get(section) or {}).get(field)
                if v is not None:
                    vals.append(float(v))
                    per_agent.setdefault(section, []).append(float(v))
            if vals:
                agent_max.append(max(vals))

        phases[f"p{phase}"] = {
            "label": f"Phase {phase}",
            "consensus": describe(consensus),
            "consensus_hist": histogram(consensus, 0.0, 1.0, 20),
            "agent_max": describe(agent_max),
            "agent_max_hist": histogram(agent_max, 0.0, 1.0, 20),
            "per_agent_mean": {
                section: round(sum(v) / len(v), 4) for section, v in per_agent.items() if v
            },
            # How much the consensus sits below the most optimistic agent.
            "consensus_vs_agent_max_gap": (
                round(
                    (describe(agent_max).get("mean") or 0)
                    - (describe(consensus).get("mean") or 0),
                    4,
                )
                if consensus and agent_max
                else None
            ),
        }

    # --- TCSP --------------------------------------------------------------
    tcsps = [(r.get("overview") or {}).get("tcsp") for r in ok]
    tcsps = [t for t in tcsps if t is not None]

    # --- risk appearance frequency ----------------------------------------
    counter = {}
    for r in ok:
        for risk in extract_risks(r):
            counter[risk] = counter.get(risk, 0) + 1

    risks = []
    for name, count in counter.items():
        pct = round(100 * count / n, 2)
        key, label = bucket_for(pct)
        risks.append({
            "name": name,
            "count": count,
            "pct": pct,
            "bucket": key,
            "bucket_label": label,
        })
    # Most frequent first; ties alphabetical so the order is stable.
    risks.sort(key=lambda x: (-x["pct"], x["name"]))

    bucket_summary = []
    for key, label, lo, hi in RISK_BUCKETS:
        members = [x for x in risks if x["bucket"] == key]
        bucket_summary.append({
            "bucket": key,
            "label": label,
            "lo": lo,
            "hi": hi,
            "range_label": f"{lo}-{hi}%",
            "n_risks": len(members),
            "risks": [m["name"] for m in members],
        })

    # --- verdict frequencies ----------------------------------------------
    verdicts = {}
    for section in ("biology", "toxicology", "pharmacology"):
        tally = {}
        for r in ok:
            v = str((r.get(section) or {}).get("verdict", "")).strip().upper()
            if v:
                tally[v] = tally.get(v, 0) + 1
        verdicts[section] = [
            {"verdict": k, "count": c, "pct": round(100 * c / n, 2)}
            for k, c in sorted(tally.items(), key=lambda kv: -kv[1])
        ]

    return {
        "n_requested": n_requested,
        "n_completed": n,
        "n_failed": n_requested - n,
        "cdr": {
            "stats": describe(scores, digits=2),
            "hist": histogram(scores, 0, 100, 20),
        },
        "tcsp": {"stats": describe(tcsps, digits=6)},
        "phases": phases,
        "risks": risks,
        "risk_buckets": bucket_summary,
        "verdicts": verdicts,
        "fingerprints": [r.get("tsa_fingerprint") for r in ok if r.get("tsa_fingerprint")],
    }
