"""Claude adapter — routes every agent call through the Claude Agent SDK.

Auth is Claude Code's own subscription login: the SDK drives the `claude` CLI as
a subprocess, which carries the credentials. No ANTHROPIC_API_KEY is read, set,
or required anywhere in this app.

The pipeline in agents.py is synchronous and fans out over a ThreadPoolExecutor,
so this module exposes plain blocking functions and owns the async bridge.
"""

import asyncio
import os
import re
import threading

import json
from datetime import datetime

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    UserMessage,
    query,
)

# Token accounting. Every call draws on the Claude subscription shared by whoever
# runs this server, so each one is tallied in-process and appended to a log the
# team can inspect.
_USAGE_LOG = os.path.join(os.path.dirname(__file__), "..", "logs", "usage.jsonl")
_usage_lock = threading.Lock()
_usage_total = {
    "calls": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0,
}


def _resolved_models(result):
    """Actual model IDs that served the call (MODEL is only an alias like 'sonnet')."""
    out = {}
    for model_id, usage in (result.model_usage or {}).items():
        if hasattr(usage, "__dict__"):
            out[model_id] = {k: v for k, v in vars(usage).items()
                             if isinstance(v, (int, float, str))}
        elif isinstance(usage, dict):
            out[model_id] = usage
        else:
            out[model_id] = str(usage)
    return out


def _record_usage(label, result):
    """Tally one call's tokens and append a line to logs/usage.jsonl."""
    usage = result.usage or {}
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "label": label,
        "model": MODEL,
        "resolved_models": _resolved_models(result),
        "num_turns": result.num_turns,
        "duration_api_ms": result.duration_api_ms,
        "input_tokens": usage.get("input_tokens", 0) or 0,
        "output_tokens": usage.get("output_tokens", 0) or 0,
        "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0) or 0,
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0) or 0,
    }
    with _usage_lock:
        _usage_total["calls"] += 1
        for key in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                    "cache_creation_input_tokens"):
            _usage_total[key] += entry[key]
        try:
            os.makedirs(os.path.dirname(_USAGE_LOG), exist_ok=True)
            with open(_USAGE_LOG, "a") as fh:
                fh.write(json.dumps(entry) + "\n")
        except OSError:
            pass  # never fail a prediction over telemetry
    return entry


def usage_total():
    """Cumulative token usage since this process started."""
    with _usage_lock:
        return dict(_usage_total)

MODEL = os.environ.get("CLAUDE_MODEL", "sonnet")

# This app is deliberately subscription-only. Claude Code prefers an API key over
# the OAuth login whenever one is present, which would silently move inference
# onto metered API billing — so refuse to run rather than let that happen quietly.
_API_KEY_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
_present = [v for v in _API_KEY_VARS if os.environ.get(v)]
if _present:
    raise RuntimeError(
        f"{', '.join(_present)} is set in this environment. This backend runs on the "
        "Claude Code subscription login only; an API key would take precedence and "
        "bill through the API instead. Unset it before starting the server."
    )

# Matches the source URLs that come back inside WebSearch tool results.
_URL_RE = re.compile(r"https?://[^\s\)\]\"'<>]+")


def _options(system, tools, allowed_tools, max_turns):
    """Build options.

    `tools` is the toolset the model can see, `allowed_tools` the subset that is
    pre-approved. Pass `tools=[]` to expose nothing at all; pass `tools=None` to
    keep the default toolset (the only way the built-in WebSearch is actually
    reachable) and rely on `allowed_tools` plus `permission_mode` to gate it.
    """
    kwargs = dict(
        system_prompt=system,
        model=MODEL,
        allowed_tools=list(allowed_tools),
        max_turns=max_turns,
        # Ignore repo-level CLAUDE.md / settings / skills: the agent personas are
        # defined solely by Agents/*/INSTRUCTIONS.md and must not inherit
        # unrelated project instructions.
        setting_sources=[],
        # Non-interactive server context — never block on a permission prompt.
        permission_mode="dontAsk",
    )
    if tools is not None:
        kwargs["tools"] = list(tools)
    return ClaudeAgentOptions(**kwargs)


async def _acall(system, user, tools, allowed_tools, max_turns, label="agent"):
    """Return (assistant_text, harvested_urls) for one system+user exchange."""
    parts = []
    urls = []
    async for message in query(
        prompt=user, options=_options(system, tools, allowed_tools, max_turns)
    ):
        if isinstance(message, ResultMessage):
            _record_usage(label, message)
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)
        elif isinstance(message, UserMessage):
            # Tool results (e.g. WebSearch) are delivered back as user messages.
            for block in message.content:
                if isinstance(block, ToolResultBlock) and not block.is_error:
                    urls.extend(_result_urls(block.content))
    return "".join(parts), urls


def _result_urls(content):
    """Pull URLs out of a tool result.

    WebSearch results arrive as a list of plain strings (occasionally dicts),
    not TextBlock objects, so this handles all three shapes — reading only the
    `.text` attribute would silently harvest nothing.
    """
    if content is None:
        return []
    if isinstance(content, str):
        return _URL_RE.findall(content)
    found = []
    for inner in content:
        if isinstance(inner, str):
            text = inner
        elif isinstance(inner, dict):
            text = str(inner.get("text") or "")
        else:
            text = str(getattr(inner, "text", "") or "")
        if text:
            found.extend(_URL_RE.findall(text))
    return found


def _run_sync(coro):
    """Run a coroutine to completion from synchronous (possibly threaded) code."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # Already inside an event loop — hand off to a thread with its own loop.
    box = {}

    def runner():
        try:
            box["value"] = asyncio.run(coro)
        except BaseException as exc:  # re-raised on the calling thread below
            box["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()
    if "error" in box:
        raise box["error"]
    return box["value"]


def invoke(system, user, max_turns=1):
    """Call with an empty toolset — the shape all four assessment agents use.

    One turn is enough: with no tools exposed the model answers in a single
    assistant message, which also keeps the JSON in one text block.
    """
    text, _ = _run_sync(
        _acall(system, user, tools=[], allowed_tools=(), max_turns=max_turns,
               label="agent")
    )
    return text


def invoke_with_search(system, user, max_turns=12):
    """Call with web search enabled. Returns (text, urls_seen_in_search_results).

    Keeps the default toolset so WebSearch is reachable; only the two search
    tools are pre-approved, and anything else the model reaches for is denied.
    """
    return _run_sync(
        _acall(
            system,
            user,
            tools=None,
            allowed_tools=("WebSearch", "WebFetch"),
            max_turns=max_turns,
            label="websearch",
        )
    )
