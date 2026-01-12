import asyncio
import aiohttp
import json
from typing import Dict, Any, List
import time
from .base_provider import BaseProvider

class CerebrasProvider(BaseProvider):
    """
    Cerebras AI Provider - 20x faster than GPT-4, ultra-generous free tier
    Free tier: 1,000,000 tokens/day (!)
    No credit card required
    
    Docs: https://docs.cerebras.ai/
    """
    
    def __init__(self, api_key: str, model_name: str = "llama-3.1-70b"):
        super().__init__(api_key, model_name)
        self.base_url = "https://api.cerebras.ai/v1/chat/completions"
    
    async def query(self, prompt: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Query Cerebras API - fastest inference available.
        """
        start_time = time.time()
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Provide concise, accurate responses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
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
                        response_text = data["choices"][0]["message"]["content"]
                        
                        # Get token count
                        token_count = 0
                        if "usage" in data:
                            token_count = (data["usage"].get("prompt_tokens", 0) + 
                                         data["usage"].get("completion_tokens", 0))
                        
                        return self.format_response(
                            response_text=response_text,
                            response_time_ms=response_time_ms,
                            token_count=token_count if token_count > 0 else len(response_text.split())
                        )
                    else:
                        error_text = await response.text()

                        # If the configured model isn't available for this key/account, retry once with a smaller model.
                        if response.status == 404 and self.model_name != "llama-3.1-8b":
                            self.model_name = "llama-3.1-8b"
                            return await self.query(prompt, timeout=timeout)

                        return self.format_error(
                            error_message=f"HTTP {response.status}: {error_text[:100]}",
                            response_time_ms=response_time_ms
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
                error_message=f"Cerebras Error: {str(e)[:100]}",
                response_time_ms=response_time_ms
            )
    
    async def validate_key(self) -> bool:
        """
        Validate Cerebras API key.
        """
        try:
            result = await self.query("Hello", timeout=10)
            return result["status"] == "success"
        except Exception:
            return False
    
    @staticmethod
    def get_available_models() -> List[str]:
        """
        Return list of available Cerebras models.
        """
        return [
            "llama-3.1-70b",  # Most capable, still fast
            "llama-3.1-8b",   # Smaller, fastest
        ]
