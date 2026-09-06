"""Catalog of the Vertex AI models the pipeline can run on.

Every entry here was probed against this project's Vertex endpoints and answered
a live request, so the picker only ever offers models that actually work.

Fields
------
id            Model identifier passed to Vertex. For MaaS models this is the
              full ``publisher/model`` string the OpenAI-compatible endpoint wants.
transport     "gemini" -> native Gemini API via ChatVertexAI.
              "maas"   -> serverless open/partner model via the OpenAI-compatible
                          ``endpoints/openapi/chat/completions`` endpoint.
location      Vertex location that serves the model ("global" for most).
price_in /    USD per 1M tokens, standard (non-batch, non-priority) rate, taken
price_out     verbatim from https://cloud.google.com/vertex-ai/generative-ai/pricing.
              Gemini prices are the <= 200K input-token tier.
context       Context window in tokens.
data_freeze   Vendor-published training-data cutoff, or None where the vendor has
              not published one (rendered as "not published" in the UI).
grounding     True if the model can run the Google Search-grounded web-search agent.
open_source   True if the weights are published and the model can be self-hosted;
              False for API-only models (Gemini, Grok).
"""

# Token profile of one full evaluation: five agent calls (four in parallel plus
# the MedChem Pass 2 synthesis). Input is measured from the four system prompts
# (~8k tokens) plus the Pass 2 message that re-sends every advisory. Output is
# dominated by reasoning tokens, and is set so the default model lands on the
# observed ~$0.30 per evaluation: 13_300 * $2.00/M + 22_800 * $12.00/M = $0.30.
# Costs for other models scale from this same profile, so they are comparative
# estimates, not quotes — a model that reasons more or less will differ.
EVAL_INPUT_TOKENS = 13_300
EVAL_OUTPUT_TOKENS = 22_800

# These three head the picker in this order; everything else follows sorted by
# price_in + price_out, cheapest first.
PINNED_MODEL_IDS = [
    "gemini-3.1-pro-preview",
    "openai/gpt-oss-20b-maas",
    "google/gemma-4-26b-a4b-it-maas",
]
DEFAULT_MODEL_ID = PINNED_MODEL_IDS[0]

