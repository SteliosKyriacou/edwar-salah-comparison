"""Single entry point for talking to any model in the catalog.

Gemini models go through ChatVertexAI as before. Open-weight and partner models
are served by Vertex as MaaS and only speak the OpenAI-compatible
``endpoints/openapi/chat/completions`` API, so they are called over plain HTTP
with an Application Default Credentials bearer token — no extra SDK needed.
"""

import os
import random
import threading
import time

import google.auth
import google.auth.transport.requests
import requests
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import SystemMessage, HumanMessage

from models_catalog import get_model

_MAAS_TIMEOUT = 600
# Reasoning models bill their scratchpad against this budget, so it has to be
# generous or the JSON answer gets truncated away. Per-model overrides live in
# the catalog's `max_tokens`.
_MAAS_MAX_TOKENS = 16384
# Shared MaaS models are capacity-limited and answer 429/503 under load; the
# pipeline fires four agent calls at once, so back off and retry rather than
# failing the whole evaluation.
_MAAS_RETRY_STATUS = (429, 503)
_MAAS_MAX_ATTEMPTS = 5
# Note: do NOT send response_format={"type": "json_object"} here. gpt-oss
# degenerates into repeated "cjson2json" tokens under constrained decoding, and
# parse_json in agents.py already copes with fences, <think> blocks and trailing
# prose, which is what the parameter would have bought.

_llm_cache = {}
_llm_lock = threading.Lock()

_credentials = None
_cred_lock = threading.Lock()


def _project():
    return os.environ.get("GOOGLE_CLOUD_PROJECT", "ai-pipeline-461818")


def _gemini_location():
    return os.environ.get("GOOGLE_CLOUD_LOCATION", "global")


def _get_chat_model(model_id: str) -> ChatVertexAI:
    """One ChatVertexAI client per model, created on first use."""
    with _llm_lock:
        if model_id not in _llm_cache:
            _llm_cache[model_id] = ChatVertexAI(
                model=model_id,
                temperature=0.0,
                project=_project(),
                location=_gemini_location(),
            )
        return _llm_cache[model_id]


def _access_token() -> str:
    """ADC access token, refreshed when it expires."""
    global _credentials
    with _cred_lock:
        if _credentials is None:
            _credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        if not _credentials.valid:
            _credentials.refresh(google.auth.transport.requests.Request())
        return _credentials.token


def _invoke_maas(model: dict, system: str, user: str) -> str:
    location = model["location"]
    host = ("aiplatform.googleapis.com" if location == "global"
            else f"{location}-aiplatform.googleapis.com")
    url = (f"https://{host}/v1/projects/{_project()}/locations/{location}"
           f"/endpoints/openapi/chat/completions")

    payload = {
        "model": model["id"],
        "temperature": 0.0,
        "max_tokens": model.get("max_tokens", _MAAS_MAX_TOKENS),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    resp = None
    for attempt in range(_MAAS_MAX_ATTEMPTS):
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {_access_token()}",
                     "Content-Type": "application/json"},
            json=payload,
            timeout=_MAAS_TIMEOUT,
        )
        if resp.ok:
            break
        if resp.status_code not in _MAAS_RETRY_STATUS or attempt == _MAAS_MAX_ATTEMPTS - 1:
            break
        retry_after = resp.headers.get("Retry-After")
        try:
            delay = float(retry_after)
        except (TypeError, ValueError):
            delay = (2 ** attempt) + random.uniform(0, 1)
        time.sleep(min(delay, 30))

    if not resp.ok:
        detail = ("is at capacity right now — try again shortly or pick another model"
                  if resp.status_code in _MAAS_RETRY_STATUS
                  else resp.text[:300])
        raise RuntimeError(
            f"Vertex call to {model['id']} failed ({resp.status_code}): {detail}"
        )
    choices = resp.json().get("choices") or []
    if not choices:
        raise RuntimeError(f"Vertex MaaS call to {model['id']} returned no choices")
    # Reasoning models return the answer in `content` and their scratchpad in
    # `reasoning_content`; only the answer is wanted here.
    content = ((choices[0].get("message") or {}).get("content") or "").strip()
    if not content:
        reason = choices[0].get("finish_reason", "unknown")
        raise RuntimeError(
            f"{model['label']} returned an empty answer (finish_reason={reason}). "
            "Reasoning models can spend their whole output budget thinking — "
            "try again or pick another model."
        )
    return content


def invoke(model_id: str, system: str, user: str) -> str:
    """Run one system+user turn against `model_id` and return the text reply."""
    model = get_model(model_id)
    if model["transport"] == "gemini":
        resp = _get_chat_model(model["id"]).invoke(
            [SystemMessage(content=system), HumanMessage(content=user)]
        )
        content = resp.content
        if isinstance(content, list):
            content = "".join(
                str(c.get("text", "")) if isinstance(c, dict) else str(c)
                for c in content
            )
        return content
    return _invoke_maas(model, system, user)
