import httpx
from typing import Dict, Optional, List
from datetime import datetime
from config import settings

class AIProviderService:
    def __init__(self):
        self.providers = {
            "openai": self._query_openai,
            "anthropic": self._query_anthropic,
            "google": self._query_google
        }
    
    async def query(self, model: str, query: str, temperature: float = 0.7, max_tokens: int = 1000) -> Dict:
        provider = self._get_provider(model)
        if not provider:
            raise ValueError(f"Unknown model: {model}")
        return await self.providers[provider](model, query, temperature, max_tokens)
    
    def _get_provider(self, model: str) -> Optional[str]:
        if model.startswith("openai-") or "gpt" in model.lower():
            return "openai"
        elif model.startswith("claude-") or "claude" in model.lower():
            return "anthropic"
        elif model.startswith("gemini-") or "gemini" in model.lower():
            return "google"
        return None
    
    async def _query_openai(self, model: str, query: str, temperature: float, max_tokens: int) -> Dict:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model.replace("openai-", ""),
                    "messages": [{"role": "user", "content": query}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return {
                "response": data["choices"][0]["message"]["content"],
                "tokens_used": data.get("usage", {}).get("total_tokens")
            }
    
    async def _query_anthropic(self, model: str, query: str, temperature: float, max_tokens: int) -> Dict:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key not configured")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model.replace("claude-", "claude-"),
                    "messages": [{"role": "user", "content": query}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return {
                "response": data["content"][0]["text"],
                "tokens_used": data.get("usage", {}).get("output_tokens")
            }
    
    async def _query_google(self, model: str, query: str, temperature: float, max_tokens: int) -> Dict:
        if not settings.GOOGLE_API_KEY:
            raise ValueError("Google API key not configured")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model.replace('gemini-', 'gemini-')}:generateContent?key={settings.GOOGLE_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": query}]}],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens
                    }
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return {
                "response": data["candidates"][0]["content"]["parts"][0]["text"],
                "tokens_used": None
            }
    
    async def get_provider_status(self) -> List[Dict]:
        statuses = []
        statuses.append({
            "name": "OpenAI",
            "status": "online" if settings.OPENAI_API_KEY else "disabled",
            "models": ["openai-gpt-4", "openai-gpt-3.5-turbo"],
            "last_checked": datetime.utcnow()
        })
        statuses.append({
            "name": "Anthropic",
            "status": "online" if settings.ANTHROPIC_API_KEY else "disabled",
            "models": ["claude-3-5-sonnet", "claude-3-opus"],
            "last_checked": datetime.utcnow()
        })
        statuses.append({
            "name": "Google",
            "status": "online" if settings.GOOGLE_API_KEY else "disabled",
            "models": ["gemini-pro", "gemini-1.5-pro"],
            "last_checked": datetime.utcnow()
        })
        return statuses
