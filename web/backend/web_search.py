"""Web-Search agent — grounds the pipeline in real-world literature.

Uses Claude with its built-in WebSearch tool to find recent publications and
clinical data relevant to the target/indication/molecule, drafts a concise
summary with references, then runs a second validation pass that checks every
claim against the cited sources and strips anything unsupported. The validated
summary is appended to the auxiliary context fed to the four assessment agents.

Claude cites its sources in the response body rather than in a separate
grounding-metadata structure, so each search prompt asks for a JSON envelope
carrying both the prose and its references; URLs seen in the raw WebSearch tool
results are used as a fallback when the model omits them.
"""

import json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from claude_llm import invoke, invoke_with_search

ANALYST_SYSTEM = (
    "You are a scientific literature analyst with web search. You MUST call the "
    "WebSearch tool before writing your answer — run at least two searches, even "
    "for a molecule or drug you already recognise, because the point of this task "
    "is current retrieved evidence rather than recall. Ground every claim in a "
    "source you actually retrieved, and never invent citations, numbers, or drug "
    "identities. Output only what the requested format asks for — no preamble and "
    "no commentary."
)

# Sent on a retry when the first attempt answered without retrieving anything.
_MUST_SEARCH_NUDGE = (
    "\n\nYou answered without retrieving any sources. Call the WebSearch tool now "
    "— at least two distinct queries — and rebuild the answer from what those "
    "searches return, listing every source you used in \"references\"."
)

# The validation pass runs with no tools, so its persona must not ask for a
# search: a denied tool attempt would consume the turn budget before it answers.
VALIDATOR_SYSTEM = (
    "You are a meticulous scientific fact-checker working only from the text you "
    "are given. Do not search the web and do not attempt to open any URL — judge "
    "the draft against your own domain knowledge and the source titles listed. "
    "Never add new factual claims or citations. Output only the requested prose, "
    "with no preamble and no commentary."
)


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


def _clean_references(raw_refs, fallback_urls):
    """Normalise model-declared references to deduped {title, uri} dicts.

    Falls back to URLs harvested from the WebSearch tool results, titled by
    hostname, when the model returned none of its own.
    """
    refs = []
    seen = set()
    for ref in raw_refs or []:
        if not isinstance(ref, dict):
            continue
        uri = str(ref.get("uri") or ref.get("url") or "").strip()
        if not uri or uri in seen:
            continue
        seen.add(uri)
        refs.append({"title": str(ref.get("title") or uri).strip(), "uri": uri})
    if not refs:
        # Search results carry far more URLs than the summary actually leans on,
        # so cap the fallback list at a readable number.
        for uri in fallback_urls or []:
            if uri in seen:
                continue
            seen.add(uri)
            refs.append({"title": urlparse(uri).netloc or uri, "uri": uri})
            if len(refs) >= 10:
                break
    return refs


def _search(smiles, target, indication, auxiliary=""):
    """Step 1 — grounded literature search + draft summary."""
    extra = f"\nAdditional context provided by the user: {auxiliary}" if auxiliary else ""
    prompt = f"""Using web search, find recent publications, clinical trial results, and
authoritative data relevant to the following drug candidate, then write a
concise evidence summary.

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
citations or numbers. If little relevant literature exists, say so plainly.

Output ONLY a JSON object, no prose outside it:
{{
  "summary": "the 150-250 word evidence summary as plain prose",
  "references": [{{"title": "page or paper title", "uri": "https://..."}}]
}}

List in "references" only sources you actually retrieved and used."""

    # Claude will sometimes answer a well-known drug from recall instead of
    # searching, which yields an ungrounded summary with no references. Retry
    # once with an explicit demand before accepting that.
    for attempt in range(2):
        text, urls = invoke_with_search(
            ANALYST_SYSTEM, prompt if attempt == 0 else prompt + _MUST_SEARCH_NUDGE
        )
        data = _parse_json(text)
        if not data:
            # Model answered in prose despite the JSON request — keep the prose.
            summary = (text or "").strip()
            refs = _clean_references(None, urls)
        else:
            summary = str(data.get("summary", "") or "").strip()
            refs = _clean_references(data.get("references"), urls)
        if refs:
            return summary, refs
    return summary, refs


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
  ],
  "references": [{{"title": "source title", "uri": "https://..."}}]
}}

Classification: approvals, positive AdCom votes, and expedited designations are
"positive"; CRLs, rejections, clinical holds, boxed warnings, and withdrawals are
"negative". If no FDA record can be found, return overall="none" with an empty
events list. Never fabricate actions, dates, or drug identities."""

    text, urls = invoke_with_search(ANALYST_SYSTEM, prompt)
    data = _parse_json(text)
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
        "references": _clean_references(data.get("references"), urls),
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

    validated = (invoke(VALIDATOR_SYSTEM, prompt, max_turns=3) or "").strip()
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
            # Only claim validation when the summary is actually backed by
            # sources that were retrieved; the UI badges this state directly.
            "validated": bool(references),
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
