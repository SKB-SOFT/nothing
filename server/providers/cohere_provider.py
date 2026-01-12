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
    
    def __init__(self, api_key: str, model_name: str = "command-r-plus"):
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
                        response_text = data["text"]
                        
                        # Extract sources if available (from citations)
                        sources = []
                        if "citations" in data:
                            sources = data["citations"]
                        
                        # Get token count estimate
                        token_count = len(response_text.split())  # Rough estimate
                        
                        return self.format_response(
                            response_text=response_text,
                            response_time_ms=response_time_ms,
                            token_count=token_count,
                            sources=sources
                        )
                    else:
                        error_text = await response.text()
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
            "command-r-plus",  # Most capable, can generate, summarize, analyze
            "command-r",       # More efficient, still powerful
            "command-light",   # Faster, lighter
        ]
