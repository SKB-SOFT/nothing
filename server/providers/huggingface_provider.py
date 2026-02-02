import asyncio
import aiohttp
import json
from typing import Dict, Any, List
import time
from .base_provider import BaseProvider

class HuggingFaceProvider(BaseProvider):
    """
    HuggingFace Inference API Provider
    Free tier: 32K tokens/month from API + unlimited model hosting
    No credit card required
    Access 100K+ open models
    
    Docs: https://huggingface.co/docs/api-inference/getting-started
    """
    
    def __init__(self, api_key: str, model_id: str = "HuggingFaceH4/zephyr-7b-beta"):
        super().__init__(api_key, model_id)
        self.model_id = model_id
        # HuggingFace deprecated api-inference.huggingface.co in favor of router.huggingface.co
        # See error 410 guidance returned by the API.
        self.router_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
        self.legacy_url = f"https://api-inference.huggingface.co/models/{model_id}"
    
    async def query(self, prompt: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Query HuggingFace Inference API.
        """
        start_time = time.time()

        # Different payload format for text-generation vs text2text-generation
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 1024,
                "max_new_tokens": 512,
                "temperature": 0.7,
            }
        }

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async def _attempt(url: str):
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    return response, (time.time() - start_time) * 1000

            async with aiohttp.ClientSession() as session:
                response, response_time_ms = await _attempt(self.router_url)

                # Router sometimes returns 404/410; retry once on legacy endpoint
                if response.status in (404, 410):
                    response, response_time_ms = await _attempt(self.legacy_url)

                if response.status == 200:
                    data = await response.json()
                    response_text = ""
                    # HuggingFace returns a list of generated texts
                    if isinstance(data, list) and data and isinstance(data[0], dict):
                        if "generated_text" in data[0]:
                            response_text = data[0]["generated_text"]
                        elif "summary_text" in data[0]:
                            response_text = data[0]["summary_text"]
                    elif isinstance(data, dict):
                        if "generated_text" in data:
                            response_text = data["generated_text"]
                        elif "summary_text" in data:
                            response_text = data["summary_text"]
                    if not response_text:
                        response_text = str(data)[:500]  # Fallback
                    token_count = len(response_text.split())
                    return self.format_response(
                        response_text=response_text,
                        response_time_ms=response_time_ms,
                        token_count=token_count,
                        sources=[]
                    )
                else:
                    error_text = await response.text()
                    return self.format_error(
                        error_message=f"HTTP {response.status}: {error_text[:200]}",
                        response_time_ms=response_time_ms,
                        error_type="model_not_found" if response.status == 404 else "unknown",
                    )
        
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            return self.format_error(
                error_message="Request timeout (30s) - Model may be loading",
                response_time_ms=response_time_ms
            )
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return self.format_error(
                error_message=f"HuggingFace Error: {str(e)[:100]}",
                response_time_ms=response_time_ms
            )
    
    async def validate_key(self) -> bool:
        """
        Validate HuggingFace API key.
        """
        try:
            result = await self.query("Hello", timeout=15)
            return result["status"] == "success"
        except Exception:
            return False
    
    @staticmethod
    def get_available_models() -> List[str]:
        """
        Return list of popular free HuggingFace models.
        There are 100K+ models available. These are tested ones.
        """
        return [
            # Popular instruction-tuned models
            "HuggingFaceH4/zephyr-7b-beta",      # Fast, good quality
            "mistralai/Mistral-7B-Instruct-v0.2",# Good balance
            "meta-llama/Llama-2-7b-chat-hf",     # Popular, reliable
            "tiiuae/falcon-7b-instruct",         # Fast inference
            "gpt2",                                # Very fast, older
            
            # Text summarization models
            "facebook/bart-large-cnn",           # Good summarization
            "google/pegasus-cnn_dailymail",      # News summarization
            
            # Larger models (may be slow on free tier)
            "meta-llama/Llama-2-13b-chat-hf",    # More capable but slower
            "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",  # Powerful
        ]
