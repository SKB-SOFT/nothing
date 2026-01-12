import asyncio
import aiohttp
import json
from typing import Dict, Any
import time
from .base_provider import BaseProvider

class GroqProvider(BaseProvider):
    """
    Groq Cloud LLM Provider - Fastest LLM inference
    Free tier: 14,400 requests/day, 6K tokens/min
    No credit card required
    
    Docs: https://console.groq.com/docs/speech-text
    """
    
    def __init__(self, api_key: str, model_name: str = "mixtral-8x7b-32768"):
        super().__init__(api_key, model_name)
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    async def query(self, prompt: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Query Groq API with streaming support.
        """
        start_time = time.time()
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. Provide concise, accurate responses."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        response_text = data["choices"][0]["message"]["content"]
                        token_count = data["usage"]["completion_tokens"] + data["usage"]["prompt_tokens"]
                        
                        return self.format_response(
                            response_text=response_text,
                            response_time_ms=response_time_ms,
                            token_count=token_count
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
                error_message=f"Groq Error: {str(e)[:100]}",
                response_time_ms=response_time_ms
            )
    
    async def validate_key(self) -> bool:
        """
        Validate Groq API key.
        """
        try:
            result = await self.query("Hello, this is a test.", timeout=10)
            return result["status"] == "success"
        except Exception:
            return False
    
    @staticmethod
    def get_available_models() -> list:
        """
        Return list of available Groq models.
        """
        return [
            "mixtral-8x7b-32768",  # Free, fastest
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "gemma-7b-it",
        ]