MODELS = [
    # ---- Google Gemini -----------------------------------------------------
    {
        "id": "gemini-3.1-pro-preview",
        "label": "Gemini 3.1 Pro (Preview)",
        "family": "Google Gemini",
        "transport": "gemini",
        "location": "global",
        "price_in": 2.00,
        "price_out": 12.00,
        "context": 1_048_576,
        "data_freeze": "Jan 2025",
        "open_source": False,
        "grounding": True,
        "note": "Current default. Strongest reasoning; highest cost.",
    },
    {
        "id": "gemini-3.8-flash",
        "label": "Gemini 3.8 Flash",
        "family": "Google Gemini",
        "transport": "gemini",
        "location": "global",
        "price_in": 0.75,
        "price_out": 3.75,
        "context": 1_048_576,
        "data_freeze": "Mar 2026",
        "open_source": False,
        "grounding": True,
        "note": "Introductory pricing through 31 Dec 2026; doubles on 1 Jan 2027.",
    },
    {
        "id": "gemini-3.7-flash",
        "label": "Gemini 3.7 Flash",
        "family": "Google Gemini",
        "transport": "gemini",
        "location": "global",
        "price_in": 0.75,
        "price_out": 3.75,
        "context": 1_048_576,
        "data_freeze": "Mar 2026",
        "open_source": False,
        "grounding": True,
        "note": "Introductory pricing through 31 Dec 2026; doubles on 1 Jan 2027.",
    },
    {
        "id": "gemini-3.6-flash",
        "label": "Gemini 3.6 Flash",
        "family": "Google Gemini",
        "transport": "gemini",
        "location": "global",
        "price_in": 0.75,
        "price_out": 3.75,
        "context": 1_048_576,
        "data_freeze": "Mar 2026",
        "open_source": False,
        "grounding": True,
        "note": "Introductory pricing through 31 Dec 2026; doubles on 1 Jan 2027.",
    },
    {
        "id": "gemini-3.5-flash",
        "label": "Gemini 3.5 Flash",
        "family": "Google Gemini",
        "transport": "gemini",
        "location": "global",
        "price_in": 1.50,
        "price_out": 9.00,
        "context": 1_048_576,
        "data_freeze": "Jan 2025",
        "open_source": False,
        "grounding": True,
        "note": "",
    },
    {
        "id": "gemini-3.5-flash-lite",
        "label": "Gemini 3.5 Flash-Lite",
        "family": "Google Gemini",
        "transport": "gemini",
        "location": "global",
        "price_in": 0.30,
        "price_out": 2.50,
        "context": 1_048_576,
        "data_freeze": "Mar 2026",
        "open_source": False,
        "grounding": True,
        "note": "",
    },
    {
        "id": "gemini-3.1-flash-lite",
        "label": "Gemini 3.1 Flash-Lite",
        "family": "Google Gemini",
        "transport": "gemini",
        "location": "global",
        "price_in": 0.25,
        "price_out": 1.50,
        "context": 1_048_576,
        "data_freeze": "Jan 2025",
        "open_source": False,
        "grounding": True,
        "note": "",
    },
    {
        "id": "gemini-2.5-pro",
        "label": "Gemini 2.5 Pro",
        "family": "Google Gemini",
        "transport": "gemini",
        "location": "global",
        "price_in": 1.25,
        "price_out": 10.00,
        "context": 1_048_576,
        "data_freeze": "Jan 2025",
        "open_source": False,
        "grounding": True,
        "note": "",
    },
    {
        "id": "gemini-2.5-flash",
        "label": "Gemini 2.5 Flash",
        "family": "Google Gemini",
        "transport": "gemini",
        "location": "global",
        "price_in": 0.30,
        "price_out": 2.50,
        "context": 1_048_576,
        "data_freeze": "Jan 2025",
        "open_source": False,
        "grounding": True,
        "note": "",
    },
    {
        "id": "gemini-2.5-flash-lite",
        "label": "Gemini 2.5 Flash-Lite",
        "family": "Google Gemini",
        "transport": "gemini",
        "location": "global",
        "price_in": 0.10,
        "price_out": 0.40,
        "context": 1_048_576,
        "data_freeze": "Jan 2025",
        "open_source": False,
        "grounding": True,
        "note": "Cheapest option overall.",
    },

    # ---- Open-weight models (serverless MaaS) ------------------------------
    {
        "id": "google/gemma-4-26b-a4b-it-maas",
        "label": "Gemma 4 26B A4B IT",
        "family": "Google Gemma",
        "transport": "maas",
        "location": "global",
        "price_in": 0.15,
        "price_out": 0.60,
        "context": 262_144,
        "data_freeze": None,
        "open_source": True,
        "grounding": False,
        "note": "Google's open-weight MoE, 26B total / 4B active.",
    },
    {
        "id": "openai/gpt-oss-20b-maas",
        "label": "gpt-oss 20B",
        "family": "OpenAI",
        "transport": "maas",
        "location": "global",
        "price_in": 0.07,
        "price_out": 0.25,
        "context": 131_072,
        "data_freeze": "Jun 2024",
        "open_source": True,
        "grounding": False,
        "note": "Smallest and cheapest open-weight option.",
    },
    {
        "id": "openai/gpt-oss-120b-maas",
        "label": "gpt-oss 120B",
        "family": "OpenAI",
        "transport": "maas",
        "location": "global",
        "price_in": 0.09,
        "price_out": 0.36,
        "context": 131_072,
        "data_freeze": "Jun 2024",
        "open_source": True,
        "grounding": False,
        "note": "",
    },
    {
        "id": "qwen/qwen3-next-80b-a3b-instruct-maas",
        "label": "Qwen3 Next 80B A3B Instruct",
        "family": "Qwen",
        "transport": "maas",
        "location": "global",
        "price_in": 0.15,
        "price_out": 1.20,
        "context": 262_144,
        "data_freeze": None,
        "open_source": True,
        "grounding": False,
        "note": "",
    },
    {
        "id": "qwen/qwen3-next-80b-a3b-thinking-maas",
        "max_tokens": 32768,
        "label": "Qwen3 Next 80B A3B Thinking",
        "family": "Qwen",
        "transport": "maas",
        "location": "global",
        "price_in": 0.15,
        "price_out": 1.20,
        "context": 262_144,
        "data_freeze": None,
        "open_source": True,
        "grounding": False,
        "note": "Reasoning variant of Qwen3 Next 80B.",
    },
    {
        "id": "qwen/qwen3-235b-a22b-instruct-2507-maas",
        "label": "Qwen3 235B A22B Instruct",
        "family": "Qwen",
        "transport": "maas",
        "location": "global",
        "price_in": 0.22,
        "price_out": 0.88,
        "context": 262_144,
        "data_freeze": None,
        "open_source": True,
        "grounding": False,
        "note": "",
    },
    {
        "id": "qwen/qwen3-coder-480b-a35b-instruct-maas",
        "label": "Qwen3 Coder 480B A35B",
        "family": "Qwen",
        "transport": "maas",
        "location": "global",
        "price_in": 0.22,
        "price_out": 1.80,
        "context": 262_144,
        "data_freeze": None,
        "open_source": True,
        "grounding": False,
        "note": "Coding-tuned; not recommended for chemistry reasoning.",
    },
    {
        "id": "deepseek-ai/deepseek-r1-0528-maas",
        "max_tokens": 32768,
        "label": "DeepSeek-R1 (0528)",
        "family": "DeepSeek",
        "transport": "maas",
        "location": "us-central1",
        "price_in": 1.35,
        "price_out": 5.40,
        "context": 163_840,
        "data_freeze": "Mar 2025",
        "open_source": True,
        "grounding": False,
        "note": "Served from us-central1, not global.",
    },
    {
        "id": "minimaxai/minimax-m2-maas",
        "max_tokens": 32768,
        "label": "MiniMax-M2",
        "family": "MiniMax",
        "transport": "maas",
        "location": "global",
        "price_in": 0.30,
        "price_out": 1.20,
        "context": 204_800,
        "data_freeze": None,
        "open_source": True,
        "grounding": False,
        "note": "",
    },
    {
        "id": "zai-org/glm-4.7-maas",
        "max_tokens": 32768,
        "label": "GLM-4.7",
        "family": "Z.ai GLM",
        "transport": "maas",
        "location": "global",
        "price_in": 0.60,
        "price_out": 2.20,
        "context": 204_800,
        "data_freeze": None,
        "open_source": True,
        "grounding": False,
        "note": "",
    },
    {
        "id": "zai-org/glm-5-maas",
        "max_tokens": 32768,
        "label": "GLM-5",
        "family": "Z.ai GLM",
        "transport": "maas",
        "location": "global",
        "price_in": 1.00,
        "price_out": 3.20,
        "context": 204_800,
        "data_freeze": None,
        "open_source": True,
        "grounding": False,
        "note": "",
    },
    {
        "id": "zai-org/glm-5.2-maas",
        "max_tokens": 32768,
        "label": "GLM-5.2",
        "family": "Z.ai GLM",
        "transport": "maas",
        "location": "global",
        "price_in": 1.40,
        "price_out": 4.40,
        "context": 1_048_576,
        "data_freeze": None,
        "open_source": True,
        "grounding": False,
        "note": "",
    },

    # ---- Partner models ----------------------------------------------------
    {
        "id": "xai/grok-4.1-fast-reasoning",
        "max_tokens": 32768,
        "label": "Grok 4.1 Fast (Reasoning)",
        "family": "xAI Grok",
        "transport": "maas",
        "location": "global",
        "price_in": 0.20,
        "price_out": 0.50,
        "context": 2_000_000,
        "data_freeze": None,
        "open_source": False,
        "grounding": False,
        "note": "Largest context window on offer.",
    },
    {
        "id": "xai/grok-4.1-fast-non-reasoning",
        "label": "Grok 4.1 Fast (Non-Reasoning)",
        "family": "xAI Grok",
        "transport": "maas",
        "location": "global",
        "price_in": 0.20,
        "price_out": 0.50,
        "context": 2_000_000,
        "data_freeze": None,
        "open_source": False,
        "grounding": False,
        "note": "",
    },
]

