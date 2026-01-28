from typing import List, Dict, Any
# ---------- Synthesis helpers ----------
def _pick_first_success_provider_id(responses: Dict[str, Dict[str, Any]]) -> str | None:
    for pid, r in responses.items():
        if r.get("status") == "success" and (r.get("response_text") or "").strip():
            return pid
    return None

import hashlib
import time
import asyncio
from typing import List, Dict, Any, Optional


try:
    # When imported as a package module (recommended): `server.orchestrator_v2`
    from .providers import (
        GroqProvider,
        GeminiProvider,
        MistralProvider,
        CerebrasProvider,
        CohereProvider,
        HuggingFaceProvider,
    )
except ImportError:
    try:
        # When running from project root or as server.providers
        from server.providers import (
            GroqProvider,
            GeminiProvider,
            MistralProvider,
            CerebrasProvider,
            CohereProvider,
            HuggingFaceProvider,
        )
    except ImportError:
        from providers import (
            GroqProvider,
            GeminiProvider,
            MistralProvider,
            CerebrasProvider,
            CohereProvider,
            HuggingFaceProvider,
        )

import os
from dotenv import load_dotenv

_ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(_ENV_PATH)

# ==================== STABILITY SETTINGS ====================

# In-memory circuit breaker state (per-process)
PROVIDER_STATE: Dict[str, Dict[str, float]] = {}
CIRCUIT_FAILS = int(os.getenv("CIRCUIT_FAILS", "3"))
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "120"))

RETRYABLE_ERROR_TYPES = {"timeout", "rate_limited", "provider_down"}
DEFAULT_MAX_RETRIES = int(os.getenv("PROVIDER_MAX_RETRIES", "2"))
HARD_DEADLINE_BUFFER_S = int(os.getenv("HARD_DEADLINE_BUFFER_S", "10"))

SYNTH_TIMEOUT_S = int(os.getenv("SYNTH_TIMEOUT_S", "30"))


import hashlib
import time
import asyncio
from typing import List, Dict, Any

# ==================== SYNTHESIS HELPERS ====================
def get_first_initialized_provider_id() -> str | None:
    # PROVIDERS preserves insertion order in modern Python, and you build it in PROVIDER_CONFIGS order.
    return next(iter(PROVIDERS.keys()), None)

def build_synthesis_prompt(user_query: str, responses: Dict[str, Dict[str, Any]]) -> str:
    successful = [(pid, r.get("response_text", "")) for pid, r in responses.items() if r.get("status") == "success"]
    # Safety: cap each answer to avoid huge prompts
    capped = [(pid, (txt or "")[:1800]) for pid, txt in successful]

    joined = "\n\n".join([f"[{pid}]\n{txt}" for pid, txt in capped])

    return (
        "You are an expert answer synthesizer.\n"
        "Task: Produce ONE final answer to the user query using the model answers below.\n"
        "Rules:\n"
        "- Merge the best parts, remove repetition.\n"
        "- If answers conflict, choose the most reasonable and mention uncertainty briefly.\n"
        "- Be concise, practical, and correct.\n\n"
        f"User query:\n{user_query}\n\n"
        f"Model answers:\n{joined}\n\n"
        "Final answer:"
    )

import hashlib
import time
import asyncio
from typing import List, Dict, Any

try:
    # When imported as a package module (recommended): `server.orchestrator_v2`
    from .providers import (
        GroqProvider,
        GeminiProvider,
        MistralProvider,
        CerebrasProvider,
        CohereProvider,
        HuggingFaceProvider,
    )
except ImportError:
    try:
        # When running from within the `server/` directory
        from server.providers import (
            GroqProvider,
            GeminiProvider,
            MistralProvider,
            CerebrasProvider,
            CohereProvider,
            HuggingFaceProvider,
        )
    except ImportError:
        from providers import (
            GroqProvider,
            GeminiProvider,
            MistralProvider,
            CerebrasProvider,
            CohereProvider,
            HuggingFaceProvider,
        )
import os
from dotenv import load_dotenv

_ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(_ENV_PATH)

# ==================== STABILITY SETTINGS ====================

# In-memory circuit breaker state (per-process)
PROVIDER_STATE: Dict[str, Dict[str, float]] = {}
CIRCUIT_FAILS = 3
COOLDOWN_SECONDS = 120

RETRYABLE_ERROR_TYPES = {"timeout", "rate_limited", "provider_down"}


