from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

_ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(_ENV_PATH)

# ==================== PROVIDER IMPORTS ====================

try:
    from .providers import (  # type: ignore
        GroqProvider,
        GeminiProvider,
        MistralProvider,
        CerebrasProvider,
        CohereProvider,
        HuggingFaceProvider,
    )
except Exception:
    try:
        from server.providers import (  # type: ignore
            GroqProvider,
            GeminiProvider,
            MistralProvider,
            CerebrasProvider,
            CohereProvider,
            HuggingFaceProvider,
        )
    except Exception:
        from providers import (  # type: ignore
            GroqProvider,
            GeminiProvider,
            MistralProvider,
            CerebrasProvider,
            CohereProvider,
            HuggingFaceProvider,
        )

# ==================== SETTINGS ====================

# Circuit breaker state (in-memory, per-process)
PROVIDER_STATE: Dict[str, Dict[str, float]] = {}

CIRCUIT_FAILS = int(os.getenv("CIRCUIT_FAILS", "3"))
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "60"))

DEFAULT_MAX_RETRIES = int(os.getenv("PROVIDER_MAX_RETRIES", "2"))
HARD_DEADLINE_BUFFER_S = int(os.getenv("HARD_DEADLINE_BUFFER_S", "10"))

# Synthesis
SYNTH_TIMEOUT_S = int(os.getenv("SYNTH_TIMEOUT_S", "30"))
SYNTH_MAX_CHARS_PER_PROVIDER = int(os.getenv("SYNTH_MAX_CHARS_PER_PROVIDER", "1800"))

# Errors
ERROR_MAX_CHARS = int(os.getenv("ERROR_MAX_CHARS", "140"))

# Only transient errors should be retried / trip the circuit breaker
RETRYABLE_ERROR_TYPES = {"timeout", "rate_limited", "provider_down"}
BREAKABLE_ERROR_TYPES = {"timeout", "rate_limited", "provider_down"}


def _safe_str(x: Any) -> str:
    return (x or "").strip() if isinstance(x, str) else str(x or "").strip()


def _short_error(msg: str) -> str:
    """
    Convert noisy provider errors like:
      'HTTP 404: {"error":{"message":"..."}}'
    into short messages.
    """
    if not msg:
        return ""
    s = msg.replace("\n", " ").replace("\r", " ").strip()

    # If it's "HTTP NNN: {json...}", try parsing the JSON part
    json_candidate = s
    if s.startswith("HTTP "):
        parts = s.split(":", 1)
        if len(parts) == 2:
            json_candidate = parts[1].strip()

    try:
        j = json.loads(json_candidate)
        if isinstance(j, dict):
            if isinstance(j.get("error"), dict) and isinstance(j["error"].get("message"), str):
                s = j["error"]["message"].strip()
            elif isinstance(j.get("message"), str):
                s = j["message"].strip()
            elif isinstance(j.get("detail"), str):
                s = j["detail"].strip()
    except Exception:
        pass

    for prefix in (
        "HTTP 400:", "HTTP 401:", "HTTP 403:", "HTTP 404:", "HTTP 429:",
        "HTTP 500:", "HTTP 502:", "HTTP 503:", "HTTP 504:",
    ):
        if s.startswith(prefix):
            s = s[len(prefix):].strip()

    s = s.replace("  ", " ").strip()
    return (s[:ERROR_MAX_CHARS] + "…") if len(s) > ERROR_MAX_CHARS else s


def _cooldown_message(until_ts: float) -> str:
    remaining = max(0, int(until_ts - time.time()))
    return f"Circuit open; retry in {remaining}s"


def generate_query_hash(user_id: int, query_text: str, agent_ids: List[str]) -> str:
    content = f"{user_id}:{query_text}:{'|'.join(sorted(agent_ids))}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ==================== PROVIDER REGISTRY ====================

_enabled_env = (os.getenv("ENABLED_PROVIDERS") or "").strip()
ENABLED_PROVIDERS = {p.strip() for p in _enabled_env.split(",") if p.strip()} or None
PROVIDER_INIT_ERRORS: Dict[str, str] = {}
PROVIDER_MISSING_KEYS: set[str] = set()

