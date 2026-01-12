import asyncio
import aiohttp
import json
from typing import Dict, Any, List
import time
from .base_provider import BaseProvider

class GeminiProvider(BaseProvider):
    """
    Google Gemini API Provider - Free tier with web search
    Free tier: 60 requests/min, 15K tokens/day
    No credit card required
    
    Docs: https://ai.google.dev/gemini-api/docs
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        super().__init__(api_key, model_name)
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    
    async def query(self, prompt: str, timeout: int = 30, web_search: bool = True) -> Dict[str, Any]:
        """
        Query Google Gemini API.
        """
        start_time = time.time()
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": "You are a helpful assistant. Provide concise, accurate responses with citations when available."}]
            },
            "generationConfig": {
                "maxOutputTokens": 1024,
                "temperature": 0.7,
                "topP": 0.9,
            },
        }
        
        # Add web search if enabled (requires grounding in Gemini 2.0+)
        if web_search:
            payload["tools"] = [
                {
                    "googleSearch": {}
                }
            ]
        
        params = {"key": self.api_key}
        headers = {"Content-Type": "application/json"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=payload,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract response text
                        response_text = ""
                        sources = []
                        
                        if "candidates" in data and len(data["candidates"]) > 0:
                            candidate = data["candidates"][0]
                            
                            # Get main content
                            if "content" in candidate and "parts" in candidate["content"]:
                                for part in candidate["content"]["parts"]:
                                    if "text" in part:
                                        response_text += part["text"]
                            
                            # Extract grounding metadata (sources)
                            if "groundingMetadata" in candidate:
                                grounding = candidate["groundingMetadata"]
                                if "searchEntryPoint" in grounding:
                                    # Note: web search was used
                                    sources.append({"type": "web_search"})
                                
                                if "groundingChunks" in grounding:
                                    for chunk in grounding["groundingChunks"]:
                                        if "web" in chunk:
                                            sources.append({
                                                "url": chunk["web"].get("uri", ""),
                                                "title": chunk["web"].get("title", ""),
                                            })
                        
                        # Get token count from usage metadata
                        token_count = 0
                        if "usageMetadata" in data:
                            token_count = (data["usageMetadata"].get("promptTokenCount", 0) + 
                                         data["usageMetadata"].get("candidatesTokenCount", 0))
                        
                        if not response_text:
                            response_text = "No response generated"
                        
                        return self.format_response(
                            response_text=response_text,
                            response_time_ms=response_time_ms,
                            token_count=token_count if token_count > 0 else len(response_text.split()),
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
                error_message=f"Gemini Error: {str(e)[:100]}",
                response_time_ms=response_time_ms
            )
    
    async def validate_key(self) -> bool:
        """
        Validate Gemini API key.
        """
        try:
            result = await self.query("Hello", timeout=10)
            return result["status"] == "success"
        except Exception:
            return False
    
    @staticmethod
    def get_available_models() -> List[str]:
        """
        Return list of available Gemini models.
        """
        return [
            "gemini-2.0-flash",  # Latest, fastest
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