async def _query_with_retries(
    provider_id: str,
    prompt: str,
    timeout: int,
    max_retries: int = 2,
) -> Dict[str, Any]:
    provider = PROVIDERS[provider_id]

    # circuit breaker check
    state = PROVIDER_STATE.get(provider_id, {"fail_count": 0.0, "cooldown_until": 0.0})
    now = time.time()
    if state.get("cooldown_until", 0.0) > now:
        return {
            "status": "error",
            "error_type": "provider_down",
            "error_message": f"Provider in cooldown until {state['cooldown_until']:.0f}",
            "response_time_ms": 0,
            "cached": False,
            "model_used": getattr(provider, "model_name", ""),
            "provider": provider.__class__.__name__,
            "attempt": 0,
        }

    attempt = 0
    backoff_s = 0.6
    last: Dict[str, Any] | None = None

    while attempt <= max_retries:
        attempt += 1
        result = await provider.query(prompt, timeout=timeout)

        if result.get("status") == "success":
            PROVIDER_STATE[provider_id] = {"fail_count": 0.0, "cooldown_until": 0.0}
            result["attempt"] = attempt
            return result

        last = result
        err_type = result.get("error_type", "unknown")
        if err_type not in RETRYABLE_ERROR_TYPES or attempt > max_retries:
            break

        # Respect retry_after_ms when provided
        retry_after_ms = result.get("retry_after_ms")
        if isinstance(retry_after_ms, int) and retry_after_ms > 0:
            await asyncio.sleep(retry_after_ms / 1000)
        else:
            await asyncio.sleep(backoff_s)
            backoff_s *= 2

    # update breaker
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
    return last

# ==================== PROVIDER REGISTRY ====================

# Optional allow-list to control which providers are active in production.
# Example: ENABLED_PROVIDERS=groq,gemini,mistral
_enabled_env = (os.getenv("ENABLED_PROVIDERS") or "").strip()
ENABLED_PROVIDERS = {p.strip() for p in _enabled_env.split(",") if p.strip()} or None
PROVIDER_INIT_ERRORS: Dict[str, str] = {}
PROVIDER_MISSING_KEYS: set[str] = set()

PROVIDER_CONFIGS = {
    "groq": {
        "class": GroqProvider,
        "api_key_env": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
        "name": "Groq",
        "tier": "free",
        "quota": "14.4K req/day",
    },
    "gemini": {
        "class": GeminiProvider,
        "api_key_env": "GEMINI_API_KEY",
        "default_model": "gemini-1.5-flash",
        "name": "Google Gemini",
        "tier": "free",
        "quota": "60 req/min, 15K tokens/day",
    },
    "mistral": {
        "class": MistralProvider,
        "api_key_env": "MISTRAL_API_KEY",
        "default_model": "mistral-large-latest",
        "name": "Mistral AI",
        "tier": "free",
        "quota": "1 req/sec, 500K tokens/month",
    },
    "cerebras": {
        "class": CerebrasProvider,
        "api_key_env": "CEREBRAS_API_KEY",
        "default_model": "llama-3.1-70b",
        "name": "Cerebras",
        "tier": "free",
        "quota": "1M tokens/day (!)",
    },
    "cohere": {
        "class": CohereProvider,
        "api_key_env": "COHERE_API_KEY",
        "default_model": "command-r",
        "name": "Cohere",
        "tier": "free",
        "quota": "1K requests/month + $1 credits",
    },
    "huggingface": {
        "class": HuggingFaceProvider,
        "api_key_env": "HUGGINGFACE_API_KEY",
        "default_model": "HuggingFaceH4/zephyr-7b-beta",
        "name": "HuggingFace",
        "tier": "free",
        "quota": "32K tokens/month + 100K+ models",
    },
}

# Initialize providers from environment
PROVIDERS = {}
for provider_id, config in PROVIDER_CONFIGS.items():
    if ENABLED_PROVIDERS is not None and provider_id not in ENABLED_PROVIDERS:
        continue
    api_key = os.getenv(config["api_key_env"])
    if api_key:
        try:
            # HuggingFace uses model_id instead of model_name
            if provider_id == "huggingface":
                PROVIDERS[provider_id] = config["class"](
                    api_key=api_key,
                    model_id=config["default_model"]
                )
            else:
                PROVIDERS[provider_id] = config["class"](
                    api_key=api_key,
                    model_name=config["default_model"]
                )
        except Exception as e:
            PROVIDER_INIT_ERRORS[provider_id] = str(e)
            print(f"Warning: Failed to initialize {provider_id}: {e}")
    else:
        PROVIDER_MISSING_KEYS.add(provider_id)

# ==================== UTILITY FUNCTIONS ====================

def generate_query_hash(user_id: int, query_text: str, agent_ids: List[str]) -> str:
    """User-scoped hash prevents cross-user cache pollution."""
    content = f"{user_id}:{query_text}:{'|'.join(sorted(agent_ids))}"
    return hashlib.sha256(content.encode()).hexdigest()