# IMPORTANT:
# - Gemini models: use official ids from Google docs (e.g. gemini-1.5-flash-latest, gemini-2.5-flash). [web:32]
# - Cohere command-r was removed; use recommended replacements like command-r-08-2024, command-r-plus-08-2024, command-a-03-2025. [web:1]
PROVIDER_CONFIGS = {
    "groq": {
        "class": GroqProvider,
        "api_key_env": "GROQ_API_KEY",
        "default_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "name": "Groq",
        "tier": "free",
        "quota": "14.4K req/day",
    },
    "gemini": {
        "class": GeminiProvider,
        "api_key_env": "GEMINI_API_KEY",
        "default_model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest"),
        "name": "Google Gemini",
        "tier": "free",
        "quota": "60 req/min, 15K tokens/day",
    },
    "mistral": {
        "class": MistralProvider,
        "api_key_env": "MISTRAL_API_KEY",
        "default_model": os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
        "name": "Mistral AI",
        "tier": "free",
        "quota": "1 req/sec, 500K tokens/month",
    },
    "cerebras": {
        "class": CerebrasProvider,
        "api_key_env": "CEREBRAS_API_KEY",
        "default_model": os.getenv("CEREBRAS_MODEL", "llama-3.1-70b"),
        "name": "Cerebras",
        "tier": "free",
        "quota": "1M tokens/day (!)",
    },
    "cohere": {
        "class": CohereProvider,
        "api_key_env": "COHERE_API_KEY",
        "default_model": os.getenv("COHERE_MODEL", "command-r-08-2024"),
        "name": "Cohere",
        "tier": "free",
        "quota": "1K requests/month + $1 credits",
    },
    "huggingface": {
        "class": HuggingFaceProvider,
        "api_key_env": "HUGGINGFACE_API_KEY",
        # HF routing can be flaky; keep configurable.
        "default_model": os.getenv("HUGGINGFACE_MODEL_ID", "gpt2"),
        "name": "HuggingFace",
        "tier": "free",
        "quota": "32K tokens/month + 100K+ models",
    },
}

PROVIDERS: Dict[str, Any] = {}
for provider_id, config in PROVIDER_CONFIGS.items():
    if ENABLED_PROVIDERS is not None and provider_id not in ENABLED_PROVIDERS:
        continue

    api_key = os.getenv(config["api_key_env"])
    if not api_key:
        PROVIDER_MISSING_KEYS.add(provider_id)
        continue

    try:
        if provider_id == "huggingface":
            PROVIDERS[provider_id] = config["class"](api_key=api_key, model_id=config["default_model"])
        else:
            PROVIDERS[provider_id] = config["class"](api_key=api_key, model_name=config["default_model"])
    except Exception as e:
        PROVIDER_INIT_ERRORS[provider_id] = str(e)
        print(f"Warning: Failed to initialize {provider_id}: {e}")


# ==================== CORE QUERY EXECUTION ====================

