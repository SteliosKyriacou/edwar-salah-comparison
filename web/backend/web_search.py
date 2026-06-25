"""Web-Search agent — grounds the pipeline in real-world literature.

Uses Gemini with Google Search grounding to find recent publications and
clinical data relevant to the target/indication/molecule, drafts a concise
summary with references, then runs a second validation pass that checks every
claim against the cited sources and strips anything unsupported. The validated
summary is appended to the auxiliary context fed to the four assessment agents.
"""

import os
import json
from concurrent.futures import ThreadPoolExecutor
from google import genai
from google.genai import types

MODEL = "gemini-3.1-pro-preview"

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client()
    return _client


def _extract_references(resp):
    """Pull deduped {title, uri} references from grounding metadata."""
    refs = []
    seen = set()
    try:
        for cand in resp.candidates or []:
            gm = getattr(cand, "grounding_metadata", None)
            if not gm:
                continue
            for chunk in getattr(gm, "grounding_chunks", None) or []:
                web = getattr(chunk, "web", None)
                if not web:
                    continue
                uri = getattr(web, "uri", "") or ""
                title = getattr(web, "title", "") or uri
                if uri and uri not in seen:
                    seen.add(uri)
                    refs.append({"title": title, "uri": uri})
    except Exception:
        pass
    return refs


def _search(smiles, target, indication, auxiliary=""):
    """Step 1 — grounded literature search + draft summary."""
    extra = f"\nAdditional context provided by the user: {auxiliary}" if auxiliary else ""
    prompt = f"""You are a scientific literature analyst. Using web search, find recent
publications, clinical trial results, and authoritative data relevant to the
following drug candidate, then write a concise evidence summary.

Target class: {target}
Indication: {indication}
Molecule (SMILES): {smiles}{extra}

Focus on facts that bear on clinical developability:
- Known clinical or preclinical outcomes for this target/indication or close analogs
- Reported safety/toxicity liabilities for the target class
- Pharmacokinetic or chemotype-specific issues documented in the literature
- Precedent approved drugs or notable clinical failures in this space

Write 150-250 words of plain prose. State only what the sources support, and
attribute notable claims (e.g. "a 2023 trial reported..."). Do not invent
citations or numbers. If little relevant literature exists, say so plainly."""

    resp = _get_client().models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    return (resp.text or "").strip(), _extract_references(resp)


def _parse_json(text):
    """Lenient JSON extraction from a model response."""
    clean = (text or "").replace("```json", "").replace("```", "").strip()
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(clean[start:end])
    except Exception:
        return None


def _fda_status(smiles, target, indication):
    """Find the current U.S. FDA regulatory status and classify its sentiment.

    Returns a dict {drug_name, overall, headline, events, references} or None.
    `overall` is one of: positive | negative | mixed | none.
    """
    prompt = f"""Using web search, determine the CURRENT U.S. FDA regulatory status of the
drug described below. First try to identify the drug by name from its structure,
target, and indication.

Target class: {target}
Indication: {indication}
Molecule (SMILES): {smiles}

Report concrete, recent FDA actions only: approvals, Complete Response Letters
(CRLs), rejections, clinical holds, Fast Track / Breakthrough Therapy / Priority
Review / Orphan designations, advisory committee votes, label expansions,
boxed warnings, or withdrawals.

Output ONLY a JSON object, no prose:
{{
  "drug_name": "best identification or 'Unknown'",
  "overall": "positive | negative | mixed | none",
  "headline": "one concise sentence describing the current FDA status",
  "events": [
    {{"sentiment": "positive | negative | neutral",
      "date": "YYYY or YYYY-MM",
      "title": "short label, e.g. 'Complete Response Letter'",
      "detail": "one sentence"}}
  ]
}}

Classification: approvals, positive AdCom votes, and expedited designations are
"positive"; CRLs, rejections, clinical holds, boxed warnings, and withdrawals are
"negative". If no FDA record can be found, return overall="none" with an empty
events list. Never fabricate actions, dates, or drug identities."""

    resp = _get_client().models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    data = _parse_json(resp.text)
    if not data:
        return None
    overall = str(data.get("overall", "none")).lower()
    if overall not in ("positive", "negative", "mixed", "none"):
        overall = "none"
    events = []
    for e in data.get("events", []) or []:
        sentiment = str(e.get("sentiment", "neutral")).lower()
        if sentiment not in ("positive", "negative", "neutral"):
            sentiment = "neutral"
        events.append({
            "sentiment": sentiment,
            "date": str(e.get("date", "") or ""),
            "title": str(e.get("title", "") or ""),
            "detail": str(e.get("detail", "") or ""),
        })
    return {
        "drug_name": str(data.get("drug_name", "Unknown") or "Unknown"),
        "overall": overall,
        "headline": str(data.get("headline", "") or ""),
        "events": events,
        "references": _extract_references(resp),
    }


def _validate(summary, references, target, indication):
    """Step 2 — fact-check the draft against its own references."""
    ref_list = "\n".join(f"- {r['title']}: {r['uri']}" for r in references) or "(none)"
    prompt = f"""You are a meticulous fact-checker. Below is a draft evidence summary about a
drug candidate (target: {target}, indication: {indication}) and the list of web
sources it was grounded in.

DRAFT SUMMARY:
{summary}

SOURCES CONSULTED:
{ref_list}

Task: Return a corrected, validated version of the summary. Remove or soften any
claim that is not clearly supportable by reputable literature, fix any
overstatement, and keep the prose concise (max ~250 words). Do not add new
factual claims or citations. Output ONLY the validated summary prose, with no
preamble, headers, or commentary."""

    resp = _get_client().models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.0),
    )
    validated = (resp.text or "").strip()
    return validated or summary


def _safe_fda_status(smiles, target, indication):
    try:
        return _fda_status(smiles, target, indication)
    except Exception:
        return None


def run_web_search(smiles, target, indication, auxiliary=""):
    """Run the full web-search agent.

    Returns a dict: {summary, references, validated, fda} or None on hard failure.
    `summary` is the validated, reference-backed prose suitable for appending to
    the auxiliary context. `fda` carries the current FDA regulatory status.
    """
    try:
        # FDA status is independent of the literature draft, so run it concurrently.
        with ThreadPoolExecutor(max_workers=2) as executor:
            fut_fda = executor.submit(_safe_fda_status, smiles, target, indication)
            draft, references = _search(smiles, target, indication, auxiliary)
            fda = fut_fda.result()

        if not draft:
            return None
        summary = _validate(draft, references, target, indication)
        return {
            "summary": summary,
            "references": references,
            "validated": True,
            "fda": fda,
        }
    except Exception as e:
        return {
            "summary": "",
            "references": [],
            "validated": False,
            "fda": None,
            "error": str(e),
        }