class ResponseSynthesizer:
    """
    Synthesize responses from multiple providers.
    """
    
    @staticmethod
    def aggregate_responses(responses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate responses from multiple providers.
        """
        successful_responses = {k: v for k, v in responses.items() if v["status"] == "success"}
        failed_responses = {k: v for k, v in responses.items() if v["status"] == "error"}
        
        # Consensus analysis
        consensus_analysis = {
            "total_providers": len(responses),
            "successful": len(successful_responses),
            "failed": len(failed_responses),
            "success_rate": len(successful_responses) / len(responses) if responses else 0,
        }
        
        # Collect all sources
        all_sources = []
        source_counts = {}
        for response in successful_responses.values():
            for source in response.get("sources", []):
                source_key = source.get("url") or source.get("type", "unknown")
                source_counts[source_key] = source_counts.get(source_key, 0) + 1
                if source not in all_sources:
                    all_sources.append(source)
        
        # Find consensus topics (common words in responses)
        response_texts = [r.get("response_text", "") for r in successful_responses.values()]
        consensus_topics = ResponseSynthesizer._extract_common_topics(response_texts)
        
        return {
            "consensus_analysis": consensus_analysis,
            "common_themes": consensus_topics,
            "sources_used": all_sources,
            "source_frequency": source_counts,
            "responses_by_provider": responses,
        }
    
    @staticmethod
    def _extract_common_topics(texts: List[str], top_n: int = 5) -> List[str]:
        """
        Extract common topics from multiple texts.
        Simple word frequency analysis.
        """
        if not texts:
            return []
        
        # Common stopwords to exclude
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "is", "are", "was", "were", "be", "been", "being"}
        
        word_freq = {}
        for text in texts:
            words = [w.lower() for w in text.split() if w.lower() not in stopwords and len(w) > 3]
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and get top N
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [word for word, _ in top_words]

# ==================== MAIN ORCHESTRATION ====================

async def orchestrate_query(
    user_id: int,
    query_text: str,
    provider_ids: List[str],
    db=None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Orchestrate parallel queries to multiple AI providers.
    
    Args:
        query_text: User's prompt
        provider_ids: List of provider IDs to query (e.g., ["groq", "gemini", "mistral"])
        db: Database session (optional, for caching)
        timeout: Timeout per request in seconds
    
    Returns:
        {
            "responses": {provider_id: response_data},
            "synthesis": synthesis_data,
            "metadata": {
                "total_providers": int,
                "successful": int,
                "avg_response_time_ms": float,
                "cached_count": int,
            }
        }
    """
    
    query_hash = generate_query_hash(user_id, query_text, provider_ids)
    requested_providers = list(provider_ids)
    cached_responses: Dict[str, Dict[str, Any]] = {}
    uncached_providers: List[str] = []
    
    # Check cache if DB available
    if db:
        from sqlalchemy import select
        try:
            from server.db import Cache  # type: ignore
        except ImportError:
            from db import Cache  # type: ignore
        
        for provider_id in provider_ids:
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

    # Only run uncached among the available
    to_run = [pid for pid in uncached_providers if pid in PROVIDERS]

    # IMPORTANT: enforce a hard deadline per provider so a single slow provider
    # (or retry/backoff logic) can't hang the entire request.
    tasks = [
        asyncio.wait_for(
            _query_with_retries(pid, query_text, timeout=timeout, max_retries=2),
            timeout=timeout + 10,
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

            # Cache successful responses
            if db and result.get("status") == "success":
                try:
                    try:
                        from server.db import Cache  # type: ignore
                    except ImportError:
                        from db import Cache  # type: ignore
                    db.add(Cache(user_id=user_id, query_hash=query_hash, agent_id=provider_id, response_text=result["response_text"]))
                except Exception as e:
                    print(f"Warning: Failed to cache {provider_id}: {e}")

    # Add explicit responses for requested but uninitialized providers
    for pid in skipped_uninitialized:
        new_responses[pid] = {
            "status": "error",
            "error_type": "not_initialized",
            "error_message": "Provider not initialized (missing API key?)",
            "cached": False,
            "response_time_ms": 0,
        }
    
    # Commit cache to DB
    if db:
        try:
            await db.commit()
        except Exception as e:
            print(f"Warning: Failed to commit cache: {e}")
            try:
                await db.rollback()
            except Exception:
                pass
    

    # Combine all responses
    all_responses = {**cached_responses, **new_responses}

    # ---------- Single final answer synthesis ----------
    final_answer: str | None = None
    synth_provider_id = _pick_first_success_provider_id(all_responses)

    if synth_provider_id:
        try:
            synth_prompt = _build_synthesis_prompt(query_text, all_responses)
            synth_result = await PROVIDERS[synth_provider_id].query(synth_prompt, timeout=timeout)
            if synth_result.get("status") == "success" and (synth_result.get("response_text") or "").strip():
                final_answer = synth_result["response_text"]
        except Exception:
            final_answer = None

    # Fallback if synthesis fails: first successful response
    if not final_answer:
        for r in all_responses.values():
            if r.get("status") == "success" and (r.get("response_text") or "").strip():
                final_answer = r.get("response_text")
                break
    if not final_answer:
        final_answer = "No provider succeeded. Try again."

    # Synthesize (legacy aggregation)
    synthesis = ResponseSynthesizer.aggregate_responses(all_responses)

    # Calculate metadata
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
            "synth_provider_id": synth_provider_id,
        }
    }

# ==================== HELPER FUNCTIONS ====================

async def validate_all_providers() -> Dict[str, bool]:
    """
    Validate all initialized providers.
    Returns status of each provider.
    """
    results = {}
    tasks = [(pid, provider.validate_key()) for pid, provider in PROVIDERS.items()]
    
    for provider_id, task in tasks:
        try:
            results[provider_id] = await task
        except Exception as e:
            print(f"Error validating {provider_id}: {e}")
            results[provider_id] = False
    
    return results

def get_provider_info() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all available providers.
    """
    info = {}
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