async def _query_with_retries(
    provider_id: str,
    prompt: str,
    timeout: int,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Dict[str, Any]:
    provider = PROVIDERS[provider_id]

    # circuit breaker check
    state = PROVIDER_STATE.get(provider_id, {"fail_count": 0.0, "cooldown_until": 0.0})
    now = time.time()
    if state.get("cooldown_until", 0.0) > now:
        until_ts = float(state["cooldown_until"])
        return {
            "status": "error",
            "error_type": "provider_down",
            "error_message": _cooldown_message(until_ts),
            "cooldown_until": until_ts,
            "response_time_ms": 0,
            "cached": False,
            "model_used": getattr(provider, "model_name", "") or getattr(provider, "model_id", ""),
            "provider": provider.__class__.__name__,
            "attempt": 0,
        }

    attempt = 0
    backoff_s = 0.6
    last: Optional[Dict[str, Any]] = None

    while attempt <= max_retries:
        attempt += 1
        try:
            result = await provider.query(prompt, timeout=timeout)
        except asyncio.TimeoutError:
            result = {
                "status": "error",
                "error_type": "timeout",
                "error_message": f"Timed out after {timeout}s",
                "response_time_ms": float(timeout) * 1000.0,
            }
        except Exception as e:
            result = {
                "status": "error",
                "error_type": "unknown",
                "error_message": str(e)[:200],
                "response_time_ms": 0,
            }

        if result.get("status") == "success":
            PROVIDER_STATE[provider_id] = {"fail_count": 0.0, "cooldown_until": 0.0}
            result["attempt"] = attempt
            result.setdefault("model_used", getattr(provider, "model_name", "") or getattr(provider, "model_id", ""))
            result.setdefault("provider", provider.__class__.__name__)
            return result

        last = result
        err_type = result.get("error_type", "unknown")

        if err_type not in RETRYABLE_ERROR_TYPES or attempt > max_retries:
            break

        retry_after_ms = result.get("retry_after_ms")
        if isinstance(retry_after_ms, int) and retry_after_ms > 0:
            await asyncio.sleep(retry_after_ms / 1000)
        else:
            await asyncio.sleep(backoff_s)
            backoff_s *= 2

    # breaker increments ONLY for transient errors
    if last and last.get("error_type") in BREAKABLE_ERROR_TYPES:
        state = PROVIDER_STATE.get(provider_id, {"fail_count": 0.0, "cooldown_until": 0.0})
        state["fail_count"] = float(state.get("fail_count", 0.0)) + 1.0
        if state["fail_count"] >= CIRCUIT_FAILS:
            state["cooldown_until"] = time.time() + COOLDOWN_SECONDS
        PROVIDER_STATE[provider_id] = state

    if last is None:
        last = {
            "status": "error",
            "error_type": "unknown",
            "error_message": "Unknown failure",
            "response_time_ms": 0,
        }

    last["attempt"] = attempt
    last.setdefault("model_used", getattr(provider, "model_name", "") or getattr(provider, "model_id", ""))
    last.setdefault("provider", provider.__class__.__name__)
    return last


# ==================== AGGREGATION + SYNTHESIS ====================

class ResponseSynthesizer:
    @staticmethod
    def aggregate_responses(responses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        successful_responses = {k: v for k, v in responses.items() if v.get("status") == "success"}
        failed_responses = {k: v for k, v in responses.items() if v.get("status") == "error"}

        consensus_analysis = {
            "total_providers": len(responses),
            "successful": len(successful_responses),
            "failed": len(failed_responses),
            "success_rate": (len(successful_responses) / len(responses)) if responses else 0,
        }

        return {
            "consensus_analysis": consensus_analysis,
            "common_themes": [],
            "sources_used": [],
            "source_frequency": {},
            "responses_by_provider": responses,
        }


def _build_synthesis_prompt(user_query: str, responses: Dict[str, Dict[str, Any]]) -> str:
    blocks: List[str] = []
    for pid, r in responses.items():
        if r.get("status") != "success":
            continue
        txt = _safe_str(r.get("response_text", ""))
        if not txt:
            continue
        blocks.append(f"[{pid}]\n{txt[:SYNTH_MAX_CHARS_PER_PROVIDER]}")
    joined = "\n\n".join(blocks) if blocks else "No successful answers."

    return (
        "You are an expert answer synthesizer.\n"
        "Create ONE best final answer to the user query using the model answers.\n"
        "Rules:\n"
        "- Merge the best parts; remove repetition.\n"
        "- If answers conflict, choose the most reasonable and mention uncertainty briefly.\n"
        "- Do not invent facts.\n"
        "- Keep it concise and actionable.\n\n"
        f"User query:\n{user_query}\n\n"
        f"Model answers:\n{joined}\n\n"
        "Final answer:"
    )


async def _synthesize_final_answer(query_text: str, responses: Dict[str, Dict[str, Any]], timeout: int) -> str:
    successful_ids = [
        pid for pid, r in responses.items()
        if r.get("status") == "success" and _safe_str(r.get("response_text"))
    ]
    if not successful_ids:
        return "No provider succeeded. Try again."

    synth_provider_id = "groq" if ("groq" in successful_ids and "groq" in PROVIDERS) else successful_ids[0]

    try:
        prompt = _build_synthesis_prompt(query_text, responses)
        res = await PROVIDERS[synth_provider_id].query(prompt, timeout=min(SYNTH_TIMEOUT_S, timeout))
        if res.get("status") == "success" and _safe_str(res.get("response_text")):
            return _safe_str(res["response_text"])
    except Exception:
        pass

    if "groq" in successful_ids:
        return _safe_str(responses["groq"].get("response_text", ""))
    return _safe_str(responses[successful_ids[0]].get("response_text", ""))


async def orchestrate_query(
    user_id: int,
    query_text: str,
    provider_ids: List[str],
    db=None,
    timeout: int = 30
) -> Dict[str, Any]:
    query_hash = generate_query_hash(user_id, query_text, provider_ids)
    requested_providers = list(provider_ids)

    cached_responses: Dict[str, Dict[str, Any]] = {}
    uncached_providers: List[str] = []

    if db:
        from sqlalchemy import select  # type: ignore
        try:
            from server.db import Cache  # type: ignore
        except Exception:
            from .db import Cache  # type: ignore

        for provider_id in provider_ids:
            if provider_id not in PROVIDERS:
                uncached_providers.append(provider_id)
                continue
            try:
                result = await db.execute(
                    select(Cache).where(
                        (Cache.query_hash == query_hash) &
                        (Cache.agent_id == provider_id) &
                        (Cache.user_id == user_id)
                    )
                )
                cached = result.scalar_one_or_none()
                if cached:
                    cached_responses[provider_id] = {
                        "status": "success",
                        "response_text": cached.response_text,
                        "response_time_ms": 0,
                        "cached": True,
                    }
                else:
                    uncached_providers.append(provider_id)
            except Exception:
                uncached_providers.append(provider_id)
    else:
        uncached_providers = provider_ids

    available_providers = [pid for pid in provider_ids if pid in PROVIDERS]
    skipped_uninitialized = [pid for pid in provider_ids if pid not in PROVIDERS]
    to_run = [pid for pid in uncached_providers if pid in PROVIDERS]

    tasks = [
        asyncio.wait_for(
            _query_with_retries(pid, query_text, timeout=timeout, max_retries=DEFAULT_MAX_RETRIES),
            timeout=timeout + HARD_DEADLINE_BUFFER_S,
        )
        for pid in to_run
    ]

    new_responses: Dict[str, Dict[str, Any]] = {}
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for provider_id, result in zip(to_run, results):
            if isinstance(result, asyncio.TimeoutError):
                new_responses[provider_id] = {
                    "status": "error",
                    "error_type": "timeout",
                    "error_message": f"Timed out after {timeout}s",
                    "cached": False,
                    "response_time_ms": float(timeout) * 1000.0,
                }
                continue
            if isinstance(result, Exception):
                new_responses[provider_id] = {
                    "status": "error",
                    "error_type": "unknown",
                    "error_message": str(result)[:200],
                    "cached": False,
                    "response_time_ms": 0,
                }
                continue
            new_responses[provider_id] = {**result, "cached": False}

            if db and result.get("status") == "success":
                try:
                    try:
                        from server.db import Cache  # type: ignore
                    except Exception:
                        from .db import Cache  # type: ignore
                    db.add(Cache(
                        user_id=user_id,
                        query_hash=query_hash,
                        agent_id=provider_id,
                        response_text=result.get("response_text", ""),
                    ))
                except Exception:
                    pass

    for pid in skipped_uninitialized:
        new_responses[pid] = {
            "status": "error",
            "error_type": "not_initialized",
            "error_message": "Provider not initialized (missing API key?)",
            "cached": False,
            "response_time_ms": 0,
        }

    if db:
        try:
            await db.commit()
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass

    all_responses = {**cached_responses, **new_responses}

    # Normalize error messages
    for _, r in all_responses.items():
        if r.get("status") == "error" and isinstance(r.get("error_message"), str):
            r["error_message"] = _short_error(r["error_message"])

    synthesis = ResponseSynthesizer.aggregate_responses(all_responses)
    final_answer = await _synthesize_final_answer(query_text, all_responses, timeout=timeout)

    successful = [r for r in all_responses.values() if r.get("status") == "success"]
    response_times = [r.get("response_time_ms", 0) for r in successful if not r.get("cached", False)]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0

    return {
        "final_answer": final_answer,
        "responses": all_responses,
        "synthesis": synthesis,
        "metadata": {
            "requested_providers": requested_providers,
            "available_providers": available_providers,
            "skipped_uninitialized": skipped_uninitialized,
            "total_requested": len(requested_providers),
            "total_available": len(available_providers),
            "successful": len(successful),
            "failed": len(all_responses) - len(successful),
            "avg_response_time_ms": avg_response_time,
            "cached_count": len(cached_responses),
            "query_hash": query_hash,
            "synth_strategy": "prefer_groq",
        }
    }


async def validate_all_providers() -> Dict[str, bool]:
    results: Dict[str, bool] = {}
    tasks = [(pid, provider.validate_key()) for pid, provider in PROVIDERS.items()]
    for provider_id, task in tasks:
        try:
            results[provider_id] = await task
        except Exception:
            results[provider_id] = False
    return results


def get_provider_info() -> Dict[str, Dict[str, Any]]:
    info: Dict[str, Dict[str, Any]] = {}
    for provider_id, config in PROVIDER_CONFIGS.items():
        enabled = ENABLED_PROVIDERS is None or provider_id in ENABLED_PROVIDERS
        is_initialized = provider_id in PROVIDERS
        init_error = PROVIDER_INIT_ERRORS.get(provider_id)
        missing_key = provider_id in PROVIDER_MISSING_KEYS

        if not enabled:
            status_reason = "disabled_by_config"
        elif is_initialized:
            status_reason = "ready"
        elif init_error:
            status_reason = "init_failed"
        elif missing_key:
            status_reason = "missing_api_key"
        else:
            status_reason = "not_initialized"

        info[provider_id] = {
            "name": config["name"],
            "tier": config["tier"],
            "quota": config["quota"],
            "enabled": enabled,
            "initialized": is_initialized,
            "default_model": config["default_model"],
            "status": status_reason,
            "error": init_error,
        }
    return info
