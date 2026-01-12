import asyncio
import aiohttp
from typing import Dict, Any, List
import time
import json
from .base_provider import BaseProvider


def _classify_http(status: int) -> str:
    if status == 429:
        return "rate_limited"
    if status in (500, 502, 503, 504):
        return "provider_down"
    if status in (401, 403):
        return "auth_error"
    if status == 400:
        return "bad_request"
    if status == 404:
        return "model_not_found"
    return "unknown"


class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        super().__init__(api_key, model_name)
        self.base_v1 = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
        self.base_v1beta = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

        # Cache ListModels results (per-process) to avoid repeated calls.
        self._models_cache: list[str] | None = None
        self._models_cache_ts: float = 0.0

    def _url_for(self, api_version: str, model_name: str) -> str:
        return f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent"

    async def _list_models(self, session: aiohttp.ClientSession, timeout: int = 10) -> list[str]:
        # 5-minute cache
        now = time.time()
        if self._models_cache and (now - self._models_cache_ts) < 300:
            return self._models_cache

        params = {"key": self.api_key}
        headers = {"Content-Type": "application/json"}

        for api_version in ("v1", "v1beta"):
            url = f"https://generativelanguage.googleapis.com/{api_version}/models"
            try:
                resp = await session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                )
                if resp.status != 200:
                    _ = await resp.text()
                    continue

                data = await resp.json()
                names: list[str] = []
                for m in data.get("models", []) or []:
                    name = m.get("name")
                    # usually "models/<id>"
                    if isinstance(name, str) and name.startswith("models/"):
                        names.append(name.split("/", 1)[1])
                if names:
                    self._models_cache = names
                    self._models_cache_ts = now
                    return names
            except Exception:
                continue

        return []

    def _pick_fallback_model(self, available: list[str]) -> str | None:
        # Prefer modern fast models, but fall back to older names if that’s all the key has access to.
        preferred = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro",
            "gemini-1.5-pro-latest",
            "gemini-pro",
            "gemini-1.0-pro",
        ]
        avail_set = set(available)
        for m in preferred:
            if m in avail_set:
                return m
        return available[0] if available else None

    async def _post(self, session: aiohttp.ClientSession, url: str, payload: dict, timeout: int):
        params = {"key": self.api_key}
        headers = {"Content-Type": "application/json"}
        return await session.post(
            url,
            json=payload,
            params=params,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout),
        )

    async def query(self, prompt: str, timeout: int = 30, web_search: bool = False) -> Dict[str, Any]:
        start_time = time.time()

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7, "topP": 0.9},
        }

        # only works for some models; keep optional
        if web_search:
            payload["tools"] = [{"googleSearch": {}}]

        try:
            async with aiohttp.ClientSession() as session:
                last_error = (404, "")

                # Try v1 first (fixes gemini-1.5-flash 404 on v1beta), then fallback to v1beta
                for url in (self.base_v1, self.base_v1beta):
                    resp = await self._post(session, url, payload, timeout)
                    response_time_ms = (time.time() - start_time) * 1000

                    if resp.status == 200:
                        data = await resp.json()

                        response_text = ""
                        sources = []

                        if data.get("candidates"):
                            cand = data["candidates"][0]
                            content = cand.get("content", {})
                            for part in content.get("parts", []):
                                if "text" in part:
                                    response_text += part["text"]

                            grounding = cand.get("groundingMetadata") or {}
                            if "groundingChunks" in grounding:
                                for chunk in grounding["groundingChunks"]:
                                    web = chunk.get("web")
                                    if web:
                                        sources.append({"url": web.get("uri", ""), "title": web.get("title", "")})

                        usage = data.get("usageMetadata") or {}
                        token_count = usage.get("promptTokenCount", 0) + usage.get("candidatesTokenCount", 0)

                        if not response_text:
                            response_text = "No response generated"

                        return self.format_response(
                            response_text=response_text,
                            response_time_ms=response_time_ms,
                            token_count=token_count if token_count > 0 else len(response_text.split()),
                            sources=sources,
                        )

                    err_text = await resp.text()

                    # If 404 on this version, try the next version (v1 <-> v1beta)
                    if resp.status == 404:
                        last_error = (resp.status, err_text)
                        continue

                    # Respect Retry-After when rate-limited
                    retry_after = resp.headers.get("Retry-After")
                    retry_after_ms = int(float(retry_after) * 1000) if retry_after else None

                    return self.format_error(
                        error_message=f"HTTP {resp.status}: {err_text[:200]}",
                        response_time_ms=response_time_ms,
                        error_type=_classify_http(resp.status),
                        retry_after_ms=retry_after_ms,
                    )

                # Both v1 and v1beta failed with 404
                available_models = await self._list_models(session, timeout=10)
                fallback_model = self._pick_fallback_model(available_models)

                if fallback_model and fallback_model != self.model_name:
                    # Retry once with a model we know exists for this key.
                    for api_version in ("v1", "v1beta"):
                        retry_url = self._url_for(api_version, fallback_model)
                        resp = await self._post(session, retry_url, payload, timeout)
                        response_time_ms = (time.time() - start_time) * 1000

                        if resp.status == 200:
                            data = await resp.json()

                            response_text = ""
                            sources = []

                            if data.get("candidates"):
                                cand = data["candidates"][0]
                                content = cand.get("content", {})
                                for part in content.get("parts", []):
                                    if "text" in part:
                                        response_text += part["text"]

                                grounding = cand.get("groundingMetadata") or {}
                                if "groundingChunks" in grounding:
                                    for chunk in grounding["groundingChunks"]:
                                        web = chunk.get("web")
                                        if web:
                                            sources.append({"url": web.get("uri", ""), "title": web.get("title", "")})

                            usage = data.get("usageMetadata") or {}
                            token_count = usage.get("promptTokenCount", 0) + usage.get("candidatesTokenCount", 0)

                            if not response_text:
                                response_text = "No response generated"

                            out = self.format_response(
                                response_text=response_text,
                                response_time_ms=response_time_ms,
                                token_count=token_count if token_count > 0 else len(response_text.split()),
                                sources=sources,
                            )
                            out["model_used"] = fallback_model
                            return out

                        if resp.status != 404:
                            err_text = await resp.text()
                            return self.format_error(
                                error_message=f"HTTP {resp.status}: {err_text[:200]}",
                                response_time_ms=response_time_ms,
                                error_type=_classify_http(resp.status),
                            )

                status, err_text = last_error
                hint = ""
                if available_models:
                    hint = f" Available models for this key include: {', '.join(available_models[:8])}"
                return self.format_error(
                    error_message=f"HTTP {status}: {err_text[:200]}{hint}",
                    response_time_ms=(time.time() - start_time) * 1000,
                    error_type="model_not_found",
                )

        except asyncio.TimeoutError:
            return self.format_error(
                error_message=f"Request timeout ({timeout}s)",
                response_time_ms=(time.time() - start_time) * 1000,
                error_type="timeout",
            )
        except Exception as e:
            return self.format_error(
                error_message=f"Gemini Error: {str(e)[:200]}",
                response_time_ms=(time.time() - start_time) * 1000,
                error_type="unknown",
            )

    async def validate_key(self) -> bool:
        try:
            r = await self.query("Hello", timeout=10)
            return r.get("status") == "success"
        except Exception:
            return False

    @staticmethod
    def get_available_models() -> List[str]:
        return [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-pro",
        ]