_BY_ID = {m["id"]: m for m in MODELS}


def get_model(model_id: str) -> dict:
    """Look up a model by id, falling back to the default for unknown ids."""
    return _BY_ID.get(model_id) or _BY_ID[DEFAULT_MODEL_ID]


def is_known(model_id: str) -> bool:
    return model_id in _BY_ID


def eval_cost(model: dict) -> float:
    """Approximate USD for one full evaluation on this model."""
    return (EVAL_INPUT_TOKENS * model["price_in"]
            + EVAL_OUTPUT_TOKENS * model["price_out"]) / 1_000_000


def _fmt_cost(usd: float) -> str:
    if usd < 0.01:
        return f"${usd:.3f}"
    return f"${usd:.2f}"


def _fmt_context(tokens: int) -> str:
    if tokens >= 1_000_000:
        return f"{tokens / 1_048_576:.0f}M" if tokens % 1_048_576 == 0 else f"{tokens / 1_000_000:.1f}M"
    return f"{round(tokens / 1024)}K"


def catalog() -> list:
    """UI-ready list: the pinned models first, then cheapest to most expensive."""
    rest = sorted(
        (m for m in MODELS if m["id"] not in PINNED_MODEL_IDS),
        key=lambda m: (m["price_in"] + m["price_out"], m["label"]),
    )
    ordered = [_BY_ID[i] for i in PINNED_MODEL_IDS if i in _BY_ID] + rest
    return [
        {
            "id": m["id"],
            "label": m["label"],
            "family": m["family"],
            "price_in": m["price_in"],
            "price_out": m["price_out"],
            "context": m["context"],
            "context_label": _fmt_context(m["context"]),
            "data_freeze": m["data_freeze"] or "not published",
            "open_source": m["open_source"],
            "cost_per_eval": round(eval_cost(m), 4),
            "cost_label": _fmt_cost(eval_cost(m)),
            "grounding": m["grounding"],
            "note": m["note"],
            "is_default": m["id"] == DEFAULT_MODEL_ID,
        }
        for m in ordered
    ]
