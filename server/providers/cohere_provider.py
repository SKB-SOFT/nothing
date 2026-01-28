import asyncio
import aiohttp
import json
from typing import Dict, Any, List
import time
from .base_provider import BaseProvider

class CohereProvider(BaseProvider):
    """
    Cohere AI Provider - Text generation and understanding
    Free tier: 1,000 requests/month with $1 trial credits
    No credit card required
    
    Docs: https://docs.cohere.com/reference/generate
    """
    
    def __init__(self, api_key: str, model_name: str = "command-r"):
        super().__init__(api_key, model_name)
        self.base_url = "https://api.cohere.ai/v1/chat"
    
    async def query(self, prompt: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Query Cohere API for text generation.
        """
        start_time = time.time()
        
        payload = {
            "message": prompt,
            "model": self.model_name,
            "max_tokens": 1024,
            "temperature": 0.7,
            "p": 0.9,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        # Try common Cohere chat response shapes
                        response_text = ""
                        if isinstance(data, dict):
                            # Some responses: {"text": "..."}
                            if isinstance(data.get("text"), str):
                                response_text = data["text"]
                            # Some chat responses: {"message": {"content": [{"type":"text","text":"..."}]}}
                            if not response_text and isinstance(data.get("message"), dict):
                                msg = data["message"]
                                content = msg.get("content")
                                if isinstance(content, list):
                                    chunks = []
                                    for item in content:
                                        if isinstance(item, dict) and isinstance(item.get("text"), str):
                                            chunks.append(item["text"])
                                    response_text = "".join(chunks).strip()
                            # Some responses: {"response": "..."} (defensive)
                            if not response_text and isinstance(data.get("response"), str):
                                response_text = data["response"]
                        if not response_text:
                            response_text = str(data)[:500]
                        sources = []
                        if isinstance(data, dict) and isinstance(data.get("citations"), list):
                            sources = data["citations"]
                        token_count = len(response_text.split())
                        return self.format_response(
                            response_text=response_text,
                            response_time_ms=response_time_ms,
                            token_count=token_count,
                            sources=sources
                        )
                    # Non-200 error
                    error_text = await response.text()
                    error_type = "model_not_found" if response.status == 404 else ("rate_limited" if response.status == 429 else ("auth_error" if response.status in (401, 403) else "unknown"))
                    return self.format_error(
                        error_message=f"HTTP {response.status}: {error_text[:200]}",
                        response_time_ms=response_time_ms,
                        error_type=error_type,
                    )
        
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            return self.format_error(
                error_message="Request timeout (30s)",
                response_time_ms=response_time_ms
            )
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return self.format_error(
                error_message=f"Cohere Error: {str(e)[:100]}",
                response_time_ms=response_time_ms
            )
    
    async def validate_key(self) -> bool:
        """
        Validate Cohere API key.
        """
        try:
            result = await self.query("Hello", timeout=10)
            return result["status"] == "success"
        except Exception:
            return False
    
    @staticmethod
    def get_available_models() -> List[str]:
        """
        Return list of available Cohere models.
        """
        return [
            "command-r",       # Strong default
            "command-r-plus",  # May require specific access
            "command-light",   # Faster, lighter
        ]
