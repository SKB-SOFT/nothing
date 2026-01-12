import asyncio
import aiohttp
from typing import Dict, Any, List
import time
from .base_provider import BaseProvider


def _classify_http(status: int) -> str:
    """Classify HTTP errors for retry logic."""
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
    """Google Gemini API Provider with v1/v1beta fallback."""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        super().__init__(api_key, model_name)
        self.base_v1 = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
        self.base_v1beta = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

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

    def _extract_text_and_sources(self, data: dict) -> tuple[str, list]:
        response_text = ""
        sources: list = []

        candidates = data.get("candidates") or []
        cand = candidates[0] if isinstance(candidates, list) and candidates else {}
        content = cand.get("content", {}) if isinstance(cand, dict) else {}
        for part in content.get("parts", []) or []:
            if isinstance(part, dict) and "text" in part:
                response_text += str(part.get("text") or "")

        grounding = (cand.get("groundingMetadata") or {}) if isinstance(cand, dict) else {}
        chunks = grounding.get("groundingChunks") or []
        if isinstance(chunks, list):
            for chunk in chunks:
                if not isinstance(chunk, dict):
                    continue
                web = chunk.get("web")
                if isinstance(web, dict):
                    sources.append({"url": web.get("uri", ""), "title": web.get("title", "")})

        return response_text, sources

    async def query(self, prompt: str, timeout: int = 30, web_search: bool = False) -> Dict[str, Any]:
        """Query Gemini API with v1/v1beta fallback."""
        start_time = time.time()

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 1024,
                "temperature": 0.7,
                "topP": 0.9,
            },
        }

        if web_search:
            payload["tools"] = [{"googleSearch": {}}]

        last_error: tuple[int | str, str] | None = None

        try:
            async with aiohttp.ClientSession() as session:
                # Try v1 first (supports more models like gemini-1.5-flash), then v1beta.
                for url in (self.base_v1, self.base_v1beta):
                    try:
                        resp = await self._post(session, url, payload, timeout)
                        response_time_ms = (time.time() - start_time) * 1000

                        if resp.status == 200:
                            data = await resp.json()
                            response_text, sources = self._extract_text_and_sources(data)

                            usage = data.get("usageMetadata") or {}
                            token_count = usage.get("promptTokenCount", 0) + usage.get("candidatesTokenCount", 0)

                            if not response_text.strip():
                                response_text = "No response generated"

                            return self.format_response(
                                response_text=response_text,
                                response_time_ms=response_time_ms,
                                token_count=token_count if token_count > 0 else len(response_text.split()),
                                sources=sources,
                            )

                        err_text = await resp.text()

                        # If 404, try next version.
                        if resp.status == 404:
                            last_error = (resp.status, err_text[:200])
                            continue

                        # Non-404 error: Respect Retry-After when rate-limited.
                        retry_after = resp.headers.get("Retry-After")
                        retry_after_ms = int(float(retry_after) * 1000) if retry_after else None

                        return self.format_error(
                            error_message=f"HTTP {resp.status}: {err_text[:200]}",
                            response_time_ms=response_time_ms,
                            error_type=_classify_http(resp.status),
                            retry_after_ms=retry_after_ms,
                        )

                    except asyncio.TimeoutError:
                        last_error = ("timeout", f"Timeout on {url}")
                        continue

                # Both versions failed.
                status, msg = last_error if last_error else (500, "Unknown error")
                return self.format_error(
                    error_message=f"HTTP {status}: {msg}",
                    response_time_ms=(time.time() - start_time) * 1000,
                    error_type="timeout" if status == "timeout" else ("model_not_found" if status == 404 else "unknown"),
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
        """Validate Gemini API key."""
        try:
            r = await self.query("Hello", timeout=10)
            return r.get("status") == "success"
        except Exception:
            return False

    @staticmethod
    def get_available_models() -> List[str]:
        """Return list of available Gemini models."""
        return [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-pro",
        ]
